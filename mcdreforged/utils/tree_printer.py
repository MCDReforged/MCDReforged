from typing import Callable, Any, TypeVar, Iterable, Sized, Generic

__all__ = [
	'LineWriter',
	'TreePrinter',
	'print_tree',
]


T = TypeVar('T')
Self = TypeVar('Self', bound='TreePrinter')
LineWriter = Callable[[str], Any]
_ChildrenGetter = Callable[[T], Iterable[T]]
_NameGetter = Callable[[T], str]


class TreePrinter(Generic[T]):
	def __init__(self):
		self.__line_writer: LineWriter = print
		self.__children_getter = None
		self.__name_getter = None
		self.__use_tab = False
		self.__use_ascii = False

	def getters(self: Self, children_getter: _ChildrenGetter, name_getter: _NameGetter) -> Self:
		self.__children_getter = children_getter
		self.__name_getter = name_getter
		return self

	def writer(self: Self, line_writer: LineWriter) -> Self:
		self.__line_writer = line_writer
		return self

	def tab(self: Self) -> Self:
		self.__use_tab = True
		return self

	def ascii(self: Self) -> Self:
		self.__use_ascii = True
		return self

	def print(self: Self, root: T) -> Self:
		def is_root(node: T) -> bool:
			return node == root

		def get_item_line(node: T, is_last: bool) -> str:
			if is_root(node):
				return ''
			if self.__use_ascii:
				return '`-- ' if is_last else '+-- '
			else:
				return '└── ' if is_last else '├── '

		def get_parent_line(node: T, is_last: bool) -> str:
			if is_root(node):
				return ''
			if is_last:
				base = '' if self.__use_tab else ' '
			else:
				base = '|' if self.__use_ascii else '│'
			padding = '\t' if self.__use_tab else '   '
			return base + padding

		def do_print(node: T, prefix: str, is_last: bool):
			line = self.__name_getter(node)
			line = get_item_line(node, is_last) + line
			self.__line_writer(prefix + line)

			children = self.__children_getter(node)
			if not isinstance(children, Sized):
				children = tuple(children)
			for i, child in enumerate(children):
				do_print(child, prefix + get_parent_line(node, is_last), i == len(children) - 1)

		assert self.__children_getter is not None, 'children_getter not assigned'
		assert self.__name_getter is not None, 'name_getter not assigned'
		do_print(root, '', False)
		return self


def print_tree(root: T, children_getter: _ChildrenGetter, name_getter: _NameGetter, line_writer: LineWriter):
	TreePrinter().writer(line_writer).getters(children_getter, name_getter).print(root)
