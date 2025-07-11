from abc import ABC, ABCMeta, abstractmethod
from typing import Union, Optional, Dict, Iterator, TypeVar, Generic

from colorama import Fore, Style
from typing_extensions import override

from mcdreforged.utils.serializer import Serializable
from mcdreforged.utils import class_utils, string_utils


class __NamedObject(ABC):
	@property
	@abstractmethod
	def name(self) -> str:
		"""
		The unique identifier used in :class:`__RRegistry`
		"""
		raise NotImplementedError()


T = TypeVar('T', bound=__NamedObject)


class __RRegistry(ABCMeta, Generic[T]):
	def __init__(cls, *args, **kwargs):
		super().__init__(*args, **kwargs)
		cls._registry: Dict[str, T] = {}

	def __iter__(self) -> Iterator[T]:
		return iter(self._registry.values())

	def __contains__(self, item_name: str) -> bool:
		return item_name in self._registry

	def __getitem__(self, item_name: str) -> T:
		return self._registry[item_name]

	def register_item(self, name: str, item: T):
		from typing import get_type_hints
		assert name in get_type_hints(self), 'registering unknown item {} for class {} ({})'.format(name, self, type(self))

		self._registry[item.name] = item
		setattr(self, item.name, item)


class RItem(__NamedObject):
	"""
	A general Minecraft text style item
	"""

	@property
	@abstractmethod
	def name(self) -> str:
		"""
		Its value in Minecraft text component
		"""
		raise NotImplementedError()


class RItemClassic(RItem, ABC):
	"""
	A type of :class:`RItem` that can be represented with a classic "§"-prefixed formatting code,
	or a "\\\\033[31m" styled console ANSI escape code

	.. seealso:: Minecraft Wiki `Formatting codes <https://minecraft.wiki/w/Formatting_codes>`__ page
	"""
	def __init__(self, name: str, mc_code: str, console_code: str):
		self.__name: str = name
		assert len(mc_code) == 2 and mc_code[0] == '§'
		self.__mc_code: str = mc_code
		self.__console_code: str = console_code

	@property
	@override
	def name(self) -> str:
		return self.__name

	@property
	def mc_code(self) -> str:
		"""
		Its code in Minecraft, with "§" prefix
		"""
		return self.__mc_code

	@property
	def console_code(self) -> str:
		"""
		Its code in console, i.e. ANSI escape code

		It might be an empty str if there's no appropriate code
		"""
		return self.__console_code

	def __repr__(self) -> str:
		return class_utils.represent(self, {
			'name': self.name,
			'mc_code': self.mc_code,
			'console_code': self.console_code,
		})

# ------------------------------------------------
#                   Text Color
# ------------------------------------------------


class __RColorMeta(__RRegistry['RColor']):
	pass


class RColor(RItem, ABC, metaclass=__RColorMeta):
	"""
	Minecraft text colors
	"""
	black:        'RColorClassic'
	dark_blue:    'RColorClassic'
	dark_green:   'RColorClassic'
	dark_aqua:    'RColorClassic'
	dark_red:     'RColorClassic'
	dark_purple:  'RColorClassic'
	gold:         'RColorClassic'
	gray:         'RColorClassic'
	dark_gray:    'RColorClassic'
	blue:         'RColorClassic'
	green:        'RColorClassic'
	aqua:         'RColorClassic'
	red:          'RColorClassic'
	light_purple: 'RColorClassic'
	yellow:       'RColorClassic'
	white:        'RColorClassic'

	reset:        'RColorClassic'

	def __init__(self, rgb_code: int):
		class_utils.check_type(rgb_code, int)
		self._rgb_code: int = rgb_code  # e.g. 0xRRGGBB

	@classmethod
	def from_mc_value(cls, value: str) -> 'RColor':
		"""
		A factory function to create a :class:`RColor` object from a valid Minecraft color value

		:param value: The value of the ``color`` field in Minecraft text component.
			e.g. ``"red"``, ``"blue"``, ``"#00AAFF"``
		:return: A corresponding :class:`RColor` object
		:raise ValueError: If the given value is not a valid Minecraft color
		"""
		if value in cls._registry:
			return cls._registry[value]
		else:
			return RColorRGB.from_code(value)

	# RGB attributes

	@property
	def r(self) -> int:
		"""
		The red portion of the color in [0, 255]
		"""
		return (self._rgb_code >> 16) & 0xFF

	@property
	def g(self) -> int:
		"""
		The green portion of the color in [0, 255]
		"""
		return (self._rgb_code >> 8) & 0xFF

	@property
	def b(self) -> int:
		"""
		The blue portion of the color in [0, 255]
		"""
		return (self._rgb_code >> 0) & 0xFF


