from typing import Callable, Any, TypeVar, Iterable, Sized

__all__ = [
	'LineWriter',
	'print_tree',
]


LineWriter = Callable[[str], Any]


T = TypeVar('T')


def print_tree(root: T, children_getter: Callable[[T], Iterable[T]], name_getter: Callable[[T], str], line_writer: LineWriter):
	def is_root(node: T) -> bool:
		return node == root

	def get_item_line(node: T, is_last: bool) -> str:
		if is_root(node):
			return ''
		return '└── ' if is_last else '├── '

	def get_parent_line(node: T, is_last: bool) -> str:
		if is_root(node):
			return ''
		return '    ' if is_last else '│   '

	def do_print(node: T, prefix: str, is_last: bool):
		line = name_getter(node)
		line = get_item_line(node, is_last) + line
		line_writer(prefix + line)

		children = children_getter(node)
		if not isinstance(children, Sized):
			children = tuple(children)
		for i, child in enumerate(children):
			do_print(child, prefix + get_parent_line(node, is_last), i == len(children) - 1)

	do_print(root, '', False)

