import collections
import queue
import time
from logging import Logger
from typing import Dict, Optional, Tuple, List, TYPE_CHECKING, Counter, Union

from pydantic import TypeAdapter, ValidationError
from ruamel.yaml import YAML, YAMLError
from typing_extensions import assert_never

from mcdreforged.handler.handler_spec import HandlerSpec, StopMethods
from mcdreforged.handler.impl import *
from mcdreforged.handler.plugin_provided_server_handler_holder import PluginProvidedServerHandlerHolder
from mcdreforged.handler.server_handler import ServerHandler
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.mcdr_config import MCDReforgedConfig, CustomHandlerEntry, CustomHandlerExtendEntry, CustomHandlerDefineEntry, CustomHandlerFileEntry
from mcdreforged.utils import class_utils, collection_utils, thread_utils, os_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer

# Attributes of the removed handler base classes that SpecServerHandler no longer calls, mapped to their replacements
_OUTDATED_HANDLER_OVERRIDES: Dict[str, str] = {
	'get_content_parsing_formatter': 'use parsing.line in the handler spec, or override parse_server_stdout',
	'get_player_message_parsing_formatter': 'use parsing.player_message in the handler spec',
	'_get_server_stdout_raw_result': 'override parse_server_stdout',
	'_content_parse': 'override parse_server_stdout',
	'format_message': 'override get_send_message_command / get_broadcast_message_command',
	'_vanilla_minecraft_player_name_regex': 'use parsing.player_name in the handler spec, or override validate_player_name',
	'_verify_player_name': 'override validate_player_name',
}


class ServerHandlerManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.logger: Logger = mcdr_server.logger
		self.handlers: Dict[str, ServerHandler] = {}
		self.__tr = mcdr_server.create_internal_translator('server_handler_manager').tr

		self.__basic_handler = BasicHandler()
		self.__plugin_provided_server_handler_holder: Optional[PluginProvidedServerHandlerHolder] = None
		self.__current_configured_handler_name: Optional[str] = None
		self.__current_configured_handler_invalid_warned: bool = False

		# Automation for lazy
		self.__handler_detector = HandlerDetector(self)

		mcdr_server.add_config_changed_callback(self.__on_mcdr_config_loaded)

	def __on_mcdr_config_loaded(self, config: MCDReforgedConfig, log: bool):
		self.register_handlers(config.custom_handlers)
		self.set_configured_handler(config.handler)
		if log:
			if (psh := self.__plugin_provided_server_handler_holder) is not None:
				self.logger.info(self.__tr('on_config_changed.handler_set_overridden', config.handler, psh.server_handler.get_name(), psh.plugin))
			else:
				self.logger.info(self.__tr('on_config_changed.handler_set', config.handler))

	def register_handlers(self, custom_handlers: Optional[List[Union[str, CustomHandlerEntry]]]):
		"""
		:raise ValueError: if a spec entry in custom_handlers is invalid. The registered handlers are not changed in this case
		"""
		handlers: Dict[str, ServerHandler] = {}

		def add_handler(hdr: ServerHandler):
			handlers[hdr.get_name()] = hdr

		add_handler(self.__basic_handler)
		add_handler(VanillaHandler())
		add_handler(BukkitHandler())
		add_handler(Bukkit14Handler())
		add_handler(ForgeHandler())
		add_handler(CatServerHandler())
		add_handler(ArclightHandler())
		add_handler(Beta18Handler())
		add_handler(BungeecordHandler())
		add_handler(WaterfallHandler())
		add_handler(VelocityHandler())
		builtin_specs: Dict[str, HandlerSpec] = {
			name: hdr.spec
			for name, hdr in handlers.items()
			if isinstance(hdr, BuiltinSpecServerHandler)
		}

		for i, entry in enumerate(custom_handlers or []):
			if isinstance(entry, str):
				class_path = entry
				try:
					handler_class = class_utils.load_class(class_path)
				except Exception:
					self.mcdr_server.logger.exception('Fail to load info handler from {!r}'.format(class_path))
				else:
					if issubclass(handler_class, ServerHandler):
						handler = handler_class()
						self.__check_outdated_overrides(handler, 'custom handler class path {!r}'.format(class_path))
						if handler.get_name() not in handlers:
							add_handler(handler)
							self.mcdr_server.logger.mdebug('Loaded info handler {} from {}'.format(handler_class.__name__, class_path), option=DebugOption.HANDLER)
						else:
							self.mcdr_server.logger.error('Handler with name {} from path {} is already registered, ignored'.format(handler.get_name(), class_path))
					else:
						self.mcdr_server.logger.error('Wrong handler class {!r}, expected {} but found {}'.format(class_path, ServerHandler, handler_class))
			else:
				location = 'custom_handlers[{}]'.format(i)
				spec = self.__load_custom_handler_spec(entry, location, builtin_specs)
				if spec.name in handlers:
					raise ValueError('{}: handler with name {!r} is already registered'.format(location, spec.name))
				add_handler(SpecServerHandler(spec))
				self.mcdr_server.logger.mdebug('Loaded spec handler {} from {}'.format(spec.name, location), option=DebugOption.HANDLER)
				if isinstance(stop := spec.control.stop, StopMethods.Signal):
					try:
						os_utils.resolve_signal(stop.signal)
					except ValueError as e:
						self.logger.warning('{}.control.stop.signal: {}, the server will be killed when stopping'.format(location, e))

		self.handlers = handlers

	@classmethod
	def __load_custom_handler_spec(cls, entry: CustomHandlerEntry, location: str, builtin_specs: Dict[str, HandlerSpec]) -> HandlerSpec:
		"""
		:raise ValueError: if the entry is invalid
		"""
		if isinstance(entry, CustomHandlerFileEntry):
			location = '{} (file {!r})'.format(location, entry.file)
			try:
				with open(entry.file, encoding='utf8') as f:
					data = YAML(typ='safe').load(f)
			except (OSError, YAMLError) as e:
				raise ValueError('{}: failed to read the handler spec file: {}'.format(location, e))
			try:
				entry = TypeAdapter(CustomHandlerEntry).validate_python(data, strict=True)
			except ValidationError as e:
				raise ValueError(cls.__format_validation_error(location, None, e))
			if isinstance(entry, CustomHandlerFileEntry):
				raise ValueError('{}: a handler spec file cannot reference another file'.format(location))

		base: Optional[HandlerSpec]
		if isinstance(entry, CustomHandlerExtendEntry):
			if (base := builtin_specs.get(entry.extends)) is None:
				raise ValueError('{}.extends: unknown builtin handler {!r}, available: {}'.format(location, entry.extends, ', '.join(builtin_specs.keys())))
			body_key, body = 'overrides', entry.overrides
		elif isinstance(entry, CustomHandlerDefineEntry):
			base = None
			body_key, body = 'spec', entry.spec
		else:
			assert_never(entry)

		if 'name' in body:
			raise ValueError('{}.{}.name: name should be set at the entry root'.format(location, body_key))
		data = {**body, 'name': entry.name}
		try:
			return base.extend(data) if base is not None else HandlerSpec.model_validate(data)
		except ValidationError as e:
			raise ValueError(cls.__format_validation_error(location, body_key, e))

	@classmethod
	def __format_validation_error(cls, location: str, body_key: Optional[str], error: ValidationError) -> str:
		lines = ['{}: invalid handler spec, {} error(s)'.format(location, error.error_count())]
		for err in error.errors():
			loc = list(err['loc'])
			if body_key is not None and loc[:1] != ['name']:
				loc.insert(0, body_key)
			path = location + ''.join('[{}]'.format(item) if isinstance(item, int) else '.{}'.format(item) for item in loc)
			lines.append('  {}: {}'.format(path, err['msg']))
		return '\n'.join(lines)

	def __check_outdated_overrides(self, handler: ServerHandler, source: str):
		if not isinstance(handler, SpecServerHandler):
			return
		handler_class = type(handler)
		for name, replacement in _OUTDATED_HANDLER_OVERRIDES.items():
			if hasattr(handler_class, name):
				self.logger.warning('Server handler {!r} ({}.{}) from {} defines {}, which MCDR no longer calls. Alternative: {}'.format(
					handler.get_name(), handler_class.__module__, handler_class.__qualname__, source, name, replacement,
				))

	@property
	def __current_configured_handler(self) -> ServerHandler:
		handler_name = self.__current_configured_handler_name
		try:
			if handler_name is None:
				raise KeyError('current handler name is not set')
			return self.handlers[handler_name]
		except KeyError:
			if not self.__current_configured_handler_invalid_warned:
				self.logger.error('Fail to load configured handler with name {}'.format(repr(handler_name)))
				self.logger.error('Fallback basic handler is used, MCDR might not works correctly')
				self.__current_configured_handler_invalid_warned = True
			return self.__basic_handler

	def set_configured_handler(self, handler_name: str):
		if handler_name != self.__current_configured_handler_name:
			self.__shutdown_handler_detection()
		self.__current_configured_handler_name = handler_name
		self.__current_configured_handler_invalid_warned = False

	def set_plugin_provided_server_handler_holder(self, psh: Optional[PluginProvidedServerHandlerHolder]):
		if psh != self.__plugin_provided_server_handler_holder:
			if psh is not None:
				self.logger.info(self.__tr('plugin_provided.set', psh.server_handler.get_name(), psh.plugin))
				self.__check_outdated_overrides(psh.server_handler, 'plugin {}'.format(psh.plugin))
			else:
				self.logger.info(self.__tr('plugin_provided.unset', self.__current_configured_handler.get_name()))
			self.__shutdown_handler_detection()
		self.__plugin_provided_server_handler_holder = psh

	def get_basic_handler(self) -> ServerHandler:
		return self.__basic_handler

	def get_plugin_provided_server_handler_holder(self) -> Optional[PluginProvidedServerHandlerHolder]:
		return self.__plugin_provided_server_handler_holder

	def get_current_handler(self) -> ServerHandler:
		if (psh := self.__plugin_provided_server_handler_holder) is not None:
			return psh.server_handler
		return self.__current_configured_handler

	def get_current_handler_name(self) -> Optional[str]:
		if (psh := self.__plugin_provided_server_handler_holder) is not None:
			return psh.server_handler.get_name()
		return self.__current_configured_handler_name

	# Automation for lazy
	def start_handler_detection(self):
		self.__handler_detector.start_handler_detection()

	def __shutdown_handler_detection(self):
		self.__handler_detector.shutdown_handler_detection()

	def detect_text(self, text: str):
		self.__handler_detector.detect_text(text)


