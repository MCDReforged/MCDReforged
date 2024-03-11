from typing import List, Tuple

from wcwidth import wcswidth

from mcdreforged.minecraft.rtext.style import RStyle
from mcdreforged.minecraft.rtext.text import RTextBase
from mcdreforged.plugin.installer.replier import Replier
from mcdreforged.utils.types import MessageText


class Table:
	Row = Tuple[MessageText]

	def __init__(self, header: List[MessageText]):
		self.__rows: List[Tuple[MessageText]] = [tuple(header)]

	@property
	def __header(self) -> Row:
		return self.__rows[0]

	@property
	def width(self) -> int:
		return len(self.__header)

	@property
	def height(self) -> int:
		return len(self.__rows)

	def add_row(self, row: List[MessageText]):
		assert self.width == len(row), 'Table width mismatch, expected {}, new row width {}'.format(self.width, len(row))
		self.__rows.append(tuple(row))

	def dump(self) -> List[MessageText]:
		widths = []
		for j in range(len(self.__header)):
			widths.append(max(map(lambda r: wcswidth(str(r[j])), self.__rows)))
		lines = []
		for i, row in enumerate(self.__rows):
			items = []
			for j, cell in enumerate(row):
				if i == 0:
					cell = RTextBase.from_any(cell).set_styles(RStyle.bold)
				width = wcswidth(str(cell))
				if j != len(row) - 1 and width < widths[j]:
					cell += ' ' * (widths[j] - width)
				items.append(cell)
			lines.append(RTextBase.join('   ', items))
		return lines

	def dump_to(self, replier: Replier):
		for line in self.dump():
			replier.reply(line)
