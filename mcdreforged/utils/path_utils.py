from pathlib import Path

from mcdreforged.utils.types.path_like import PathStr


def is_relative_to(child: Path, parent: PathStr) -> bool:
	return child.is_relative_to(parent)
