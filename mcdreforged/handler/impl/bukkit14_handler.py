from mcdreforged.handler.impl.bukkit_handler import BukkitHandler
from mcdreforged.handler.impl.vanilla_handler import VanillaHandler


class Bukkit14Handler(BukkitHandler):
	"""
	A handler for `bukkit and spigot <https://www.spigotmc.org/wiki/buildtools>`__ Minecraft servers in 1.14+
	"""
	# 1.14.4+ bukkit / spigot change its console logger into vanilla like format
	# idk why they did this
	# paper is not included

	@classmethod
	def get_content_parsing_formatter(cls):
		return VanillaHandler.get_content_parsing_formatter()
