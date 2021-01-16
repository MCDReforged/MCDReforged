from mcdreforged.handler.impl.bukkit_handler import BukkitHandler
from mcdreforged.handler.impl.vanilla_handler import VanillaHandler


class Bukkit14Handler(BukkitHandler):
	# 1.14.4+ bukkit / spigot change it's console logger into vanilla like format
	# idk why they did this
	# paper is not included

	@classmethod
	def get_content_parsing_formatter(cls):
		return VanillaHandler.get_content_parsing_formatter()
