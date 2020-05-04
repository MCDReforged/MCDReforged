# Credit: Pandaria98 https://github.com/Pandaria98
# https://github.com/TISUnion/stext

# -*- coding: utf-8 -*-

import json


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

	def __str__(self):
		return self.to_plain_text()

	def __add__(self, other):
		return RTextList(self, other)

	def __radd__(self, other):
		return RTextList(other, self)


class RText(RTextBase):
	def __init__(self, text, color=RColor.white, styles=None):
		if styles is None:
			styles = []
		elif styles is str:
			styles = [styles]
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

	def to_plain_text(self):
		return self.data['text']


class RTextList(RTextBase):
	def __init__(self, *args):
		self.data = []
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

