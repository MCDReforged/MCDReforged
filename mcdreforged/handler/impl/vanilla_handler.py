import re

from typing_extensions import override

from mcdreforged.handler.impl.abstract_minecraft_handler import AbstractMinecraftHandler


class VanillaHandler(AbstractMinecraftHandler):
	"""
	A handler for vanilla Minecraft servers
	"""
	@classmethod
	@override
	def get_content_parsing_formatter(cls) -> re.Pattern:
		return re.compile(
			r'\[(?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+)]'
			r' \[(?P<thread>[^]]+)/(?P<logging>[^]/]+)]'
			r': (?P<content>.*)'
		)
