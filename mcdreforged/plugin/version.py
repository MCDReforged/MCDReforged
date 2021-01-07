"""
Plugin Version
"""
import re
from typing import List, Callable


class Version:
	EXTRA_ID_PATTERN = re.compile(r'|[-0-9A-Za-z]+(\.[-0-9A-Za-z]+)*')
	WILDCARDS = {'x', 'X', '*'}
	WILDCARD = -1

	def __init__(self, version_str: str, allow_wildcard=True):
		"""
		:param str version_str: the version str like '1.2.3-pre4+build.5'
		"""
		if not isinstance(version_str, str):
			raise VersionParsingError('Invalid input version string')

		def separate_extra(text, char):
			if char in text:
				text, extra = text.split(char, 1)
				if not self.EXTRA_ID_PATTERN.fullmatch(extra):
					raise VersionParsingError('Invalid build string: ' + extra)
			else:
				extra = None
			return text, extra

		self.component = []
		self.has_wildcard = False
		version_str, self.build = separate_extra(version_str, '+')
		version_str, self.pre = separate_extra(version_str, '-')
		if len(version_str) == 0:
			raise VersionParsingError('Version string is empty')
		for comp in version_str.split('.'):
			if comp in self.WILDCARDS:
				self.component.append(self.WILDCARD)
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
				self.component.append(num)
		if len(self.component) == 0:
			raise VersionParsingError('Empty version string')

	def __str__(self):
		version_str = '.'.join(map(str, self.component))
		if self.pre is not None:
			version_str += '-' + self.pre
		if self.build is not None:
			version_str += '+' + self.build
		return version_str

	def __getitem__(self, index):
		if index < len(self.component):
			return self.component[index]
		else:
			return self.WILDCARD if self.component[len(self.component) - 1] == self.WILDCARD else 0

	def __lt__(self, other):
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

	def __eq__(self, other):
		return not self < other and not other < self

	def __le__(self, other):
		return self == other or self < other

	def compare_to(self, other):
		if self < other:
			return -1
		elif self > other:
			return 1
		else:
			return 0


class Criterion:
	def __init__(self, opt: str, base_version: Version, criterion: Callable[[Version, Version], bool]):
		self.opt = opt
		self.base_version = base_version
		self.criterion = criterion

	def test(self, target: str or Version):
		return self.criterion(self.base_version, target)

	def __str__(self):
		return '{}{}'.format(self.opt, self.base_version)


class VersionRequirement:
	CRITERIONS = {
		'<=': lambda base, ver: ver <= base,
		'>=': lambda base, ver: ver >= base,
		'<': lambda base, ver: ver < base,
		'>': lambda base, ver: ver > base,
		'=': lambda base, ver: ver == base,
		'^': lambda base, ver: ver >= base and ver[0] == base[0],
		'~': lambda base, ver: ver >= base and ver[0] == base[0] and ver[1] == base[1],
	}

	def __init__(self, requirements: str):
		if not isinstance(requirements, str):
			raise VersionParsingError('Requirements should be a str, not {}'.format(type(requirements).__name__))
		self.criterions = []  # type: List[Criterion]
		for requirement in requirements.split(' '):
			if len(requirement) > 0:
				for prefix, func in self.CRITERIONS.items():
					if requirement.startswith(prefix):
						opt = prefix
						base_version = requirement[len(prefix):]
						break
				else:
					opt = '='
					base_version = requirement
				self.criterions.append(Criterion(opt, Version(base_version), self.CRITERIONS[opt]))

	def accept(self, version: Version or str):
		if isinstance(version, str):
			version = Version(version)
		for criterion in self.criterions:
			if not criterion.test(version):
				return False
		return True

	def __str__(self):
		return ' '.join(map(str, self.criterions))


class VersionParsingError(ValueError):
	pass


