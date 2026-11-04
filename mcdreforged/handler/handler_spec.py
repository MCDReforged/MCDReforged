"""
Server handler spec models for declarative handler configuration
"""
import enum
import re
import string
from typing import List, Dict, Annotated, Any, ClassVar, FrozenSet, Mapping, Type

from pydantic import BaseModel, ConfigDict, Field, AfterValidator, Tag, StringConstraints, ValidationInfo, field_validator
from typing_extensions import TypeAliasType

from mcdreforged.utils.pydantic_utils import key_discriminator


# ------------------------------
#             Common
# ------------------------------

class _SpecModel(BaseModel):
	model_config = ConfigDict(frozen=True, extra='forbid')


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
	"""
	The available forms of :data:`TextTransform <mcdreforged.handler.handler_spec.TextTransform>`, which modify a line of text

	.. versionadded:: v2.17.0
	"""

	class Builtin(_SpecModel):
		"""
		.. code-block:: yaml

			builtin: strip_ansi_color

		Available values of ``builtin``:

		* ``strip_ansi_color``: Remove ANSI console color codes, e.g. ``\\033[31m``
		* ``strip_minecraft_color``: Remove Minecraft color codes, e.g. ``§a``
		"""

		class Name(enum.Enum):
			strip_ansi_color = 'strip_ansi_color'
			strip_minecraft_color = 'strip_minecraft_color'

		builtin: Name

	class Sub(_SpecModel):
		"""
		Replace occurrences of a regular expression, like :external:func:`re.sub`

		.. code-block:: yaml

			sub: '^>*\\r'  # the pattern to search for anywhere in the text
			repl: ''       # the replacement
			count: 1       # optional, the maximum number of replacements. Default: 0, replace all
		"""

		sub: re.Pattern[str]
		repl: str
		count: int = Field(default=0, ge=0)

		@field_validator('repl')
		@classmethod
		def _validate_repl(cls, repl: str, info: ValidationInfo) -> str:
			if (pattern := info.data.get('sub')) is not None:
				try:
					pattern.sub(repl, '')
				except (re.error, IndexError) as e:
					raise ValueError(f'invalid replacement: {e}') from e
			return repl


TextTransform = TypeAliasType('TextTransform', Annotated[
	Annotated[TextTransforms.Builtin, Tag('builtin')] | Annotated[TextTransforms.Sub, Tag('sub')],
	key_discriminator({'builtin': 'builtin', 'sub': 'sub'}),
])
"""
A text transform, in one of the forms in :class:`TextTransforms <mcdreforged.handler.handler_spec.TextTransforms>`, determined by the key present

.. versionadded:: v2.17.0
"""


# ------------------------------
#         Stop method
# ------------------------------

class StopMethods:
	"""
	The available forms of :data:`StopMethod <mcdreforged.handler.handler_spec.StopMethod>`, which stop the server

	.. versionadded:: v2.17.0
	"""

	class Command(_SpecModel):
		"""
		Send a command to the standard input of the server

		.. code-block:: yaml

			command: stop
		"""

		command: str

	class Signal(_SpecModel):
		"""
		Send a signal to the server process

		.. code-block:: yaml

			signal: SIGTERM       # a signal name like "SIGINT", or a signal number like 15
			scope: process_tree   # optional, default: process

		Available values of ``scope``:

		* ``process``: Only the server process, i.e. the process started by MCDR
		* ``process_tree``: The server process and all of its child processes

		On Windows, only ``SIGTERM`` is supported, which terminates the process immediately
		"""

		class Scope(enum.Enum):
			process = 'process'
			process_tree = 'process_tree'

		signal: Annotated[str, StringConstraints(pattern=r'^SIG[A-Z0-9]+$')] | Annotated[int, Field(ge=1)]
		scope: Scope = Scope.process


