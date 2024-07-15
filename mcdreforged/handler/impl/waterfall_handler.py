import re
from typing import Optional

from typing_extensions import override

from mcdreforged.handler.impl.bungeecord_handler import BungeecordHandler
from mcdreforged.info_reactor.info import Info


class WaterfallHandler(BungeecordHandler):
	"""
	A handler for `Waterfall <https://github.com/PaperMC/Waterfall>`__ servers

	The logging format of waterfall server is paper like (waterfall is PaperMC's bungeecord fork shmm)
	"""

	# [02:18:30 INFO]: Enabled plugin cmd_list version git:cmd_list:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
	# [02:18:29 INFO] [ViaVersion]: Loading 1.12.2 -> 1.13 mappings..."
	@classmethod
	@override
	def get_content_parsing_formatter(cls):
		return re.compile(
			r'\[(?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+) (?P<logging>[^]]+)]'
			r'( \[[^]]+])?'  # useless logger name
			r': (?P<content>.*)'
		)

	@override
	def parse_player_joined(self, info: Info) -> Optional[str]:
		# [02:18:52 INFO]: [/127.0.0.1:14426] <-> InitialHandler has connected
		# sadly no player id display here
		return None

	# [/127.0.0.1:14426|Fallen_Breath] -> UpstreamBridge has disconnected
	__player_left_regex = re.compile(r'\[/[^|]+\|(?P<name>[^]]+)] -> UpstreamBridge has disconnected')

	@override
	def parse_player_left(self, info):
		if not info.is_user:
			if (m := self.__player_left_regex.fullmatch(info.content)) is not None:
				return m['name']
		return None