def __register_classic_rcolor():
	def register(name: str, rgb_hex: int, mc_code: str, console_code: str):
		RColor.register_item(name, RColorClassic(name, rgb_hex, mc_code, console_code))

	register('black',        0x000000, '§0', Fore.BLACK)
	register('dark_blue',    0x0000AA, '§1', Fore.BLUE)
	register('dark_green',   0x00AA00, '§2', Fore.GREEN)
	register('dark_aqua',    0x00AAAA, '§3', Fore.CYAN)
	register('dark_red',     0xAA0000, '§4', Fore.RED)
	register('dark_purple',  0xAA00AA, '§5', Fore.MAGENTA)
	register('gold',         0xFFAA00, '§6', Fore.YELLOW)
	register('gray',         0xAAAAAA, '§7', Fore.WHITE + Style.DIM)
	register('dark_gray',    0x555555, '§8', Fore.WHITE + Style.DIM)
	register('blue',         0x5555FF, '§9', Fore.LIGHTBLUE_EX)
	register('green',        0x55FF55, '§a', Fore.LIGHTGREEN_EX)
	register('aqua',         0x55FFFF, '§b', Fore.LIGHTCYAN_EX)
	register('red',          0xFF5555, '§c', Fore.LIGHTRED_EX)
	register('light_purple', 0xFF55FF, '§d', Fore.LIGHTMAGENTA_EX)
	register('yellow',       0xFFFF55, '§e', Fore.LIGHTYELLOW_EX)
	register('white',        0xFFFFFF, '§f', Fore.WHITE)

	# default text color is white, so use 0xFFFFFF
	register('reset',        0xFFFFFF, '§r', Style.RESET_ALL)


class RColorClassic(RItemClassic, RColor):
	"""
	Classic Minecraft text color defined with color name

	.. attention::

		Do not construct the class yourself. Use class fields in :class:`RColor` if you want to use classic colors
	"""
	def __init__(self, name: str, rgb_code: int, mc_code: str, console_code: str):
		super().__init__(name, mc_code, console_code)
		super(RItemClassic, self).__init__(rgb_code)
		self.__rgb_cache: Optional['RColorRGB'] = None

	def to_rgb(self) -> 'RColorRGB':
		"""
		Converts to the corresponding :class:`RColorRGB` object with the exact same color
		"""
		if self.__rgb_cache is None:  # concurrency invocation is fine
			self.__rgb_cache = RColorRGB(self._rgb_code)
		return self.__rgb_cache


class RColorRGB(RColor):
	"""
	Minecraft text color type in hexadecimal color format, with which you can specify
	the red / green / blue values of the color precisely

	.. note:: Available in Minecraft 1.16+
	"""
	def __init__(self, rgb_code: int):
		"""
		:param rgb_code: An int in hex 0xRRGGBB format,
			or a str like ``"RRGGBB"``, ``"0xRRGGBB"`` or ``"#RRGGBB"``
		"""
		class_utils.check_type(rgb_code, (str, int))
		super().__init__(rgb_code)
		self.__classic_cache: Optional['RColorClassic'] = None

	@classmethod
	def from_code(cls, rgb_code: Union[str, int]) -> 'RColorRGB':
		"""
		A factory function to create a :class:`RColorRGB` object using a single RGB code

		:param rgb_code: An int in hex 0xRRGGBB format,
			or a str like ``"RRGGBB"``, ``"0xRRGGBB"`` or ``"#RRGGBB"``
		"""
		class_utils.check_type(rgb_code, (str, int))
		if isinstance(rgb_code, str):
			hex_code = string_utils.remove_prefix(string_utils.remove_prefix(rgb_code, '0x'), '#')
			try:
				rgb_code = int(hex_code, 16)
			except ValueError:
				raise ValueError('Invalid rgb code {}'.format(repr(rgb_code))) from None
		return RColorRGB(rgb_code)

	@classmethod
	def from_rgb(cls, red: int, green: int, blue: int) -> 'RColorRGB':
		"""
		A factory function to create a :class:`RColorRGB` object using 3 RGB values

		:param red: The red portion of the color
		:param green: The green portion of the color
		:param blue: The blue portion of the color
		"""
		return cls.from_code((red << 16) | (green << 8) | (blue << 0))

	def __to_classic(self) -> 'RColorClassic':
		def calc_distance(x: RColorRGB, y: RColorRGB) -> int:
			return (x.r - y.r) ** 2 + (x.g - y.g) ** 2 + (x.b - y.b) ** 2

		result: Optional[RColorClassic] = None
		min_distance: int = 0
		for color in RColor:
			if isinstance(color, RColorClassic) and color != RColor.reset:  # ignore reset
				distance = calc_distance(self, color.to_rgb())
				if result is None or distance < min_distance:
					result = color
					min_distance = distance
		assert result is not None
		return result

	def to_classic(self) -> 'RColorClassic':
		"""
		Converts to the :class:`RColorClassic` object with the closest Euclidean distance in the RGB color space
		"""
		if self.__classic_cache is None:  # concurrency invocation is fine
			self.__classic_cache = self.__to_classic()
		return self.__classic_cache

	def __repr__(self) -> str:
		return class_utils.represent(self, {'rgb': '0x{:06X}'.format(self._rgb_code)})

	# Interface implementation

	@property
	@override
	def name(self) -> str:
		return '#{:06X}'.format(self._rgb_code)