class HandlerDetector:
	HANDLER_DETECTION_MINIMUM_SAMPLE_COUNT = 20   # At least 20 messages
	HANDLER_DETECTION_MINIMUM_SAMPLING_TIME = 60  # will do sample for 1 minute

	def __init__(self, manager: 'ServerHandlerManager'):
		self.manager = manager
		self.mcdr_server: 'MCDReforgedServer' = manager.mcdr_server
		self.running_flag = False
		self.text_queue: 'queue.Queue[Optional[str]]' = queue.Queue()
		self.text_count = 0
		self.success_count: Counter[str] = collections.Counter()
		self.__tr = self.mcdr_server.create_internal_translator('server_handler_manager').tr

	def start_handler_detection(self):
		if not self.is_detection_running():
			self.running_flag = True
			self.text_count = 0
			self.success_count.clear()
			thread_utils.start_thread(self.__detection_thread, (), 'HandlerDetector')

	def shutdown_handler_detection(self):
		# do nothing if it's called before the detection starts
		if self.is_detection_running():
			self.text_queue.put(None)

	def is_detection_running(self) -> bool:
		return self.running_flag

	def __detection_thread(self):
		start_time = time.time()
		try:
			while True:
				time_elapsed = time.time() - start_time
				if time_elapsed >= self.HANDLER_DETECTION_MINIMUM_SAMPLING_TIME and self.text_count >= self.HANDLER_DETECTION_MINIMUM_SAMPLE_COUNT:
					break
				try:
					text = self.text_queue.get(block=True, timeout=1)
				except queue.Empty:
					continue
				if text is None:  # shutdown
					self.mcdr_server.logger.debug('Handler detection has shutdown')
					return

				self.text_count += 1
				handler: ServerHandler
				for handler in collection_utils.unique_list([*self.manager.handlers.values(), self.manager.get_current_handler()]):
					if handler is not self.manager.get_basic_handler():
						try:
							handler.parse_server_stdout(handler.pre_parse_server_stdout(text))
						except Exception:
							pass
						else:
							self.success_count[handler.get_name()] += 1
		finally:
			self.running_flag = False
			while True:  # drain the queue
				try:
					self.text_queue.get(block=False)
				except queue.Empty:
					break

		most_common: List[Tuple[str, int]] = self.success_count.most_common()
		if len(most_common) == 0:
			return
		total = self.text_count
		best_count = most_common[0][1]
		best_handler_tuples = [t for t in most_common if t[1] == best_count]
		best_handler_names = [t[0] for t in best_handler_tuples]

		current_handler = self.manager.get_current_handler()
		current_handler_name = current_handler.get_name()
		current_count = self.success_count[current_handler_name]

		if current_handler_name not in best_handler_names:
			psh = self.manager.get_plugin_provided_server_handler_holder()
			if psh is not None and current_handler is psh.server_handler:
				current_handler_name += ' ({})'.format(psh.plugin)

			self.mcdr_server.logger.warning(self.__tr('handler_detection.result1'))
			self.mcdr_server.logger.warning(self.__tr('handler_detection.result2', current_handler_name, round(100.0 * current_count / total, 2), current_count, total))
			for best_handler_name, best_count in best_handler_tuples:
				self.mcdr_server.logger.warning(self.__tr('handler_detection.result3', best_handler_name, round(100.0 * best_count / total, 2), best_count, total))

	def detect_text(self, text: str):
		if self.is_detection_running():
			self.text_queue.put(text)
