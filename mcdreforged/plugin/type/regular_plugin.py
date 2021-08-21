import os
import sys
import time
from abc import ABC
from typing import TYPE_CHECKING, Optional, List, Tuple, Any

from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.plugin_event import MCDRPluginEvents, EventListener, PluginEvent
from mcdreforged.plugin.plugin_registry import DEFAULT_LISTENER_PRIORITY
from mcdreforged.plugin.type.plugin import AbstractPlugin, PluginState
from mcdreforged.utils.exception import IllegalCallError
from mcdreforged.utils.logger import DebugOption

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager

MODULE_TYPE = Any


class RegularPlugin(AbstractPlugin, ABC):
	def __init__(self, plugin_manager: 'PluginManager', file_path: str):
		super().__init__(plugin_manager, file_path)
		self.file_name = os.path.basename(file_path)
		self.file_modify_time = None  # type: Optional[int]
		self.__metadata = None  # type: Optional[Metadata]
		self.entry_module_instance = None  # type: MODULE_TYPE
		self.old_entry_module_instance = None  # type: MODULE_TYPE
		self.decorated_event_listeners = []  # type: List[Tuple[PluginEvent, EventListener]]

	def _reset(self):
		self.file_modify_time = self.calculate_file_modify_time()
		self.plugin_registry.clear()

	def is_regular(self) -> bool:
		return True

	def get_metadata(self) -> Metadata:
		if self.__metadata is None:
			raise IllegalCallError('Meta data of plugin {} is not loaded. Plugin state = {}'.format(repr(self), self.state))
		return self.__metadata

	def _set_metadata(self, metadata: Metadata):
		self.__metadata = metadata

	def get_fallback_metadata_id(self) -> str:
		raise NotImplementedError()

	@property
	def __class_name(self):
		return self.__class__.__name__

	def __repr__(self):
		return '{}[file={},path={},state={}]'.format(self.__class_name, self.file_name, self.plugin_path, self.state)

	# ----------------------
	#   Instance Operation
	# ----------------------

	def is_own_module(self, module_name: str) -> bool:
		raise NotImplementedError()

	def _load_entry_instance(self):
		self.old_entry_module_instance = self.entry_module_instance
		with self.plugin_manager.with_plugin_context(self):
			self.entry_module_instance = self._get_module_instance()

	# ---------------------
	#   To be Implemented
	# ---------------------

	def _get_module_instance(self):
		raise NotImplementedError()

	def _on_ready(self):
		self._register_default_listeners()

	def _on_load(self):
		self._reset()

	def _on_unload(self):
		for module_name in sys.modules.copy().keys():
			if self.is_own_module(module_name):
				rv = sys.modules.pop(module_name, None)
				self.mcdr_server.logger.debug('Removed module {} when unloading plugin {}, success = {}'.format(module_name, repr(self), rv is not None), option=DebugOption.PLUGIN)

	# --------------
	#   Life Cycle
	# --------------

	def load(self):
		self.assert_state({PluginState.UNINITIALIZED})
		self.set_state(PluginState.LOADING)
		self._on_load()
		self.mcdr_server.logger.debug('{} {} loaded from {}, file modify file = {}'.format(self.__class_name, self, self.plugin_path, self.pretty_file_modify_time), option=DebugOption.PLUGIN)
		self.set_state(PluginState.LOADED)

	def ready(self):
		"""
		Get ready, and register default things (listeners etc.)
		"""
		self.assert_state({PluginState.LOADED, PluginState.READY})
		self._on_ready()
		self.set_state(PluginState.READY)

	def reload(self):
		self.assert_state({PluginState.READY})
		self._on_unload()
		self._on_load()
		self.mcdr_server.logger.debug('{} {} reloaded, file modify file = {}'.format(self.__class_name, self, self.pretty_file_modify_time))

	def unload(self):
		self.assert_state({PluginState.LOADED, PluginState.READY})
		self._on_unload()
		self.set_state(PluginState.UNLOADING)

	def remove(self):
		self.assert_state({PluginState.UNLOADING})
		self.set_state(PluginState.UNLOADED)

	# -------------------
	#   Plugin Registry
	# -------------------

	def _register_default_listeners(self):
		for event in MCDRPluginEvents.get_event_list():
			if isinstance(event.default_method_name, str):
				func = getattr(self.entry_module_instance, event.default_method_name, None)
				if callable(func):
					self.register_event_listener(event, EventListener(self, func, DEFAULT_LISTENER_PRIORITY))
		for event, listener in self.decorated_event_listeners:
			self.register_event_listener(event, listener)
		self.decorated_event_listeners.clear()

	def register_event_listener(self, event: PluginEvent, listener: EventListener):
		# Special handling event listener registered with @event_listener decorator
		# Store and register them in method _register_default_listeners
		if self.in_states({PluginState.LOADING}):
			self.decorated_event_listeners.append((event, listener))
		else:
			super().register_event_listener(event, listener)

	# ---------------
	#   Plugin File
	# ---------------

	def plugin_exists(self):
		return os.path.isfile(self.plugin_path)

	def file_changed(self):
		return self.calculate_file_modify_time() != self.file_modify_time

	@property
	def pretty_file_modify_time(self) -> Optional[str]:
		if self.file_modify_time is not None:
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.file_modify_time / 1e9))
		else:
			return None

	def calculate_file_modify_time(self):
		if self.plugin_exists():
			try:
				return os.stat(self.plugin_path).st_mtime_ns
			except:
				pass
		return None