__register_classic_rcolor()


# ------------------------------------------------
#                   Text Style
# ------------------------------------------------


class __RStyleMeta(__RRegistry['RStyle']):
	pass


class RStyle(RItem, ABC, metaclass=__RStyleMeta):
	"""
	Minecraft text styles
	"""
	bold:          'RStyleClassic'
	italic:        'RStyleClassic'
	underlined:    'RStyleClassic'
	strikethrough: 'RStyleClassic'
	obfuscated:    'RStyleClassic'


def __register_rstyle():
	def register(name: str, mc_code: str, console_code: str):
		RStyle.register_item(name, RStyleClassic(name, mc_code, console_code))

	register('bold',          '§l', Style.BRIGHT)
	register('italic',        '§o', '')
	register('underlined',    '§n', '')
	register('strikethrough', '§m', '')
	register('obfuscated',    '§k', '')


class RStyleClassic(RItemClassic, RStyle):
	"""
	Classic Minecraft text style with corresponding "§"-prefixed formatting code
	"""


__register_rstyle()


# ------------------------------------------------
#                  Text Special
# ------------------------------------------------


class __RHoverMeta(__RRegistry['RHover']):
	pass


class RHover(RItem, ABC, metaclass=__RStyleMeta):
	"""
	Minecraft hover event actions
	"""

	show_entity:     'RHover'
	"""Show an entity's information"""

	show_item:       'RHover'
	"""Show an item's information"""

	show_text:       'RHover'
	"""Display texts in hover event"""



def __register_rhover():
	def register(name: str):
		RHover.register_item(name, _RHoverImpl(name))

	register('show_entity')
	register('show_item')
	register('show_text')


class _RHoverImpl(RHover):
	def __init__(self, name: str):
		self.__name = name

	@property
	@override
	def name(self) -> str:
		return self.__name

	def __repr__(self) -> str:
		return class_utils.represent(self, {'action': self.name})


class RHoverComponents(Serializable):
	"""
	Internal components in hover event actions (except `show_text`)

	:param id: Generic id attribute for components
	"""
	id: str


class RHoverEntity(RHoverComponents, Serializable):
	"""
	Component for `show_entity` hover event action.

	:param name: Set display name of the target entity
	:param uuid: UUID of the target entity, format requirements see MinecraftWiki plz.
	"""
	name: str
	uuid: str  # uuid of the target entity, format requirements see MinecraftWiki plz.


class RHoverItem(RHoverComponents, Serializable):
	"""
	Component for `show_item` hover event action.

	:param count: Optional, the number of the target item.
		Due to it's not displayed actually, so set default to 1.
	:param components: Optional, receive extra item components by a custom dict object.
	"""
	count: Optional[int] = 1  # seems useless because it can't be displayed in hover event, but available.
	components: Optional[dict] = None  # Extra item info, can be empty.


__register_rhover()


class __RActionMeta(__RRegistry['RAction']):
	pass


class RAction(__NamedObject, ABC, metaclass=__RActionMeta):
	"""
	Minecraft click event actions
	"""

	suggest_command:   'RAction'
	"""Fill the chat bar with given text"""

	run_command:       'RAction'
	"""
	Run the given text as command
	
	(Minecraft <1.19.1) If the given text doesn't start with ``"/"``, the given text will be considered as a chat message and sent to the server,
	so it can be used to automatically execute MCDR command after the player click the decorated text
	
	.. attention:: 
	
		In vanilla Minecraft >=1.19.1, only strings starting with ``"/"``, i.e. command strings, can be used as the text value of :attr:`run_command` action
		
		For other strings that don't start with ``"/"``, the client will reject to send the chat message
		
		See `Issue #203 <https://github.com/MCDReforged/MCDReforged/issues/203>`__
	"""

	open_url:          'RAction'
	"""Open given url"""

	open_file:         'RAction'
	"""
	Open file from given path
	
	.. note:: 
	
		Actually vanilla Minecraft doesn't allow texts sent by command contain :attr:`open_file` actions,
		so don't be surprised if this :attr:`open_file` doesn't work
	"""

	copy_to_clipboard: 'RAction'
	"""
	Copy given text to clipboard
	
	.. note:: Available in Minecraft 1.15+
	"""


def __register_raction():
	def register(name: str):
		RAction.register_item(name, _RActionImpl(name))

	register('suggest_command')
	register('run_command')
	register('open_url')
	register('open_file')
	register('copy_to_clipboard')


class _RActionImpl(RAction):
	def __init__(self, name: str):
		self.__name = name

	@property
	@override
	def name(self) -> str:
		return self.__name

	def __repr__(self) -> str:
		return class_utils.represent(self, {'name': self.name})


__register_raction()
