from mcdreforged.handler.impl.bukkit_handler import BukkitHandler
from mcdreforged.handler.impl.vanilla_handler import VanillaHandler
from mcdreforged.utils import string_util


class CatServerHandler(BukkitHandler):
	# https://github.com/Luohuayu/CatServer
	# CatServer uses vanilla logging format but spigot like player joined message
	# And has color code around the player left message

	@staticmethod
	def __cleaned_info(info):
		info.content = string_util.clean_minecraft_color_code(info.content)
		return info

	@classmethod
	def get_content_parsing_formatter(cls):
		return VanillaHandler.get_content_parsing_formatter()

	def parse_player_left(self, info):
		# §eSteve left the game§r
		return super().parse_player_left(self.__cleaned_info(info))
