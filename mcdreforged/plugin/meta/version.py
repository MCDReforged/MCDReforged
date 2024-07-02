"""
Plugin Version
"""
import dataclasses
import re
from typing import List, Callable, Tuple, Optional, Union, Any


# beta.3 -> (beta, 3), random -> (random, None)
class _ExtraElement:
	DIVIDER = '.'
	body: str
	num: Optional[int]

	def __init__(self, segment_str: str):
		segments = segment_str.rsplit(self.DIVIDER, 1)
		try:
			self.body, self.num = segments[0], int(segments[1])
		except (IndexError, ValueError):
			self.body, self.num = segment_str, None

	def __str__(self):
		if self.num is None:
			return self.body
		return '{}{}{}'.format(self.body, self.DIVIDER, self.num)

	def __lt__(self, other):
		if not isinstance(other, _ExtraElement):
			raise TypeError()
		if self.num is None or other.num is None:
			return str(self) < str(other)
		else:
			return (self.body, self.num) < (other.body, other.num)

	def __hash__(self):
		return hash((self.body, self.num))


class Version:
	"""
	A version container that stores semver like version string

	Example:

	* ``"1.2.3"``
	* ``"1.0.*"``
	* ``"1.2.3-pre4+build.5"``
	"""
	EXTRA_ID_PATTERN = re.compile(r'|[-+0-9A-Za-z]+(\.[-+0-9A-Za-z]+)*')
	WILDCARDS = ('*', 'x', 'X')
	WILDCARD = -1

	component: Tuple[int, ...]
	has_wildcard: bool
	pre: Optional[_ExtraElement]
	build: Optional[_ExtraElement]

	def __init__(self, version_str: str, *, allow_wildcard: bool = True):
		"""
		:param version_str: The version string to be parsed
		:keyword allow_wildcard: If wildcard (``"*"``, ``"x"``, ``"X"``) is allowed. Default: ``True``
		"""
		if not isinstance(version_str, str):
			raise VersionParsingError('Invalid input version string')

		def separate_extra(text, char) -> Tuple[str, Optional[_ExtraElement]]:
			if char in text:
				text, extra_str = text.split(char, 1)
				if not self.EXTRA_ID_PATTERN.fullmatch(extra_str):
					raise VersionParsingError('Invalid build string: ' + extra_str)
				extra = _ExtraElement(extra_str)
			else:
				extra = None
			return text, extra

		components = []
		self.has_wildcard = False
		version_str, self.build = separate_extra(version_str, '+')
		version_str, self.pre = separate_extra(version_str, '-')
		if len(version_str) == 0:
			raise VersionParsingError('Version string is empty')
		for comp in version_str.split('.'):
			if comp in self.WILDCARDS:
				components.append(self.WILDCARD)
				self.has_wildcard = True
				if not allow_wildcard:
					raise VersionParsingError('Wildcard {} is not allowed'.format(comp))
			else:
				try:
					num = int(comp)
				except ValueError:
					num = None
				if num is None:
					raise VersionParsingError('Invalid version number component: {}'.format(comp))
				if num < 0:
					raise VersionParsingError('Unsupported negatived number component: {}'.format(num))
				components.append(num)
		if len(components) == 0:
			raise VersionParsingError('Empty version string')
		self.component = tuple(components)

	def __str__(self):
		version_str = '.'.join(
			str(c)
			if c != self.WILDCARD
			else self.WILDCARDS[0]
			for c in self.component
		)
		if self.pre is not None:
			version_str += '-' + str(self.pre)
		if self.build is not None:
			version_str += '+' + str(self.build)
		return version_str

	def __getitem__(self, index: int) -> int:
		if index < len(self.component):
			return self.component[index]
		else:
			return self.WILDCARD if self.component[len(self.component) - 1] == self.WILDCARD else 0

	def __lt__(self, other: 'Version') -> bool:
		if not isinstance(other, Version):
			raise TypeError('Cannot compare between instances of {} and {}'.format(Version.__name__, type(other).__name__))
		for i in range(max(len(self.component), len(other.component))):
			if self[i] == self.WILDCARD or other[i] == self.WILDCARD:
				continue
			if self[i] != other[i]:
				return self[i] < other[i]
		if self.pre is not None and other.pre is not None:
			return self.pre < other.pre
		elif self.pre is not None:
			return not other.has_wildcard
		elif other.pre is not None:
			return False
		else:
			return False

	def __eq__(self, other: Any) -> bool:
		return isinstance(other, Version) and not self < other and not other < self

	def __le__(self, other: 'Version'):
		return self == other or self < other

	def compare_to(self, other):
		if self < other:
			return -1
		elif self > other:
			return 1
		else:
			return 0

	def __hash__(self):
		return hash((self.component, self.pre, self.build))

	def __repr__(self):
		return '{}({!r})'.format(self.__class__.__name__, str(self))


DEFAULT_CRITERION_OPERATOR = '=='


@dataclasses.dataclass(frozen=True)
class Criterion:
	opt: str
	base_version: Version
	criterion: Callable[[Version, Version], bool]
	is_default: bool

	def test(self, target: Union[Version, str]):
		return self.criterion(self.base_version, target)

	def __str__(self):
		if self.is_default:
			return str(self.base_version)
		else:
			return '{}{}'.format(self.opt, self.base_version)


class VersionRequirement:
	"""
	A version requirement tester

	It can test if a given :class:`Version` object matches its requirement
	"""
	CRITERIONS = {
		'<=': lambda base, ver: ver <= base,
		'>=': lambda base, ver: ver >= base,
		'<': lambda base, ver: ver < base,
		'>': lambda base, ver: ver > base,
		'==': lambda base, ver: ver == base,
		'=': lambda base, ver: ver == base,
		'^': lambda base, ver: ver >= base and ver[0] == base[0],
		'~': lambda base, ver: ver >= base and ver[0] == base[0] and ver[1] == base[1],
	}

	def __init__(self, requirements: str):
		"""
		:param requirements: The requirement string, which contains several version predicates connected by space character.
			e.g. ``">=1.0.x"``, ``"^2.9"``, ``">=1.2.0 <1.4.3"``, `""`
		"""
		if not isinstance(requirements, str):
			raise VersionParsingError('Requirements should be a str, not {}'.format(type(requirements).__name__))
		self.criterions: List[Criterion] = []
		for requirement in requirements.split(' '):
			if len(requirement) > 0:
				for prefix, func in self.CRITERIONS.items():
					if requirement.startswith(prefix):
						opt = prefix
						base_version = requirement[len(prefix):]
						is_default = False
						break
				else:
					opt = DEFAULT_CRITERION_OPERATOR
					base_version = requirement
					is_default = True
				self.criterions.append(Criterion(opt, Version(base_version), self.CRITERIONS[opt], is_default))

	def has_criterion(self) -> bool:
		return len(self.criterions) > 0

	def accept(self, version: Union[Version, str]) -> bool:
		if isinstance(version, str):
			version = Version(version)
		return all(criterion.test(version) for criterion in self.criterions)

	def __str__(self):
		return ' '.join(map(str, self.criterions))

	def __repr__(self):
		return '{}({!r})'.format(self.__class__.__name__, str(self))

	def __hash__(self):
		return hash(str(self))

	def __eq__(self, other):
		if not isinstance(other, VersionRequirement):
			return False
		return self.criterions == other.criterions


class VersionParsingError(ValueError):
	pass
