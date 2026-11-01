"""
Server handler spec models for declarative handler configuration
"""
import enum
import re
import string
from typing import List, Dict, Annotated, Any, ClassVar, FrozenSet, Mapping, Type

from pydantic import BaseModel, ConfigDict, Field, AfterValidator, Discriminator, Tag, StringConstraints, field_validator


# ------------------------------
#             Common
# ------------------------------

class _SpecModel(BaseModel):
	model_config = ConfigDict(frozen=True)


def _key_discriminator(key_to_tag: Dict[str, str], default: str) -> Discriminator:
	def func(value: Any) -> str:
		for key, tag in key_to_tag.items():
			if (isinstance(value, dict) and key in value) or (not isinstance(value, dict) and hasattr(value, key)):
				return tag
		return default
	return Discriminator(func)


def _require_groups(*groups: str) -> AfterValidator:
	required = frozenset(groups)

	def validate(pattern: re.Pattern[str]) -> re.Pattern[str]:
		if len(missing := required - pattern.groupindex.keys()) > 0:
			raise ValueError('missing named group(s): {}'.format(', '.join(map(repr, sorted(missing)))))
		return pattern

	return AfterValidator(validate)


# ------------------------------
#         Text transform
# ------------------------------

class TextTransforms:
	class Builtin(_SpecModel):
		class Name(enum.Enum):
			strip_ansi_color = 'strip_ansi_color'
			strip_minecraft_color = 'strip_minecraft_color'

		builtin: Name

	class Sub(_SpecModel):
		sub: re.Pattern[str]
		repl: str
		count: int = Field(default=0, ge=0)


TextTransform = Annotated[
	Annotated[TextTransforms.Builtin, Tag('builtin')] | Annotated[TextTransforms.Sub, Tag('sub')],
	_key_discriminator({'builtin': 'builtin'}, 'sub'),
]


# ------------------------------
#         Stop method
# ------------------------------

class StopMethods:
	class Command(_SpecModel):
		model_config = ConfigDict(frozen=True, extra='forbid')
		command: str

	class Signal(_SpecModel):
		class Scope(enum.Enum):
			process = 'process'
			process_tree = 'process_tree'

		model_config = ConfigDict(frozen=True, extra='forbid')
		signal: Annotated[str, StringConstraints(pattern=r'^(SIG[A-Z0-9]+|CTRL_[A-Z]+_EVENT)$')] | Annotated[int, Field(ge=0)]
		scope: Scope = Scope.process


StopMethod = Annotated[
	Annotated[StopMethods.Command, Tag('command')] | Annotated[StopMethods.Signal, Tag('signal')],
	_key_discriminator({'command': 'command'}, 'signal'),
]


# ------------------------------
#         Message method
# ------------------------------

class _MessageBuiltin(_SpecModel):
	class Name(enum.Enum):
		minecraft_tellraw = 'minecraft_tellraw'

	builtin: Name


class _MessageTemplate(_SpecModel):
	class Format(enum.Enum):
		json = 'json'
		plain = 'plain'

	ALLOWED_PLACEHOLDERS: ClassVar[FrozenSet[str]] = frozenset()

	template: str
	message_format: Format

	@field_validator('template')
	@classmethod
	def _validate_template(cls, template: str) -> str:
		try:
			parsed = list(string.Formatter().parse(template))
		except ValueError as e:
			raise ValueError(f'invalid template: {e}') from e
		for _, field_name, format_spec, conversion in parsed:
			if field_name is None:
				continue
			if field_name not in cls.ALLOWED_PLACEHOLDERS:
				allowed = ', '.join(f'{{{p}}}' for p in sorted(cls.ALLOWED_PLACEHOLDERS))
				raise ValueError(f'unknown placeholder {{{field_name}}}, allowed: {allowed}')
			if conversion is not None or format_spec:
				raise ValueError(f'conversion or format spec is not allowed in placeholder {{{field_name}}}')
		return template


class SendMessageMethods:
	class Builtin(_MessageBuiltin):
		pass

	class Template(_MessageTemplate):
		ALLOWED_PLACEHOLDERS = frozenset({'target', 'message'})


SendMessageMethod = Annotated[
	Annotated[SendMessageMethods.Builtin, Tag('builtin')] | Annotated[SendMessageMethods.Template, Tag('template')],
	_key_discriminator({'template': 'template'}, 'builtin'),
]


class BroadcastMessageMethods:
	class Builtin(_MessageBuiltin):
		target: Annotated[str, Field(min_length=1)]

	class Template(_MessageTemplate):
		ALLOWED_PLACEHOLDERS = frozenset({'message'})


BroadcastMessageMethod = Annotated[
	Annotated[BroadcastMessageMethods.Builtin, Tag('builtin')] | Annotated[BroadcastMessageMethods.Template, Tag('template')],
	_key_discriminator({'template': 'template'}, 'builtin'),
]


# ------------------------------
#        Handler spec
# ------------------------------

class HandlerSpec(_SpecModel):
	class Control(_SpecModel):
		stop: StopMethod
		send_message: SendMessageMethod | None = None
		broadcast_message: BroadcastMessageMethod | None = None

	class Parsing(_SpecModel):
		pre_parse: List[TextTransform] = Field(default_factory=list)
		line_transforms: List[TextTransform] = Field(default_factory=list)
		line: Annotated[List[Annotated[re.Pattern[str], _require_groups('content')]], Field(min_length=1)]
		player_message: List[Annotated[re.Pattern[str], _require_groups('name', 'message')]] = Field(default_factory=list)
		player_name: re.Pattern[str]

	class Events(_SpecModel):
		player_joined: List[Annotated[re.Pattern[str], _require_groups('name')]] = Field(default_factory=list)
		player_left: List[Annotated[re.Pattern[str], _require_groups('name')]] = Field(default_factory=list)
		server_version: List[Annotated[re.Pattern[str], _require_groups('version')]] = Field(default_factory=list)
		server_address: List[Annotated[re.Pattern[str], _require_groups('ip', 'port')]] = Field(default_factory=list)
		server_startup_done: List[re.Pattern[str]] = Field(default_factory=list)
		rcon_started: List[re.Pattern[str]] = Field(default_factory=list)
		server_stopping: List[re.Pattern[str]] = Field(default_factory=list)

	name: Annotated[str, Field(min_length=1)]
	control: Control
	parsing: Parsing
	events: Events = Field(default_factory=Events)

	def extend(self, override: Mapping[str, Any]) -> 'HandlerSpec':
		"""
		Merge override onto this spec and validate the result as a complete HandlerSpec.
		The "extends" key is ignored; "name" is not inherited from this spec
		"""
		override = {k: v for k, v in override.items() if k != 'extends'}
		merged_dict = self._merge(type(self), self.model_dump(exclude={'name'}), override)
		return HandlerSpec.model_validate(merged_dict)

	@classmethod
	def _merge(cls, model_type: Type[_SpecModel], base: Dict[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
		result = dict(base)
		for key, value in override.items():
			field = model_type.model_fields.get(key)
			sub_type = field.annotation if field is not None else None
			if isinstance(sub_type, type) and issubclass(sub_type, _SpecModel) and isinstance(value, Mapping) and isinstance(result.get(key), dict):
				result[key] = cls._merge(sub_type, result[key], value)
			else:
				result[key] = value
		return result
