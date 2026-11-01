import functools
import re
from typing import Optional, Tuple

from mcdreforged.minecraft.rtext.text import RTextJsonFormat
from mcdreforged.utils import string_utils


def check_mc_version_ge(version_name: Optional[str], min_release: Tuple[int, ...], min_snapshot: Tuple[int, int]) -> bool:
	if version_name is None:
		return False

	def check_release_version(major: str, minor: str, patch: Optional[str]) -> bool:
		if patch is None:
			patch = '0'
		return (int(major), int(minor), int(patch)) >= min_release

	def check_snapshot_version(year: str, week: str) -> bool:
		return (int(year), int(week)) >= min_snapshot

	version_name = string_utils.remove_suffix(version_name, ' Unobfuscated')  # "1.21.11 Unobfuscated"

	release_regexps = [
		re.compile(r'(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<patch>\d+))?', re.IGNORECASE),  # "1.21", "1.17.1", "26.1"
		re.compile(r'(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<patch>\d+))? Pre-Release \d+', re.IGNORECASE),  # "1.20.5 Pre-Release 4"
		re.compile(r'(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<patch>\d+))? Release Candidate \d+', re.IGNORECASE),  # "1.21 Release Candidate 1"
	]
	for regex in release_regexps:
		if (m := regex.fullmatch(version_name)) is not None:
			return check_release_version(m.group('major'), m.group('minor'), m.group('patch'))

	snapshot_regexps = [
		re.compile(r'(?P<year>\d+)w(?P<week>\d+)[a-z]', re.IGNORECASE),  # "22w45a"
		re.compile(r'(?P<year>\d+)(\.(?P<minor>\d+)(\.(?P<patch>\d+))?)? Snapshot (?P<num>\d+)', re.IGNORECASE),  # "26.1 Snapshot 1"
	]
	for regex in snapshot_regexps:
		if (m := regex.fullmatch(version_name)) is not None:
			groups = m.groupdict()
			snapshot_id = groups.get('week') or groups.get('num')
			assert snapshot_id is not None
			return check_snapshot_version(m.group('year'), snapshot_id)

	# unknown version
	return False


@functools.lru_cache(maxsize=128)
def does_mc_version_has_execute_command(version_name: Optional[str]) -> bool:
	# >= 18w30a, first 1.13.1 snapshot
	return check_mc_version_ge(version_name, (1, 13, 0), (18, 30))


@functools.lru_cache(maxsize=128)
def get_rtext_json_format(version_name: Optional[str]) -> RTextJsonFormat:
	# >= 25w03a, an 1.21.5 snapshot
	if check_mc_version_ge(version_name, (1, 21, 5), (25, 3)):
		return RTextJsonFormat.V_1_21_5
	else:
		return RTextJsonFormat.default()
