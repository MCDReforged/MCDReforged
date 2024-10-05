import logging
import os
from typing import Callable, TYPE_CHECKING, Union, Optional, IO, Type, TypeVar
from typing import Literal as TLiteral

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource, PluginCommandSource
from mcdreforged.constants import plugin_constant
from mcdreforged.info_reactor.info_filter import InfoFilter
from mcdreforged.logging.logger import MCDReforgedLogger
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.plugin_event import EventListener, LiteralEvent, PluginEvent
from mcdreforged.plugin.plugin_registry import DEFAULT_LISTENER_PRIORITY, HelpMessage
from mcdreforged.plugin.si._simple_config_handler import FileFormat, SimpleConfigHandler
from mcdreforged.plugin.si.server_interface import ServerInterface
from mcdreforged.plugin.type.multi_file_plugin import MultiFilePlugin
from mcdreforged.plugin.type.plugin import AbstractPlugin
from mcdreforged.utils import class_utils
from mcdreforged.utils.serializer import Serializable
from mcdreforged.utils.types.message import MessageText, TranslationKeyDictRich, TranslationKeyDictNested

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.handler.server_handler import ServerHandler


SerializableType = TypeVar('SerializableType', bound=Serializable)


class PluginServerInterface(ServerInterface):
	"""
	Derived from :class:`~mcdreforged.plugin.si.server_interface.ServerInterface`,
	:class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface` adds the ability
	for plugins to control the plugin itself on the basis of :class:`~mcdreforged.plugin.si.server_interface.ServerInterface`
	"""

	def __init__(self, mcdr_server: 'MCDReforgedServer', plugin: AbstractPlugin):
		super().__init__(mcdr_server)
		self.__plugin = plugin
		self.__logger_for_plugin: Optional[MCDReforgedLogger] = None

	@property
	def logger(self) -> logging.Logger:
		if self.__logger_for_plugin is None:
			try:
				logger = self.__logger_for_plugin = self._create_plugin_logger(self.__plugin.get_id())
			except Exception:
				logger = self._mcdr_server.logger
			self.__logger_for_plugin = logger
		return self.__logger_for_plugin

	def as_plugin_server_interface(self) -> Optional['PluginServerInterface']:
		return self

	# -----------------------
	#   Overwritten methods
	# -----------------------

	def get_plugin_command_source(self) -> PluginCommandSource:
		return PluginCommandSource(self, self.__plugin)

	# ------------------------
	#     Plugin Registry
	# ------------------------

	def register_event_listener(self, event: Union[PluginEvent, str], callback: Callable, priority: Optional[int] = None) -> None:
		"""
		Register an event listener for the current plugin

		:param event: The id of the event, or a :class:`~mcdreforged.plugin.plugin_event.PluginEvent` instance.
			It indicates the target event for the plugin to listen
		:param callback: The callback listener method for the event
		:param priority: The priority of the listener. It will be set to the default value ``1000`` if it's not specified
		"""
		if priority is None:
			priority = DEFAULT_LISTENER_PRIORITY
		if isinstance(event, str):
			event = LiteralEvent(event_id=event)
		self.__plugin.register_event_listener(event, EventListener(self.__plugin, callback, priority))

	def register_command(self, root_node: Literal, *, allow_duplicates: bool = False) -> None:
		"""
		Register a command for the current plugin

		:param root_node: the root node of your command tree. It should be a :class:`~mcdreforged.command.builder.nodes.basic.Literal` node
		:keyword allow_duplicates: If set to False (default), a warning will be printed if duplicated command root node is found.
			If set to True, the warning will be suppressed as what it behaves before

		.. versionadded:: v2.13.0
			The *allow_duplicates* parameter
		"""
		self.__plugin.register_command(root_node, allow_duplicates=allow_duplicates)

	def register_help_message(self, prefix: str, message: Union[MessageText, TranslationKeyDictRich], permission: int = PermissionLevel.MINIMUM_LEVEL) -> None:
		"""
		Register a help message for the current plugin, which is used in ``!!help`` command

		:param prefix: The help command of your plugin. When player click on the displayed message it will suggest this
			prefix parameter to the player. It's recommend to set it to the entry command of your plugin
		:param message: A neat command description. It can be a str or a :class:`RText <mcdreforged.minecraft.rtext.text.RTextBase>`
			Also, it can be a dict maps from language to description message
		:param permission: The minimum permission level for the user to see this help message.
			With default permission, anyone can see this message
		"""
		self.__plugin.register_help_message(HelpMessage(self.__plugin, prefix, message, permission))

	def register_translation(self, language: str, mapping: TranslationKeyDictNested) -> None:
		"""
		Register a translation mapping for a specific language for the current plugin

		:param language: The language of this translation
		:param mapping: A dict which maps translation keys into translated text.
			The translation key could be expressed as node name which under root node or the path of a nested multi-level nodes
		"""
		self.__plugin.register_translation(language, mapping)

	def register_server_handler(self, server_handler: 'ServerHandler'):
		"""
		Register a plugin-provided server handler

		The server handler will override the configured server handler of MCDR, within the lifecycle of the current plugin

		If multiple plugins provide multiple server handler, only the first one will be used, and warning messages will be logged

		:param server_handler: The server handler to register

		.. versionadded:: v2.13.0
		"""
		from mcdreforged.handler.server_handler import ServerHandler
		class_utils.check_type(server_handler, ServerHandler)
		self.__plugin.register_server_handler(server_handler)

	def register_info_filter(self, info_filter: InfoFilter):
		"""
		Register a plugin-provided info filter. See :class:`~mcdreforged.info_reactor.info_filter.InfoFilter` for more information

		The info filter take effects within the lifecycle of the current plugin

		.. warning::

			The info filter callbacks will be invoked in the MCDR main thread, not the task executor thread

			Make sure your function is well optimized, or it might lag MCDR, and also be aware of multithreading race condition

		:param info_filter: The info filter to register

		.. versionadded:: v2.13.0
		"""
		class_utils.check_type(info_filter, InfoFilter)
		self.__plugin.register_info_filter(info_filter)

	# ------------------------
	#      Plugin Utils
	# ------------------------

	def get_self_metadata(self) -> Metadata:
		"""
		Return the metadata of the plugin itself
		"""
		return self.__plugin.get_metadata()

	def get_data_folder(self) -> str:
		"""
		Return a unified data directory path for the current plugin

		The path of the folder will be ``"config/plugin_id"/`` where ``plugin_id`` is the id of the current plugin
		if the directory does not exist, create it

		Example::

			with open(os.path.join(server.get_data_folder(), 'my_data.txt'), 'w') as file_handler:
				write_some_data(file_handler)

		:return: The path to the data directory
		"""
		plugin_data_folder = os.path.join(plugin_constant.PLUGIN_CONFIG_DIRECTORY, self.__plugin.get_id())
		if not os.path.isdir(plugin_data_folder):
			os.makedirs(plugin_data_folder)
		return plugin_data_folder

	def open_bundled_file(self, relative_file_path: str) -> IO[bytes]:
		"""
		Open a file inside the plugin with readonly binary mode

		Example::

			with server.open_bundled_file('message.txt') as file_handler:
				message = file_handler.read().decode('utf8')
			server.logger.info('A message from the file: {}'.format(message))

		:param relative_file_path: The related file path in your plugin to the file you want to open
		:return: A un-decoded bytes file-like object
		:raise FileNotFoundError: if the plugin is not a packed plugin (that is, a solo plugin)
		"""
		if not isinstance(self.__plugin, MultiFilePlugin):
			raise FileNotFoundError('Only packed plugin supported this API, found plugin type: {}'.format(self.__plugin.__class__))
		return self.__plugin.open_file(relative_file_path)

	def load_config_simple(
			self, file_name: Optional[str] = None, default_config: Optional = None, *,
			in_data_folder: bool = True,
			echo_in_console: bool = True,
			source_to_reply: Optional[CommandSource] = None,
			target_class: Optional[Type[SerializableType]] = None,
			encoding: str = 'utf8',
			file_format: Optional[FileFormat] = None,
			failure_policy: TLiteral['regen', 'raise'] = 'regen',
			data_processor: Optional[Callable[[dict], bool]] = None,
	) -> Union[dict, SerializableType]:
		"""
		A simple method to load a dict or :class:`~mcdreforged.utils.serializer.Serializable` type config from a json file

		Default config is supported. Missing key-values in the loaded config object will be filled using the default config
		
		Example 1::

			config = {
				'settingA': 1
				'settingB': 'xyz'
			}
			default_config = config.copy()

			def on_load(server: PluginServerInterface, prev_module):
				global config
				config = server.load_config_simple('my_config.json', default_config)

		Example 2::

			class Config(Serializable):
				settingA: int = 1
				settingB: str = 'xyz'

			config: Config

			def on_load(server: PluginServerInterface, prev_module):
				global config
				config = server.load_config_simple(target_class=Config)
			
		Assuming that the plugin id is ``my_plugin``, then the config file will be in ``"config/my_plugin/my_config.json"``

		:param file_name: The name of the config file. It can also be a path to the config file
		:param default_config: A dict contains the default config. It's required when the config file is missing,
			or exception will be risen. If *target_class* is given and *default_config* is missing, the default values in *target_class*
			will be used when the config file is missing
		:keyword in_data_folder: If True, the parent directory of file operating is the :meth:`data folder <get_data_folder>` of the plugin
		:keyword echo_in_console: If logging messages in console about config loading
		:keyword source_to_reply: The command source for replying logging messages
		:keyword target_class: A class derived from :class:`~mcdreforged.utils.serializer.Serializable`.
			When specified the loaded config data will be deserialized
			to an instance of *target_class* which will be returned as return value
		:keyword encoding: The encoding method to read the config file. Default ``"utf8"``
		:keyword file_format: The syntax format of the config file. Default: ``None``, which means that
			MCDR will try to detect the format from the name of the config file
		:keyword failure_policy: The policy of handling a config loading error.
			``"regen"`` (default): try to re-generate the config; ``"raise"``: directly raise the exception
		:keyword data_processor: A callback function that processes the data read from the config file.
			It should accept one argument and return a bool. The argument is the parsed config file, normally a dict-like object.
			The return value indicates if the file saving operation should be performed after the config loading
			Example usage: config data migration
		:return: A dict contains the loaded and processed config

		.. versionadded:: v2.2.0
			The *encoding* parameter
		.. versionadded:: v2.12.0
			The *failure_policy* and *file_format* parameter
		.. versionadded:: v2.13.0
			The *data_processor* parameter
		"""
		config_handler = SimpleConfigHandler(file_name, file_format, self.get_data_folder() if in_data_folder else '.')

		def log(msg: MessageText):
			if isinstance(source_to_reply, CommandSource):
				source_to_reply.reply(msg)
			# don't do double-echo if the source is a console command source
			if echo_in_console and not (source_to_reply is not None and source_to_reply.is_console):
				self.logger.info(msg)

		read_data = None
		needs_save = False
		try:
			read_data = config_handler.load(encoding=encoding)
		except Exception as e:
			# non file-read error, raise it
			if failure_policy == 'raise' and not isinstance(e, OSError):
				raise

			# no default config and cannot read config file, raise the error
			if default_config is None and target_class is None:
				raise

			needs_save = True
			log(self._tr('load_config_simple.failed', e))
		else:
			if data_processor is not None:
				needs_save |= data_processor(read_data)

		if target_class is not None:
			def set_imperfect(*_):
				nonlocal imperfect
				imperfect = True
			imperfect = False
			try:
				if read_data is None:  # read failed, use default
					result_config = target_class.get_default()
				else:
					result_config = target_class.deserialize(read_data, missing_callback=set_imperfect, redundancy_callback=set_imperfect)
			except Exception as e:
				if failure_policy == 'raise':
					raise
				result_config = target_class.get_default()
				needs_save = True
				log(self._tr('load_config_simple.failed', e))
			else:
				if imperfect:
					needs_save = True
		else:
			if read_data is None:  # read failed, use default
				result_config = default_config.copy()
			else:
				result_config = read_data
				if default_config is not None:
					# Notes: support level-1 nesting only
					# constructing the result config based on the given default config
					for key, value in default_config.items():
						if key not in read_data:
							result_config[key] = value
							log(self._tr('load_config_simple.key_missed', key, value))
							needs_save = True

				# remove unexpected keys
				for key in list(result_config.keys()):
					if key not in default_config:
						result_config.pop(key)

		log(self._tr('load_config_simple.succeed'))
		if needs_save:
			self.save_config_simple(result_config, file_name=file_name, file_format=file_format, in_data_folder=in_data_folder)
		return result_config

	def save_config_simple(
			self, config: Union[dict, Serializable], file_name: str = 'config.json', *,
			in_data_folder: bool = True,
			encoding: str = 'utf8',
			file_format: Optional[FileFormat] = None,
	) -> None:
		"""
		A simple method to save your dict or :class:`~mcdreforged.utils.serializer.Serializable` type config as a json file

		:param config: The config instance to be saved
		:param file_name: The name of the config file. It can also be a path to the config file
		:keyword in_data_folder: If True, the parent directory of file operating is the :meth:`data folder <get_data_folder>` of the plugin
		:keyword encoding: The encoding method to write the config file. Default ``"utf8"``
		:keyword file_format: The syntax format of the config file. Default: ``None``, which means that
			MCDR will try to detect the format from the name of the config file

		.. versionadded:: v2.2.0
			The *encoding* parameter
		.. versionadded:: v2.12.0
			The *file_format* parameter
		"""
		if isinstance(config, Serializable):
			data = config.serialize()
		else:
			data = config

		config_handler = SimpleConfigHandler(file_name, file_format, self.get_data_folder() if in_data_folder else '.')
		config_handler.save(data, encoding=encoding)
