from typing import List

from mcdreforged.handler.impl.abstract_minecraft_handler import AbstractMinecraftHandler


class BukkitHandler(AbstractMinecraftHandler):
	"""
	A handler for `bukkit <https://www.spigotmc.org/wiki/buildtools>`__
	and bukkit-like (e.g. `Paper <https://github.com/PaperMC/Paper>`__) Minecraft servers
	"""
	@classmethod
	def get_content_parsing_formatter(cls):
		return '[{hour:d}:{min:d}:{sec:d} {logging}]: {content}'

	@classmethod
	def get_player_message_parsing_formatter(cls) -> List[str]:
		return super().get_player_message_parsing_formatter() + ['[{dim_name}]<{name}> {message}']

