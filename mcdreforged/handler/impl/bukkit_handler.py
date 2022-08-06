from typing import List

from mcdreforged.handler.impl.abstract_minecraft_handler import AbstractMinecraftHandler


class BukkitHandler(AbstractMinecraftHandler):
	@classmethod
	def get_content_parsing_formatter(cls):
		return '[{hour:d}:{min:d}:{sec:d} {logging}]: {content}'

	@classmethod
	def get_player_message_parsing_formatter(cls) -> List[str]:
		return super().get_player_message_parsing_formatter() + ['[{dim_name}]<{name}> {message}']

