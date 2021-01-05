"""
Advanced text container for Minecraft
Credit: Pandaria98 https://github.com/Pandaria98 https://github.com/TISUnion/stext
"""

import copy
import json
from typing import Iterable, List

from colorama import Fore, Style


class RColor:
	black = "black"
	dark_blue = "dark_blue"
	dark_green = "dark_green"
	dark_aqua = "dark_aqua"
	dark_red = "dark_red"
	dark_purple = "dark_purple"
	gold = "gold"
	gray = "gray"
	dark_gray = "dark_gray"
	blue = "blue"
	green = "green"
	aqua = "aqua"
	red = "red"
	light_purple = "light_purple"
	yellow = "yellow"
	white = "white"
	reset = 'reset'


_RCOLOR_TO_CONSOLE = {
	RColor.black: Fore.BLACK,
	RColor.dark_blue: Fore.BLUE,
	RColor.dark_green: Fore.GREEN,
	RColor.dark_aqua: Fore.CYAN,
	RColor.dark_red: Fore.RED,
	RColor.dark_purple: Fore.MAGENTA,
	RColor.gold: Fore.YELLOW,
	RColor.gray: Style.RESET_ALL,
	RColor.dark_gray: Style.RESET_ALL,
	RColor.blue: Fore.LIGHTBLUE_EX,
	RColor.green: Fore.LIGHTGREEN_EX,
	RColor.aqua: Fore.LIGHTCYAN_EX,
	RColor.red: Fore.LIGHTRED_EX,
	RColor.light_purple: Fore.LIGHTMAGENTA_EX,
	RColor.yellow: Fore.LIGHTYELLOW_EX,
	RColor.white: Style.RESET_ALL,
	RColor.reset: Style.RESET_ALL,
}

_MC_COLOR_TO_RCOLOR = {
	'§0': RColor.black,
	'§1': RColor.dark_blue,
	'§2': RColor.dark_green,
	'§3': RColor.dark_aqua,
	'§4': RColor.dark_red,
	'§5': RColor.dark_purple,
	'§6': RColor.gold,
	'§7': RColor.gray,
	'§8': RColor.dark_gray,
	'§9': RColor.blue,
	'§a': RColor.green,
	'§b': RColor.aqua,
	'§c': RColor.red,
	'§d': RColor.light_purple,
	'§e': RColor.yellow,
	'§f': RColor.white,
	'§r': RColor.reset,
}


class RColorConvertor:
	__MC_COLOR_TO_CONSOLE_LIST = [(mc_color, _RCOLOR_TO_CONSOLE[rcolor]) for mc_color, rcolor in _MC_COLOR_TO_RCOLOR.items()]
	__MC_COLOR_TO_CONSOLE_LIST.append(('§l', Style.BRIGHT))  # bold
	MC_COLOR_TO_RCOLOR = _MC_COLOR_TO_RCOLOR
	RCOLOR_TO_CONSOLE = _RCOLOR_TO_CONSOLE
	MC_COLOR_TO_CONSOLE = dict(__MC_COLOR_TO_CONSOLE_LIST)

	# minecraft code -> console code
	@classmethod
	def convert_minecraft_color_code(cls, text):
		for key, value in cls.__MC_COLOR_TO_CONSOLE_LIST:
			if key in text:
				text = text.replace(key, value)
		return text


class RStyle:
	bold = "bold"
	italic = "italic"
	underlined = "underlined"
	strike_through = "strikethrough"
	obfuscated = "obfuscated"


class RAction:
	suggest_command = "suggest_command"
	run_command = "run_command"
	open_url = "open_url"
	open_file = "open_file"
	copy_to_clipboard = "copy_to_clipboard"


class RTextBase:
	def to_json_object(self):
		raise NotImplementedError()

	def to_json_str(self):
		return json.dumps(self.to_json_object())

	def to_plain_text(self):
		raise NotImplementedError()

	def to_colored_text(self):
		raise NotImplementedError()

	def copy(self):
		return copy.deepcopy(self)

	def set_click_event(self, action, value):
		"""
		:rtype: RTextBase
		"""
		raise NotImplementedError()

	def set_hover_text(self, *args):
		"""
		:rtype: RTextBase
		"""
		raise NotImplementedError()

	def c(self, action, value):
		"""
		:rtype: RTextBase
		"""
		return self.set_click_event(action, value)

	def h(self, *args):
		"""
		:rtype: RTextBase
		"""
		return self.set_hover_text(*args)

	def __str__(self):
		return self.to_plain_text()

	def __add__(self, other):
		return RTextList(self, other)

	def __radd__(self, other):
		return RTextList(other, self)

	@staticmethod
	def from_any(text):
		"""
		:param text: can be a RTextBase, or a str, or anything
		:rtype: RTextBase
		"""
		if isinstance(text, RTextBase):
			return text
		return RText(text)


class RText(RTextBase):
	def __init__(self, text, color=RColor.reset, styles=None):
		if styles is None:
			styles = {}
		elif isinstance(styles, str):
			styles = {styles}
		elif isinstance(styles, Iterable):
			styles = set(styles)
		else:
			raise TypeError('Unsupported style type {}'.format(type(styles)))
		if isinstance(text, type(self)):
			self.data = text.data.copy()
		else:
			self.data = {
				'text': str(text),
				'color': color
			}  # type: dict
			for style in [RStyle.bold, RStyle.italic, RStyle.underlined, RStyle.strike_through, RStyle.obfuscated]:
				if style in styles:
					self.data[style] = style in styles

	def to_json_object(self):
		return self.data

	def set_click_event(self, action, value):
		self.data['clickEvent'] = {
			'action': action,
			'value': value
		}
		return self

	def set_hover_text(self, *args):
		self.data['hoverEvent'] = {
			'action': 'show_text',
			'value': {
				'text': '',
				'extra': RTextList(*args).to_json_object(),
			}
		}
		return self

	def to_plain_text(self):
		return self.data['text']

	def to_colored_text(self):
		color = RColorConvertor.RCOLOR_TO_CONSOLE[self.data['color']]
		if self.data.get(RStyle.bold, False):
			color += Style.BRIGHT
		return color + self.to_plain_text() + Style.RESET_ALL


class RTextTranslation(RText):
	def __init__(self, translation_key, color=RColor.reset, styles=None):
		super().__init__(translation_key, color, styles)
		self.data.pop('text')
		self.data['translate'] = translation_key

	def to_plain_text(self):
		return self.data['translate']


class RTextList(RTextBase):
	def __init__(self, *args):
		self.header = RText('')
		self.header_empty = True
		self.children = []  # type: List[RTextBase or str]
		self.append(*args)

	def set_click_event(self, action, value):
		self.header.set_click_event(action, value)
		self.header_empty = False
		return self

	def set_hover_text(self, *args):
		self.header.set_hover_text(*args)
		self.header_empty = False
		return self

	def append(self, *args):
		for obj in args:
			if isinstance(obj, RTextList):
				self.children.extend(obj.children)
			elif isinstance(obj, RTextBase):
				self.children.append(obj)
			else:
				self.children.append(RText(obj))

	def empty(self):
		return len(self.children) == 0

	def __get_item_list(self, func=lambda x: x):
		return [func(obj) for obj in self.children]

	def to_json_object(self):
		ret = ['' if self.header_empty else self.header.to_json_object()]
		ret.extend(self.__get_item_list(lambda obj: obj.to_json_object()))
		return ret

	def to_plain_text(self):
		return ''.join(self.__get_item_list(lambda obj: obj.to_plain_text()))

	def to_colored_text(self):
		return ''.join(self.__get_item_list(lambda obj: obj.to_colored_text()))
