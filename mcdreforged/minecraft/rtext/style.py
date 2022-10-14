from enum import Enum, auto

from colorama import Fore, Style

from mcdreforged.utils import class_util


class RItem:
	"""
	A general Minecraft text style item
	"""
	def __init__(self, mc_code: str, console_code: str):
		self.mc_code: str = mc_code
		"""It's code in Minecraft"""
		self.console_code: str = console_code
		"""It's code in console"""

	def __repr__(self):
		return class_util.represent(self)


class RColor(Enum):
	"""
	Minecraft text colors
	"""
	black = RItem('§0', Fore.BLACK)
	dark_blue = RItem('§1', Fore.BLUE)
	dark_green = RItem('§2', Fore.GREEN)
	dark_aqua = RItem('§3', Fore.CYAN)
	dark_red = RItem('§4', Fore.RED)
	dark_purple = RItem('§5', Fore.MAGENTA)
	gold = RItem('§6', Fore.YELLOW)
	gray = RItem('§7', Style.RESET_ALL)
	dark_gray = RItem('§8', Style.RESET_ALL)
	blue = RItem('§9', Fore.LIGHTBLUE_EX)
	green = RItem('§a', Fore.LIGHTGREEN_EX)
	aqua = RItem('§b', Fore.LIGHTCYAN_EX)
	red = RItem('§c', Fore.LIGHTRED_EX)
	light_purple = RItem('§d', Fore.LIGHTMAGENTA_EX)
	yellow = RItem('§e', Fore.LIGHTYELLOW_EX)
	white = RItem('§f', Style.RESET_ALL)

	reset = RItem('§r', Style.RESET_ALL)


class RColorConvertor:
	MC_COLOR_TO_CONSOLE = dict([(rcolor.value.mc_code, rcolor.value.console_code) for rcolor in RColor])
	MC_COLOR_TO_RCOLOR = dict([(rcolor.value.mc_code, rcolor) for rcolor in RColor])
	RCOLOR_TO_CONSOLE = dict([(rcolor, rcolor.value.console_code) for rcolor in RColor])
	RCOLOR_NAME_TO_CONSOLE = dict([(rcolor.name, rcolor.value.console_code) for rcolor in RColor])


class RStyle(Enum):
	"""
	Minecraft text styles
	"""
	bold = RItem('§l', Style.BRIGHT)
	italic = RItem('§o', '')
	underlined = RItem('§n', '')
	strikethrough = RItem('§m', '')
	obfuscated = RItem('§k', '')


class RAction(Enum):
	"""
	Minecraft click event actions
	"""

	suggest_command = auto()
	"""Fill the chat bar with given text"""

	run_command = auto()
	"""Run the given text as command"""

	open_url = auto()
	"""Open given url"""

	open_file = auto()
	"""Open file from given path"""

	copy_to_clipboard = auto()
	"""
	Copy given text to clipboard
	
	.. note:: Available in Minecraft 1.15+
	"""

