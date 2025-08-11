import contextlib
import json
from abc import ABC, abstractmethod
from typing import Iterable, List, Union, Optional, Any, Tuple, Set, Dict, TypeVar, overload

from colorama import Style
from typing_extensions import Self, override, TypedDict, NotRequired, Unpack, final

from mcdreforged.minecraft.rtext.click_event import RClickAction, RClickEvent, RClickEventSingleValue
from mcdreforged.minecraft.rtext.hover_event import RHoverEvent, RHoverText
from mcdreforged.minecraft.rtext.schema import RTextJsonFormat
from mcdreforged.minecraft.rtext.style import RStyle, RColor, RColorClassic, RColorRGB, RItemClassic
from mcdreforged.utils import class_utils

_T = TypeVar('_T')
_UNSET = object()


class RTextBase(ABC):
	"""
	An abstract base class of Minecraft text component
	"""
	class ToJsonKwargs(TypedDict):
		json_format: NotRequired[RTextJsonFormat]

	class FromJsonKwargs(TypedDict):
		json_format: NotRequired[Optional[RTextJsonFormat]]  # None means auto-detect

	@abstractmethod
	def to_json_object(self, **kwargs: Unpack[ToJsonKwargs]) -> Union[dict, list]:
		"""
		Return an object representing its data that can be serialized into a json string
		"""
		raise NotImplementedError()

	def to_json_str(self, **kwargs: Unpack[ToJsonKwargs]) -> str:
		"""
		Return a json formatted str representing its data

		It can be used as the second parameter in Minecraft command ``/tellraw <target> <message>`` and more
		"""
		return json.dumps(self.to_json_object(**kwargs), ensure_ascii=False, separators=(',', ':'))

	@abstractmethod
	def to_plain_text(self) -> str:
		"""
		Return a plain text for console display

		Click event and hover event will be ignored
		"""
		raise NotImplementedError()

	@abstractmethod
	def to_colored_text(self) -> str:
		"""
		Return a colored text stained with ANSI escape code for console display

		Click event and hover event will be ignored
		"""
		raise NotImplementedError()

	@abstractmethod
	def to_legacy_text(self) -> str:
		"""
		Return a colored text stained with classic "§"-prefixed Minecraft formatting code

		Click event and hover event will be ignored
		"""
		raise NotImplementedError()

	@abstractmethod
	def copy(self) -> Self:
		"""
		Return a deep copy version of itself
		"""
		raise NotImplementedError()

	@abstractmethod
	def set_color(self, color: RColor) -> Self:
		"""
		Set the color of the text and return the text component itself
		"""
		raise NotImplementedError()

	@abstractmethod
	def set_styles(self, styles: Union[RStyle, Iterable[RStyle]]) -> Self:
		"""
		Set the styles of the text and return the text component itself
		"""
		raise NotImplementedError()

	@overload
	def set_click_event(self, click_event: RClickEvent) -> Self:
		"""
		Set the click event of the text directly
		"""
		...

	@overload
	def set_click_event(self, action: RClickAction[RClickEventSingleValue[_T]], value: _T) -> Self:
		"""
		Set the click event of the text by providing the action type and the action value

		This overload works for click actions that accept exactly 1 argument
		"""
		...

	@final
	def set_click_event(self, action: Union[RClickEvent, RClickAction[RClickEventSingleValue[_T]]], value: _T = _UNSET) -> Self:
		"""
		Set the click event

		You can either directly provide the click event, or provide the action type and the action value separately

		.. code-block:: python

			text = RText('example')

			text.set_click_event(RClickSuggestCommand('/say something'))  # directly
			text.set_click_event(RClickAction.suggest_command, '/say something')  # action + value

		Method :meth:`c` is the short form of :meth:`set_click_event`
		"""
		if value is not _UNSET:
			if not isinstance(action, RClickAction):
				raise TypeError('The action parameter should be a valid RClickAction if value is provided, but got {}'.format(type(action)))

			event_class = action.event_class
			if issubclass(event_class, RClickEventSingleValue):
				if value is _UNSET:
					raise ValueError('value arg not provided')
				return self._set_click_event_direct(event_class.from_json_value(value))
			else:
				raise TypeError('Unsupported action type {} with event class {}'.format(type(action), event_class))
		elif isinstance(action, RClickEvent):
			return self._set_click_event_direct(action)
		else:
			raise TypeError('Unexpected argument type {}'.format(type(action)))

	@abstractmethod
	def _set_click_event_direct(self, click_event: RClickEvent) -> Self:
		raise NotImplementedError()

	@abstractmethod
	def set_hover_event(self, hover_event: RHoverEvent) -> Self:
		"""
		Set the hover event
		"""
		raise NotImplementedError()

	def set_hover_text(self, *args) -> Self:
		"""
		Set the hover text

		Method :meth:`h` is the short form of :meth:`set_hover_text`

		:param args: The elements be used to create a :class:`RTextList` instance.
			The :class:`RTextList` instance is used as the actual hover text
		:return: The text component itself
		"""
		for arg in args:
			# typo checker
			if isinstance(arg, RHoverEvent):
				raise TypeError(f'Argument can not be a RHoverEvent, got {arg!r}. If you want to directly set the hover event, use `set_hover_event` instead')

		if len(args) == 1:
			text = RTextBase.from_any(args[0])
		else:
			text = RTextList(*args)
		self.set_hover_event(RHoverText(text=text))
		return self

	c = set_click_event
	"""
	Alias of :meth:`set_click_event`
	"""

	h = set_hover_text
	"""
	Alias of :meth:`set_hover_text`
	"""

	def __str__(self):
		return self.to_plain_text()

	def __add__(self, other):
		return RTextList(self, other)

	def __radd__(self, other):
		return RTextList(other, self)

	@staticmethod
	def from_any(text) -> 'RTextBase':
		"""
		Convert anything into a RText component
		"""
		if isinstance(text, RTextBase):
			return text
		return RText(text)

	@staticmethod
	def join(divider: Any, iterable: Iterable[Any]) -> 'RTextBase':
		"""
		Just like method :meth:`str.join`, it concatenates any number of texts with *divider*

		Example::

			>>> text = RTextBase.join(',', [RText('1'), '2', 3])
			>>> text.to_plain_text()
			'1,2,3'

		:param divider: The divider between elements. The divider object will be reused
		:param iterable: The elements to be joined
		"""
		result = RTextList()
		for i, item in enumerate(iterable):
			if i > 0:
				result.append(divider)
			result.append(item)
		return result

	@staticmethod
	def format(fmt: str, *args, **kwargs) -> 'RTextBase':
		"""
		Just like method :meth:`str.format`, it uses *\\*args* and *\\*\\*kwargs* to build a formatted RText component based on the formatter *fmt*

		Example::

			>>> text = RTextBase.format('a={},b={},c={c}', RText('1', color=RColor.blue), '2', c=3)
			>>> text.to_plain_text()
			'a=1,b=2,c=3'

		:param fmt: The formatter string
		:param args: The given arguments
		:param kwargs: The given keyword arguments
		"""
		args = list(args)
		kwargs = kwargs.copy()
		placeholder_counter = 0
		rtext_elements: List[Tuple[str, RTextBase]] = []

		def acquire_placeholder():
			nonlocal placeholder_counter
			ph = '@@MCDR#RText.FMT#PH#{}@@'.format(placeholder_counter)
			placeholder_counter += 1
			return ph

		for i, arg in enumerate(args):
			if isinstance(arg, RTextBase):
				placeholder = acquire_placeholder()
				rtext_elements.append((placeholder, arg))
				args[i] = placeholder
		for key, value in kwargs.items():
			if isinstance(value, RTextBase):
				placeholder = acquire_placeholder()
				rtext_elements.append((placeholder, value))
				kwargs[key] = placeholder

		texts: List[Union[str, RTextBase]] = [fmt.format(*args, **kwargs)]
		for placeholder, rtext in rtext_elements:
			new_texts: List[Union[str, RTextBase]] = []
			for text in texts:
				processed_text: List[Union[str, RTextBase]] = []
				if isinstance(text, str):
					for j, ele in enumerate(text.split(placeholder)):
						if j > 0:
							processed_text.append(rtext)
						if len(ele) > 0:
							processed_text.append(ele)
				else:
					processed_text.append(text)
				new_texts.extend(processed_text)
			texts = new_texts
		return RTextList(*texts)

	@classmethod
	def __from_json_list(cls, data: list, json_format: Optional[RTextJsonFormat]) -> 'RTextBase':
		text = RTextList()
		if len(data) == 0:
			return text
		lst = [cls.from_json_object(item, json_format=json_format) for item in data]
		if data[0] != '':
			text.set_header_text(lst[0])
		text.append(*lst[1:])
		return text

	@classmethod
	def __from_json_dict(cls, data: dict, json_format: Optional[RTextJsonFormat]) -> 'RTextBase':
		text: RTextBase
		if 'text' in data:
			text = RText(data['text'])
		elif 'translate' in data:
			tr_args = data.get('with', [])
			text = RTextTranslation(data['translate']).arg(*map(cls.from_json_object, tr_args))
		else:
			raise ValueError('No method to create RText from {}'.format(data))
		if isinstance(siblings := data.get('extra'), list):
			text_list = RTextList()
			text_list.set_header_text(text)
			text_list.append(*map(cls.from_json_object, siblings))
			text = text_list

		styles: List[RStyle] = []
		for style in RStyle:
			if data.get(style.name, False):
				styles.append(style)
		text.set_styles(styles)

		if isinstance(color := data.get('color'), str):
			with contextlib.suppress(ValueError):
				text.set_color(RColor.from_mc_value(color))

		if json_format is None:
			json_format = RTextJsonFormat.guess(data)
		with contextlib.suppress(KeyError):
			if isinstance(click_event := data[json_format.value.click_event_key], dict):
				text._set_click_event_direct(RClickEvent.from_json_object(click_event, json_format))
		with contextlib.suppress(KeyError):
			if isinstance(hover_event := data[json_format.value.hover_event_key], dict):
				text.set_hover_event(RHoverEvent.from_json_object(hover_event, json_format))

		return text

	@classmethod
	def from_json_object(cls, data: Union[str, list, dict], **kwargs: Unpack[FromJsonKwargs]) -> 'RTextBase':
		"""
		Convert a json object into a :class:`RText <RTextBase>` component

		Example::

			>>> text = RTextBase.from_json_object({'text': 'my text', 'color': 'red'})
			>>> text.to_plain_text()
			'my text'
			>>> text.to_json_object()['color']
			'red'

		:param data: A json object

		.. versionadded:: v2.4.0
		"""
		json_format = kwargs.get('json_format')
		if isinstance(data, str):
			return cls.from_any(data)
		if isinstance(data, list):
			return cls.__from_json_list(data, json_format)
		elif isinstance(data, dict):
			return cls.__from_json_dict(data, json_format)
		else:
			raise TypeError('Unsupported data {!r}'.format(data))


