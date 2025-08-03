import dataclasses
import enum

from typing_extensions import Self


@dataclasses.dataclass(frozen=True)
class RTextJsonFormatItem:
	click_event_key: str
	hover_event_key: str


class RTextJsonFormat(enum.Enum):
	V_1_7 = RTextJsonFormatItem('clickEvent', 'hoverEvent')  # Minecraft [1.7, 1.21.5)
	V_1_21_5 = RTextJsonFormatItem('click_event', 'hover_event')  # Minecraft [1.21.5, ~)

	@classmethod
	def default(cls) -> Self:
		return cls.V_1_7

	@classmethod
	def guess(cls, text_obj: dict) -> Self:
		for key in [cls.V_1_21_5.value.click_event_key, cls.V_1_21_5.value.hover_event_key]:
			if key in text_obj:
				return cls.V_1_21_5
		return cls.default()
