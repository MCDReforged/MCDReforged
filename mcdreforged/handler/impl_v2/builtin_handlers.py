from abc import ABC

from mcdreforged.handler.handler_spec import HandlerSpec
from mcdreforged.handler.impl_v2.spec_server_handler import SpecServerHandler
from mcdreforged.utils import resources_utils


class BuiltinSpecServerHandler(SpecServerHandler, ABC):
	"""
	A spec server handler whose spec is loaded from a resource file of MCDR
	"""

	def __init__(self, resource_path: str):
		spec = HandlerSpec.model_validate(resources_utils.get_yaml(resource_path))
		super().__init__(spec)


class VanillaHandler(BuiltinSpecServerHandler):
	"""
	A handler for vanilla Minecraft servers
	"""

	def __init__(self):
		super().__init__('resources/handler/vanilla_handler.yml')


class Beta18Handler(BuiltinSpecServerHandler):
	"""
	Yes, a handler for Minecraft beta 1.8
	"""

	def __init__(self):
		super().__init__('resources/handler/beta18_handler.yml')


class ForgeHandler(BuiltinSpecServerHandler):
	"""
	A handler for `Forge <https://files.minecraftforge.net>`__ Minecraft servers
	"""

	def __init__(self):
		super().__init__('resources/handler/forge_handler.yml')


class BukkitHandler(BuiltinSpecServerHandler):
	"""
	A handler for `bukkit <https://www.spigotmc.org/wiki/buildtools>`__
	and bukkit-like (e.g. `Paper <https://github.com/PaperMC/Paper>`__) Minecraft servers
	"""

	def __init__(self):
		super().__init__('resources/handler/bukkit_handler.yml')


class Bukkit14Handler(BuiltinSpecServerHandler):
	"""
	A handler for `bukkit and spigot <https://www.spigotmc.org/wiki/buildtools>`__ Minecraft servers in 1.14+
	"""

	def __init__(self):
		super().__init__('resources/handler/bukkit14_handler.yml')


class CatServerHandler(BuiltinSpecServerHandler):
	"""
	A handler for `CatServer <https://github.com/Luohuayu/CatServer>`__ Minecraft servers
	"""

	def __init__(self):
		super().__init__('resources/handler/cat_server_handler.yml')


class ArclightHandler(BuiltinSpecServerHandler):
	"""
	A handler for `Arclight <https://github.com/IzzelAliz/Arclight>`__ servers
	"""

	def __init__(self):
		super().__init__('resources/handler/arclight_handler.yml')


class BungeecordHandler(BuiltinSpecServerHandler):
	"""
	A handler for `Bungeecord <https://github.com/SpigotMC/BungeeCord>`__ servers
	"""

	def __init__(self):
		super().__init__('resources/handler/bungeecord_handler.yml')


class WaterfallHandler(BuiltinSpecServerHandler):
	"""
	A handler for `Waterfall <https://github.com/PaperMC/Waterfall>`__ servers
	"""

	def __init__(self):
		super().__init__('resources/handler/waterfall_handler.yml')


class VelocityHandler(BuiltinSpecServerHandler):
	"""
	A handler for `Velocity <https://velocitypowered.com>`__ servers
	"""

	def __init__(self):
		super().__init__('resources/handler/velocity_handler.yml')
