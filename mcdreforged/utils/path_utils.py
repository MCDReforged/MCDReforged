from pathlib import Path

from mcdreforged.utils.types.path_like import PathStr


def is_relative_to(child: Path, parent: PathStr) -> bool:
	if hasattr(child, 'is_relative_to'):  # python3.9+
		return child.is_relative_to(parent)
	else:
		try:
			child.relative_to(parent)
		except ValueError:
			return False
		else:
			return True
