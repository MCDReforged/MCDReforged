# Link to mcdreforged.rtext
# The advance text component class for Minecraft
from mcdreforged.minecraft.rtext.click_event import RClickAction, RClickEvent, RAction, RClickSuggestCommand, RClickRunCommand, RClickOpenUrl, RClickOpenFile, RClickCopyToClipboard
from mcdreforged.minecraft.rtext.hover_event import RHoverAction, RHoverEvent, RHoverText, RHoverEntity, RHoverItem
from mcdreforged.minecraft.rtext.schema import RTextJsonFormat
from mcdreforged.minecraft.rtext.style import RColor, RStyle, RColorClassic, RColorRGB, RStyleClassic
from mcdreforged.minecraft.rtext.text import RTextTranslation, RTextList, RTextBase, RText
from mcdreforged.translation.translation_text import RTextMCDRTranslation

__all__ = [
	# color and style
	'RColor', 'RColorRGB', 'RColorClassic',
	'RStyle', 'RStyleClassic',

	# click event
	'RClickAction', 'RAction', 'RClickEvent',
	'RClickSuggestCommand', 'RClickRunCommand', 'RClickOpenUrl', 'RClickOpenFile', 'RClickCopyToClipboard',

	# hover event
	'RHoverAction', 'RHoverEvent',
	'RHoverText', 'RHoverEntity', 'RHoverItem',

	# text component
	'RTextBase', 'RText', 'RTextTranslation', 'RTextList',
	'RTextMCDRTranslation',

	# text serialization
	'RTextJsonFormat',
]