class RText(RTextBase):
	"""
	The regular text component class
	"""

	def __init__(self, text: Any, color: Optional[RColor] = None, styles: Optional[Union[RStyle, Iterable[RStyle]]] = None):
		"""
		Create a :class:`RText` object with specific text, optional color and optional style

		:param text: The content of the text. It will be converted into str
		:param color: Optional, the color of the text
		:param styles: Optional, the style of the text. It can be a single :class:`~mcdreforged.minecraft.rtext.style.RStyle`
			or an iterable of :class:`~mcdreforged.minecraft.rtext.style.RStyle`
		"""
		self.__text: str = str(text) if type(text) is not str else text
		self.__color: Optional[RColor] = None
		self.__styles: Set[RStyle] = set()
		self.__click_event: Optional[RClickEvent] = None
		self.__hover_event: Optional[RHoverEvent] = None
		if color is not None:
			self.set_color(color)
		if styles is not None:
			self.set_styles(styles)

	@override
	def set_color(self, color: RColor) -> Self:
		self.__color = color
		return self

	@override
	def set_styles(self, styles: Union[RStyle, Iterable[RStyle]]) -> Self:
		if isinstance(styles, RStyle):
			styles = {styles}
		elif isinstance(styles, Iterable):
			styles = set(styles)
		else:
			raise TypeError('Unsupported style type {}'.format(type(styles)))
		self.__styles = styles
		return self

	@override
	def _set_click_event_direct(self, click_event: RClickEvent) -> Self:
		self.__click_event = click_event
		return self

	@override
	def set_hover_event(self, hover_event: RHoverEvent) -> Self:
		self.__hover_event = hover_event
		return self

	@override
	def to_json_object(self, **kwargs: Unpack[RTextBase.ToJsonKwargs]) -> Union[dict, list]:
		json_format = kwargs.get('json_format', RTextJsonFormat.default())
		obj: Dict[str, Any] = {'text': self.__text}
		if self.__color is not None:
			obj['color'] = self.__color.name
		for style in self.__styles:
			obj[style.name] = True
		if self.__click_event is not None:
			obj[json_format.value.click_event_key] = self.__click_event.to_json_object(json_format)
		if self.__hover_event is not None:
			obj[json_format.value.hover_event_key] = self.__hover_event.to_json_object(json_format)
		return obj

	@override
	def to_plain_text(self) -> str:
		return self.__text

	def _get_console_style_codes(self) -> str:
		if isinstance(self.__color, RColorClassic):
			color = self.__color.console_code
		elif isinstance(self.__color, RColorRGB):
			color = self.__color.to_classic().console_code
		else:
			color = ''
		for style in self.__styles:
			if isinstance(style, RItemClassic):
				color += style.console_code
		return color

	@override
	def to_colored_text(self) -> str:
		head = self._get_console_style_codes()
		tail = Style.RESET_ALL if len(head) > 0 else ''
		return head + self.to_plain_text() + tail

	def _get_legacy_style_codes(self) -> str:
		if isinstance(self.__color, RColorClassic):
			color = self.__color.mc_code
		elif isinstance(self.__color, RColorRGB):
			color = self.__color.to_classic().mc_code
		else:
			color = ''
		for style in self.__styles:
			if isinstance(style, RItemClassic):
				color += style.mc_code
		return color

	@override
	def to_legacy_text(self) -> str:
		head = self._get_legacy_style_codes()
		tail = RColor.reset.mc_code if len(head) > 0 else ''
		return head + self.to_plain_text() + tail

	def _copy_from(self, text: 'RText'):
		self.__text = text.__text
		self.__color = text.__color
		self.__styles = text.__styles.copy()
		self.__click_event = text.__click_event
		self.__hover_event = text.__hover_event

	@override
	def copy(self) -> 'RText':
		copied = RText('')
		copied._copy_from(self)
		return copied

	def __repr__(self) -> str:
		return class_utils.represent(self, fields={
			'text': self.__text,
			'color': self.__color,
			'styles': self.__styles,
			'click_event': self.__click_event,
			'hover_event': self.__hover_event,
		})

	def __eq__(self, other: 'RText') -> bool:
		"""
		.. versionadded:: v2.15.0
		"""
		if type(other) != type(self):
			return False
		return all((
			self.__text == other.__text,
			self.__color == other.__color,
			self.__styles == other.__styles,
			self.__click_event == other.__click_event,
			self.__hover_event == other.__hover_event,
		))


