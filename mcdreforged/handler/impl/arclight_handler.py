from mcdreforged.handler.impl.bukkit_handler import BukkitHandler


class ArclightHandler(BukkitHandler):
	"""
	A handler for `Arclight <https://github.com/IzzelAliz/Arclight>`__ servers
	"""

	# [13:22:36 INFO]: Successfully initialized permission handler forge:default_handler
	# [13:22:36 INFO] [Arclight]: Forwarding forge permission[forge:default_handler] to bukkit
	# [13:26:10 INFO]: Fallen_Breath joined the game
	# [13:26:18 INFO]: [Not Secure] <Fallen_Breath> hello
	# [13:26:28 INFO]: Fallen_Breath lost connection: Disconnected
	@classmethod
	def get_content_parsing_formatter(cls):
		return (
			super().get_content_parsing_formatter(),
			'[{hour:d}:{min:d}:{sec:d} {logging}] [{dummy}]: {content}'
		)

