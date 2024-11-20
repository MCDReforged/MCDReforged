import re

from typing_extensions import override

from mcdreforged.handler.impl import AbstractMinecraftHandler


class ForgeHandler(AbstractMinecraftHandler):
	"""
	A handler for `Forge <https://files.minecraftforge.net>`__ Minecraft servers
	"""

	# [18:26:03] [Server thread/INFO] [FML]: Unloading dimension 1
	# [18:26:03] [Server thread/INFO] [minecraft/DedicatedServer]: Done (9.855s)! For help, type "help" or "?"
	# [18:29:30] [Server thread/INFO] [minecraft/DedicatedServer]: <Steve> tests
	# [09:00:00] [Server thread/INFO]: <Steve> Hello  // vanilla format, in some old forge servers e.g. forge 1.7.10

	@classmethod
	@override
	def get_content_parsing_formatter(cls) -> re.Pattern:
		return re.compile(
			r'\[(?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+)]'
			r' \[(?P<thread>[^]]+)/(?P<logging>[^]/]+)]'
			r'( \[[^]]+])?'  # useless logger name
			r': (?P<content>.*)'
		)
