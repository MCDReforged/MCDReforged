# Credit: Pandaria98
# https://github.com/TISUnion/stext

# -*- coding: utf-8 -*-

import json


class SColor:
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


class SStyle:
	bold = "bold"
	italic = "italic"
	underlined = "underlined"
	strike_through = "strikethrough"
	obfuscated = "obfuscated"


class SAction:
	suggest_command = "suggest_command"
	run_command = "run_command"
	open_url = "open_url"
	open_file = "open_file"
	copy_to_clipboard = "copy_to_clipboard"


class STextBase:
	def to_json_object(self):
		pass

	def to_json_str(self):
		return json.dumps(self.to_json_object())

	def to_plain_text(self):
		pass

	def show_to_player(self, server, player):
		server.execute('tellraw {} {}'.format(player, self.to_json_str()))

	def __str__(self):
		return self.to_plain_text()


class SText(STextBase):
	def __init__(self, text, color=SColor.white, styles=None):
		if styles is None:
			styles = []
		elif styles is str:
			styles = [styles]
		self.data = {
			'text': str(text),
			'color': color
		}  # type: dict
		for style in [SStyle.bold, SStyle.italic, SStyle.underlined, SStyle.strike_through, SStyle.obfuscated]:
			self.data[style] = style in styles

	def to_json_object(self):
		return self.data

	def set_click_event(self, action, value):
		self.data['clickEvent'] = {
			'action': action,
			'value': value
		}
		return self

	def set_hover_event(self, *args):
		self.data['hoverEvent'] = {
			'action': 'show_text',
			'value': {
				'text': '',
				'extra': STextList(*args).to_json_object(),
			}
		}
		return self

	def __add__(self, other):
		return STextList(self, other)

	def to_plain_text(self):
		return self.data['text']


class STextList(STextBase):
	def __init__(self, *args):
		self.data = []
		for obj in args:
			if type(obj) is STextList:
				self.data.extend(obj.data)
			elif type(obj) is SText:
				self.data.append(obj)
			else:
				self.data.append(SText(str(obj)))

	def to_json_object(self):
		return [t.to_json_object() for t in self.data]

	def to_plain_text(self):
		return ''.join([obj.to_plain_text() for obj in self.data])

	def __add__(self, other):
		return STextList(self, other)
