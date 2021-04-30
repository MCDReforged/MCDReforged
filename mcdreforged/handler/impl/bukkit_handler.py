from parse import parse

from mcdreforged.handler.impl.vanilla_handler import VanillaHandler


class BukkitHandler(VanillaHandler):
	@classmethod
	def get_content_parsing_formatter(cls):
		return '[{hour:d}:{min:d}:{sec:d} {logging}]: {content}'

	def parse_server_stdout(self, text):
		result = super().parse_server_stdout(text)
		parsed = parse('<{name}> {message}', result.content)
		if parsed is None:
			parsed = parse('[{dim_name}]<{name}> {message}', result.content)
		if parsed is not None and self._verify_player_name(parsed['name']):
			result.player, result.content = parsed['name'], parsed['message']
		return result

