import re
from typing import List

from typing_extensions import override

from mcdreforged.handler.impl.abstract_minecraft_handler import AbstractMinecraftHandler


class BukkitHandler(AbstractMinecraftHandler):
	"""
	A handler for `bukkit <https://www.spigotmc.org/wiki/buildtools>`__
	and bukkit-like (e.g. `Paper <https://github.com/PaperMC/Paper>`__) Minecraft servers
	"""
	@classmethod
	@override
	def get_content_parsing_formatter(cls) -> re.Pattern:
		# [00:12:10 INFO]: foo bar
		return re.compile(
			r'\[(?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+) (?P<logging>[^]]+)]'
			r': (?P<content>.*)'
		)

	@classmethod
	@override
	def get_player_message_parsing_formatter(cls) -> List[re.Pattern]:
		# [Not Secure] <Alex> hello
		# [world_nether]<Alex> world
		return [re.compile(
			r'(\[Not Secure] )?'  # mc1.19+ un-verified chat message
			r'(\[[a-z0-9_:]+])?'  # dimension name
			r'<(?P<name>[^>]+)> (?P<message>.*)'
		)]