StopMethod = TypeAliasType('StopMethod', Annotated[
	Annotated[StopMethods.Command, Tag('command')] | Annotated[StopMethods.Signal, Tag('signal')],
	key_discriminator({'command': 'command', 'signal': 'signal'}),
])
"""
A stop method, in one of the forms in :class:`StopMethods <mcdreforged.handler.handler_spec.StopMethods>`, determined by the key present

.. versionadded:: v2.17.0
"""


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
	"""
	The available forms of :data:`SendMessageMethod <mcdreforged.handler.handler_spec.SendMessageMethod>`, which send a message to a target

	.. versionadded:: v2.17.0
	"""

	class Builtin(_MessageBuiltin):
		"""
		.. code-block:: yaml

			builtin: minecraft_tellraw

		Available values of ``builtin``:

		* ``minecraft_tellraw``: The ``tellraw`` command of Minecraft
		"""

	class Template(_MessageTemplate):
		"""
		A command built from a template

		.. code-block:: yaml

			template: 'tell {target} {message}'
			message_format: plain

		``template`` uses the :external:meth:`str.format` syntax. Available placeholders:

		* ``{target}``: The target of the message
		* ``{message}``: The message, formatted according to ``message_format``

		Use ``{{`` and ``}}`` for literal braces. Placeholders with conversions or format specs, e.g. ``{message!r}``, are not allowed

		Available values of ``message_format``:

		* ``json``: A JSON text component
		* ``plain``: Plain text, with Minecraft color codes like ``§a`` removed
		"""

		ALLOWED_PLACEHOLDERS = frozenset({'target', 'message'})


SendMessageMethod = TypeAliasType('SendMessageMethod', Annotated[
	Annotated[SendMessageMethods.Builtin, Tag('builtin')] | Annotated[SendMessageMethods.Template, Tag('template')],
	key_discriminator({'template': 'template', 'builtin': 'builtin'}),
])
"""
A send message method, in one of the forms in :class:`SendMessageMethods <mcdreforged.handler.handler_spec.SendMessageMethods>`, determined by the key present

.. versionadded:: v2.17.0
"""


class BroadcastMessageMethods:
	"""
	The available forms of :data:`BroadcastMessageMethod <mcdreforged.handler.handler_spec.BroadcastMessageMethod>`, which broadcast a message

	.. versionadded:: v2.17.0
	"""

	class Builtin(_MessageBuiltin):
		"""
		.. code-block:: yaml

			builtin: minecraft_tellraw
			target: '@a'

		Same as :class:`SendMessageMethods.Builtin <mcdreforged.handler.handler_spec.SendMessageMethods.Builtin>`, with a fixed ``target``
		"""

		target: Annotated[str, Field(min_length=1)]

	class Template(_MessageTemplate):
		"""
		A command built from a template

		.. code-block:: yaml

			template: 'say {message}'
			message_format: plain

		Same as :class:`SendMessageMethods.Template <mcdreforged.handler.handler_spec.SendMessageMethods.Template>`, except that only the ``{message}`` placeholder is available
		"""

		ALLOWED_PLACEHOLDERS = frozenset({'message'})


BroadcastMessageMethod = TypeAliasType('BroadcastMessageMethod', Annotated[
	Annotated[BroadcastMessageMethods.Builtin, Tag('builtin')] | Annotated[BroadcastMessageMethods.Template, Tag('template')],
	key_discriminator({'template': 'template', 'builtin': 'builtin'}),
])
"""
A broadcast message method, in one of the forms in :class:`BroadcastMessageMethods <mcdreforged.handler.handler_spec.BroadcastMessageMethods>`, determined by the key present

.. versionadded:: v2.17.0
"""


# ------------------------------
#        Handler spec
# ------------------------------