class RTextList(RTextBase):
	"""
	A list of :class:`RTextBase` objects, a compound text component
	"""
	def __init__(self, *args):
		"""
		Use the given *\\*args* to create a :class:`RTextList`

		:param args: The items in this :class:`RTextList`. They can be :class:`str`, :class:`RTextBase`
			or any class implements ``__str__`` method. All non- :class:`RTextBase` items
			will be converted to :class:`RText`
		"""
		self.header = RText('')
		self.header_empty = True
		self.children: List[RTextBase] = []
		self.append(*args)

	@override
	def set_color(self, color: RColor) -> Self:
		self.header.set_color(color)
		self.header_empty = False
		return self

	@override
	def set_styles(self, styles: Union[RStyle, Iterable[RStyle]]) -> Self:
		self.header.set_styles(styles)
		self.header_empty = False
		return self

	@override
	def _set_click_event_direct(self, click_event: RClickEvent) -> Self:
		# noinspection PyProtectedMember
		self.header._set_click_event_direct(click_event)
		self.header_empty = False
		return self

	@override
	def set_hover_event(self, hover_event: RHoverEvent) -> Self:
		self.header.set_hover_event(hover_event)
		self.header_empty = False
		return self

	def set_header_text(self, header_text: RTextBase) -> Self:
		self.header = header_text
		self.header_empty = False
		return self

	def append(self, *args) -> Self:
		for obj in args:
			self.children.append(RTextBase.from_any(obj))
		return self

	def is_empty(self) -> bool:
		return len(self.children) == 0

	@override
	def to_json_object(self, **kwargs: Unpack[RTextBase.ToJsonKwargs]) -> Union[dict, list]:
		ret = ['' if self.header_empty else self.header.to_json_object(**kwargs)]
		ret.extend([rtext.to_json_object(**kwargs) for rtext in self.children])
		return ret

	@override
	def to_plain_text(self) -> str:
		return ''.join(rtext.to_plain_text() for rtext in self.children)

	@override
	def to_colored_text(self) -> str:
		# noinspection PyProtectedMember
		head = self.header._get_console_style_codes()
		tail = Style.RESET_ALL if len(head) > 0 else ''
		return ''.join(
			''.join([head, rtext.to_colored_text(), tail])
			for rtext in self.children
		)

	@override
	def to_legacy_text(self) -> str:
		# noinspection PyProtectedMember
		head = self.header._get_legacy_style_codes()
		tail = RColor.reset.mc_code if len(head) > 0 else ''
		return ''.join(
			''.join([head, rtext.to_legacy_text(), tail])
			for rtext in self.children
		)

	@override
	def copy(self) -> 'RTextList':
		copied = RTextList()
		copied.header = self.header.copy()
		copied.header_empty = self.header_empty
		copied.children = [child.copy() for child in self.children]
		return copied

	def __repr__(self) -> str:
		return class_utils.represent(self, {
			'header': None if self.header_empty else self.header,
			'children': self.children
		})

	def __eq__(self, other: 'RTextList') -> bool:
		"""
		.. versionadded:: v2.15.0
		"""
		if type(other) != type(self):
			return False
		return all((
			self.header == other.header,
			self.header_empty == other.header_empty,
			self.children == other.children,
		))


