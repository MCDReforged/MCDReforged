# Credit: Pandaria98 https://github.com/Pandaria98
# https://github.com/TISUnion/stext

# -*- coding: utf-8 -*-
import copy
import json
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

	# RColor -> console color
	@classmethod
	def to_console_code(cls, color):
		color_dict = {
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
		return color_dict[color]

	# minecraft code -> console code
	@classmethod
	def convert_minecraft_color_code(cls, text):
		mc_color_dict = {
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
		for key, value in mc_color_dict.items():
			text = text.replace(key, cls.to_console_code(value))
		text = text.replace('§l', Style.BRIGHT)  # bold
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
		pass

	def to_json_str(self):
		return json.dumps(self.to_json_object())

	def to_plain_text(self):
		pass

	def to_colored_text(self):
		pass

	def copy(self):
		return copy.deepcopy(self)

	def __str__(self):
		return self.to_plain_text()

	def __add__(self, other):
		return RTextList(self, other)

	def __radd__(self, other):
		return RTextList(other, self)


class RText(RTextBase):
	def __init__(self, text, color=RColor.reset, styles=None):
		if styles is None:
			styles = []
		elif styles is str:
			styles = [styles]
		if type(text) == type(self):
			self.data = text.data.copy()
		else:
			self.data = {
				'text': str(text),
				'color': color
			}  # type: dict
			for style in [RStyle.bold, RStyle.italic, RStyle.underlined, RStyle.strike_through, RStyle.obfuscated]:
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

	def c(self, action, value):
		return self.set_click_event(action, value)

	def h(self, *args):
		return self.set_hover_text(*args)

	def to_plain_text(self):
		return self.data['text']

	def to_colored_text(self):
		color = RColor.to_console_code(self.data['color'])
		if self.data['bold']:
			color += Style.BRIGHT
		return color + self.to_plain_text() + Style.RESET_ALL


class RTextList(RTextBase):
	def __init__(self, *args):
		self.data = []
		self.append(*args)

	def append(self, *args):
		for obj in args:
			if type(obj) is RTextList:
				self.data.extend(obj.data)
			elif type(obj) is RText:
				self.data.append(obj)
			else:
				self.data.append(RText(str(obj)))

	def to_json_object(self):
		return [''] + [t.to_json_object() for t in self.data]  # to disable style inherit

	def to_plain_text(self):
		return ''.join([obj.to_plain_text() for obj in self.data])

	def to_colored_text(self):
		return ''.join([obj.to_colored_text() for obj in self.data])