class HandlerSpec(_SpecModel):
	"""
	The declarative definition of a server handler, as an immutable `pydantic <https://docs.pydantic.dev/>`__ model

	.. list-table::
		:header-rows: 1

		* - Field
		  - Type
		  - Description
		* - ``name``
		  - :class:`str`
		  - Required. The name of the handler
		* - ``control``
		  - :class:`HandlerSpec.Control <mcdreforged.handler.handler_spec.HandlerSpec.Control>`
		  - Required
		* - ``parsing``
		  - :class:`HandlerSpec.Parsing <mcdreforged.handler.handler_spec.HandlerSpec.Parsing>`
		  - Required
		* - ``events``
		  - :class:`HandlerSpec.Events <mcdreforged.handler.handler_spec.HandlerSpec.Events>`
		  - Optional. Default: no event is recognized

	All regular expressions use the Python :external:mod:`re` syntax. Except the ``sub`` of :class:`TextTransforms.Sub <mcdreforged.handler.handler_spec.TextTransforms.Sub>`:

	* A regular expression needs to match the whole text
	* For a list of regular expressions, they are tried in order, and the first matched one is used
	* Named groups listed as required must be present. Other groups are ignored

	.. versionadded:: v2.17.0
	"""

	class Control(_SpecModel):
		"""
		Rules for controlling the server

		.. list-table::
			:header-rows: 1

			* - Field
			  - Type
			  - Description
			* - ``stop``
			  - :data:`StopMethod <mcdreforged.handler.handler_spec.StopMethod>`
			  - Required. How to stop the server
			* - ``send_message``
			  - :data:`SendMessageMethod <mcdreforged.handler.handler_spec.SendMessageMethod>` or ``null``
			  - Optional. How to send a message to a player. Default: ``null``, not supported
			* - ``broadcast_message``
			  - :data:`BroadcastMessageMethod <mcdreforged.handler.handler_spec.BroadcastMessageMethod>` or ``null``
			  - Optional. How to broadcast a message to all players. Default: ``null``, not supported
		"""

		stop: StopMethod
		send_message: SendMessageMethod | None = None
		broadcast_message: BroadcastMessageMethod | None = None

	class Parsing(_SpecModel):
		"""
		Rules for parsing the server output

		Each line of the server output is processed in the following steps:

		1.  Apply the ``pre_parse`` text transforms. The result is the :attr:`~mcdreforged.info_reactor.info.Info.raw_content` of the info
		2.  Apply the ``line_transforms`` text transforms to the raw content
		3.  Match the result against the ``line`` rules.
		    If none of the rules matches, the line is unrecognized, its :attr:`~mcdreforged.info_reactor.info.Info.content` is the raw content
		4.  Match the content against the ``player_message`` rules.
		    If matched, the line is a message from a player

		.. list-table::
			:header-rows: 1

			* - Field
			  - Type
			  - Description
			* - ``pre_parse``
			  - List of :data:`TextTransform <mcdreforged.handler.handler_spec.TextTransform>`
			  - Optional. Default: ``[]``
			* - ``line_transforms``
			  - List of :data:`TextTransform <mcdreforged.handler.handler_spec.TextTransform>`
			  - Optional. Default: ``[]``
			* - ``line``
			  - List of regular expressions
			  - Required, at least one. The formats of a line.
			    Named group ``content`` is required, as the :attr:`~mcdreforged.info_reactor.info.Info.content` of the info.
			    Named groups ``hour``, ``min``, ``sec`` and ``logging`` are optional,
			    as the :attr:`~mcdreforged.info_reactor.info.Info.hour`, :attr:`~mcdreforged.info_reactor.info.Info.min`,
			    :attr:`~mcdreforged.info_reactor.info.Info.sec` and :attr:`~mcdreforged.info_reactor.info.Info.logging_level` of the info
			* - ``player_message``
			  - List of regular expressions
			  - Optional. The formats of a player message.
			    Named groups ``name`` and ``message`` are required,
			    as the :attr:`~mcdreforged.info_reactor.info.Info.player` and the :attr:`~mcdreforged.info_reactor.info.Info.content` of the info.
			    A rule is skipped if the player name is invalid.
			    Default: ``[]``, player messages are not recognized
			* - ``player_name``
			  - Regular expression
			  - Required. The format of a valid player name
		"""

		pre_parse: List[TextTransform] = Field(default_factory=list)
		line_transforms: List[TextTransform] = Field(default_factory=list)
		line: Annotated[List[Annotated[re.Pattern[str], _require_groups('content')]], Field(min_length=1)]
		player_message: List[Annotated[re.Pattern[str], _require_groups('name', 'message')]] = Field(default_factory=list)
		player_name: re.Pattern[str]

	class Events(_SpecModel):
		"""
		Rules for recognizing server events

		Each field is an optional list of regular expressions, matched against the :attr:`~mcdreforged.info_reactor.info.Info.content` of the info.
		Default: ``[]``, the event is not recognized

		Events are only recognized from server output that is not a player message.
		For rules with the ``name`` named group, a rule is skipped if the player name is invalid

		.. list-table::
			:header-rows: 1

			* - Field
			  - Required named groups
			* - ``player_joined``
			  - ``name``
			* - ``player_left``
			  - ``name``
			* - ``server_version``
			  - ``version``
			* - ``server_address``
			  - ``ip``, ``port``
			* - ``server_startup_done``
			  -
			* - ``rcon_started``
			  -
			* - ``server_stopping``
			  -
		"""

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
		Create a new spec by merging the given override onto this spec

		Merging rules:

		* ``control``, ``parsing`` and ``events`` are merged key by key. Keys not present in the override are inherited from this spec
		* Other values are replaced as a whole, including lists, stop methods, message methods and text transforms
		* ``name`` is not inherited

		:param override: The override, in the same structure as a handler spec
		:return: The merged handler spec
		:raise pydantic.ValidationError: If the merged handler spec is invalid
		"""
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
