import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	pass


class PluginRequirementSource(enum.Enum):
	user_input = enum.auto()
	existing = enum.auto()
	existing_pinned = enum.auto()