class RTextTranslation(RText):
	"""
	The translation text component class. It's almost the same as :class:`RText`
	"""
	def __init__(self, translation_key: str, color: RColor = RColor.reset, styles: Optional[Union[RStyle, Iterable[RStyle]]] = None):
		"""
		Create a :class:`RTextTranslation` object with specific translation key.
		The rest of the parameters are the same to the constructor of :class:`RText`

		Use method :meth:`arg` to set the translation arguments, if the translation requires some arguments

		Example::

			RTextTranslation('advancements.nether.root.title', color=RColor.red)

		:param translation_key: The translation key
		:param color: Optional, the color of the text
		:param styles: Optional, the style of the text. It can be a single :class:`~mcdreforged.minecraft.rtext.style.RStyle`
			or a collection of :class:`~mcdreforged.minecraft.rtext.style.RStyle`
		"""

		super().__init__(translation_key, color, styles)
		self.__translation_key: str = translation_key
		self.__args: tuple = ()
		self.__fallback: Optional[str] = None

	def arg(self, *args: Any) -> Self:
		"""
		Set the translation arguments

		:param args: The translation arguments
		"""
		self.__args = args
		return self

	def fallback(self, fallback: str) -> Self:
		"""
		Set the translation fallback

		.. attention::

			Works in Minecraft >= 1.19.4 only

		:param fallback: The fallback text if the translation is unknown
		"""
		self.__fallback = fallback
		return self

	@override
	def to_plain_text(self) -> str:
		return self.__translation_key

	@override
	def to_json_object(self, **kwargs: Unpack[RTextBase.ToJsonKwargs]) -> Union[dict, list]:
		obj = super().to_json_object(**kwargs)
		obj.pop('text')
		obj['translate'] = self.__translation_key
		if len(self.__args) > 0:
			obj['with'] = [
				arg.to_json_object()
				if isinstance(arg, RTextBase)
				else arg  # keep it as-is
				for arg in self.__args
			]
		if self.__fallback is not None:
			obj['fallback'] = self.__fallback
		return obj

	@override
	def _copy_from(self, text: 'RTextTranslation'):
		super()._copy_from(text)
		self.__translation_key = text.__translation_key
		self.__args = text.__args

	@override
	def copy(self) -> 'RTextTranslation':
		copied = RTextTranslation('')
		copied._copy_from(self)
		return copied

	def __repr__(self) -> str:
		return class_utils.represent(self, fields={
			'key': self.__translation_key,
			'args': self.__args,
			'fallback': self.__fallback,
			'color': self.__color,
			'styles': self.__styles,
			'click_event': self.__click_event,
			'hover_event': self.__hover_event,
		})

	def __eq__(self, other: 'RTextTranslation') -> bool:
		"""
		.. versionadded:: v2.15.0
		"""
		if type(other) != type(self):
			return False
		return all((
			super().__eq__(other),
			self.__translation_key == other.__translation_key,
			self.__args == other.__args,
			self.__fallback == other.__fallback,
		))
