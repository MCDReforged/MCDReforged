from typing import List, Callable, Any

__all__ = [
	'LineWriter',
	'Node',
	'print_tree',
]


LineWriter = Callable[[str], Any]


class Node:
	def __init__(self, name: str):
		self.name: str = name
		self.children: List['Node'] = []

	def add_child(self, child: 'Node'):
		self.children.append(child)


def print_tree(root: Node, line_writer: LineWriter):
	def is_root(node: Node) -> bool:
		return node == root

	def get_item_line(node: Node, is_last: bool) -> str:
		if is_root(node):
			return ''
		return '└── ' if is_last else '├── '

	def get_parent_line(node: Node, is_last: bool) -> str:
		if is_root(node):
			return ''
		return '    ' if is_last else '│   '

	def do_print(node: Node, prefix: str, is_last: bool):
		line = node.name
		line = get_item_line(node, is_last) + line
		line_writer(prefix + line)

		children = node.children
		for i, child in enumerate(children):
			do_print(child, prefix + get_parent_line(node, is_last), i == len(children) - 1)

	do_print(root, '', False)

