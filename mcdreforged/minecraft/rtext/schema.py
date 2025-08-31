import dataclasses
import enum


@dataclasses.dataclass(frozen=True)
class RTextJsonFormatItem:
	click_event_key: str
	hover_event_key: str


class RTextJsonFormat(enum.Enum):
	"""
	Define the serialization format of :class:`RText <RTextBase>` components for different Minecraft versions
	"""

	V_1_7 = RTextJsonFormatItem('clickEvent', 'hoverEvent')
	"""For Minecraft ``[1.7, 1.21.5)``"""

	V_1_21_5 = RTextJsonFormatItem('click_event', 'hover_event')
	"""For Minecraft ``[1.21.5, ~)``"""

	@classmethod
	def default(cls) -> 'RTextJsonFormat':
		return cls.V_1_7

	@classmethod
	def guess(cls, text_obj: dict) -> 'RTextJsonFormat':
		for key in [cls.V_1_21_5.value.click_event_key, cls.V_1_21_5.value.hover_event_key]:
			if key in text_obj:
				return cls.V_1_21_5
		return cls.default()
