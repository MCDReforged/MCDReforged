
import hashlib
import os
import re
import sys
from threading import RLock
from typing import TYPE_CHECKING

from mcdreforged import constant
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.plugin import AbstractPlugin, PluginState
from mcdreforged.plugin.plugin_event import MCDRPluginEvents, EventListener
from mcdreforged.plugin.plugin_registry import DEFAULT_LISTENER_PRIORITY
from mcdreforged.utils import misc_util, string_util
from mcdreforged.utils.exception import IllegalCallError
from mcdreforged.utils.logger import DebugOption

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager

GLOBAL_LOAD_LOCK = RLock()


class RegularPlugin(AbstractPlugin):
	def __init__(self, plugin_manager: 'PluginManager', file_path: str):
		super().__init__(plugin_manager, file_path)
		self.file_name = os.path.basename(file_path)
		self.file_hash = None
		self.module_instance = None
		self.old_module_instance = None
		self.newly_loaded_module = []
		# noinspection PyTypeChecker
		self.__metadata = None  # type: Metadata

	def is_regular(self) -> bool:
		return True

	def get_metadata(self) -> Metadata:
		if self.__metadata is None:
			raise IllegalCallError('Meta data of plugin {} is not loaded. Plugin state = {}'.format(repr(self), self.state))
		return self.__metadata

	def get_fallback_metadata_id(self) -> str:
		file_name = string_util.remove_suffix(self.file_name, constant.PLUGIN_FILE_SUFFIX)
		return re.sub(r'[^a-z0-9]', '_', file_name.lower())

	def __repr__(self):
		return 'RegularPlugin[file={},path={},state={}]'.format(self.file_name, self.file_path, self.state)

	def __register_default_listeners(self):
		for event in MCDRPluginEvents.get_event_list():
			if isinstance(event.default_method_name, str):
				func = getattr(self.module_instance, event.default_method_name, None)
				if callable(func):
					self.register_event_listener(event, EventListener(self, func, DEFAULT_LISTENER_PRIORITY))

	# --------------
	#   Life Cycle
	# --------------

	def __load_instance(self):
		self.file_hash = self.get_file_hash()
		with GLOBAL_LOAD_LOCK:
			previous_modules = sys.modules.copy()
			self.old_module_instance = self.module_instance
			try:
				self.module_instance = misc_util.load_source(self.file_path)
			finally:
				self.newly_loaded_module = [module for module in sys.modules if module not in previous_modules]
				self.mcdr_server.logger.debug('Newly loaded modules of {}: {}'.format(self, self.newly_loaded_module), option=DebugOption.PLUGIN)
		self.__metadata = Metadata(self, getattr(self.module_instance, 'PLUGIN_METADATA', None))
		self.plugin_registry.clear()

	def __unload_instance(self):
		with GLOBAL_LOAD_LOCK:
			for module in self.newly_loaded_module:
				try:
					sys.modules.pop(module)
				except KeyError:
					self.mcdr_server.logger.critical('Module {} not found when unloading plugin {}'.format(module, repr(self)))
				else:
					self.mcdr_server.logger.debug('Removed module {} when unloading plugin {}'.format(module, repr(self)), option=DebugOption.PLUGIN)
			self.newly_loaded_module.clear()

	def load(self):
		self.assert_state({PluginState.UNINITIALIZED})
		self.__load_instance()
		self.mcdr_server.logger.debug('Plugin {} loaded from {}, file sha256 = {}'.format(self, self.file_path, self.file_hash), option=DebugOption.PLUGIN)
		self.set_state(PluginState.LOADED)

	def ready(self):
		"""
		Get ready, and register default things (listeners etc.)
		"""
		self.assert_state({PluginState.LOADED, PluginState.READY})
		self.__register_default_listeners()
		self.set_state(PluginState.READY)

	def reload(self):
		self.assert_state({PluginState.READY})
		self.__unload_instance()
		self.__load_instance()
		self.mcdr_server.logger.debug('RegularPlugin {} reloaded, file sha256 = {}'.format(self, self.file_hash))

	def unload(self):
		self.assert_state({PluginState.LOADED, PluginState.READY})
		self.__unload_instance()
		self.set_state(PluginState.UNLOADING)

	def remove(self):
		self.assert_state({PluginState.UNLOADING})
		self.set_state(PluginState.UNLOADED)

	# ---------------
	#   Plugin File
	# ---------------

	def file_exists(self):
		return os.path.isfile(self.file_path)

	def file_changed(self):
		return self.get_file_hash() != self.file_hash

	def get_file_hash(self):
		if self.file_exists():
			with open(self.file_path, 'rb') as file:
				return hashlib.sha256(file.read()).hexdigest()
		else:
			return None
