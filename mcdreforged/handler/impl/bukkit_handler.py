from parse import parse

from mcdreforged.handler.impl.abstract_minecraft_handler import AbstractMinecraftHandler


class BukkitHandler(AbstractMinecraftHandler):
	@classmethod
	def get_content_parsing_formatter(cls):
		return '[{hour:d}:{min:d}:{sec:d} {logging}]: {content}'

	def parse_server_stdout(self, text):
		result = super().parse_server_stdout(text)
		if result.player is None:
			parsed = parse('[{dim_name}]<{name}> {message}', result.content)
			if parsed is not None and self._verify_player_name(parsed['name']):
				result.player, result.content = parsed['name'], parsed['message']
		return result

