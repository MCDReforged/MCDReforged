from typing import List, Tuple, Optional, Iterable

from wcwidth import wcswidth

from mcdreforged.utils.replier import Replier
from mcdreforged.utils.types.message import MessageText


class Table:
	Row = Tuple[MessageText, ...]

	def __init__(self, header: Optional[Iterable[MessageText]]):
		self.__rows: Optional[List[Table.Row]] = [tuple(header)] if header is not None else None
		self.__has_header = header is not None
		self.__width: Optional[int] = None

	@property
	def width(self) -> int:
		if self.__width is None:
			self.__width = len(self.__rows[0])
		return self.__width

	@property
	def height(self) -> int:
		return len(self.__rows)

	def add_row(self, row: List[MessageText]):
		if len(self.__rows) > 0 and self.width != len(row):
			raise AssertionError('Table width mismatch, expected {}, new row width {}'.format(self.width, len(row)))
		self.__rows.append(tuple(row))
		if len(self.__rows) == 1:
			_ = self.width

	def dump(self) -> List[MessageText]:
		if len(self.__rows) == 0:
			return []
		widths = []
		for j in range(self.width):
			widths.append(max(wcswidth(str(r[j])) for r in self.__rows))

		from mcdreforged.minecraft.rtext.style import RStyle
		from mcdreforged.minecraft.rtext.text import RTextBase
		lines = []
		for i, row in enumerate(self.__rows):
			items = []
			for j, cell in enumerate(row):
				if i == 0 and self.__has_header:
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
