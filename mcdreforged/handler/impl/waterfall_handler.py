from typing import Optional

from parse import parse

from mcdreforged.handler.impl.bukkit_handler import BukkitHandler
from mcdreforged.handler.impl.bungeecord_handler import BungeecordHandler
from mcdreforged.info import Info


class WaterfallHandler(BungeecordHandler):
	# The logging format of waterfall server is paper like
	# [02:18:30 INFO]: Enabled plugin cmd_list version git:cmd_list:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
	# [02:18:29 INFO] [ViaVersion]: Loading 1.12.2 -> 1.13 mappings..."

	FORMATTERS = [
		BukkitHandler.get_content_parsing_formatter(),
		'[{hour:d}:{min:d}:{sec:d} {logging}] {why_this}: {content}'
	]

	def parse_server_stdout(self, text):
		result = self._get_server_stdout_raw_result(text)
		for formatter in self.FORMATTERS:
			try:
				self._content_parse(result, formatter=formatter)
				return result
			except:
				pass
		raise ValueError()

	def parse_player_joined(self, info: Info) -> Optional[str]:
		# [02:18:52 INFO]: [/127.0.0.1:14426] <-> InitialHandler has connected
		# sadly no player id display here
		return None

	def parse_player_left(self, info):
		# [/127.0.0.1:14426|Fallen_Breath] -> UpstreamBridge has disconnected
		if not info.is_user:
			parsed = parse('[/{ip}|{name}] -> UpstreamBridge has disconnected', info.content)
			if parsed is not None:
				return parsed['name']
		return None
