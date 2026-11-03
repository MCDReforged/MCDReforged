"""
MCDR config file stuffs
"""
import threading
from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Tuple, Dict, Union, Optional, List, TypeVar, Annotated, Generic, Callable

from pydantic import BaseModel, Field, ConfigDict, Tag

from mcdreforged.constants import core_constant
from mcdreforged.constants.environment_variables import ENV_DISABLE_TELEMETRY
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.utils.pydantic_utils import key_discriminator

CONFIG_SCHEMA_VERSION = 1


class RconConfig(BaseModel):
	enable: bool = False
	address: Optional[str] = '127.0.0.1'
	port: Optional[int] = 25575
	password: Optional[str] = 'password'


class CustomHandlerExtendEntry(BaseModel):
	model_config = ConfigDict(extra='forbid')
	name: str
	extends: str
	overrides: Dict[str, Any]


class CustomHandlerDefineEntry(BaseModel):
	model_config = ConfigDict(extra='forbid')
	name: str
	spec: Dict[str, Any]


class CustomHandlerFileEntry(BaseModel):
	model_config = ConfigDict(extra='forbid')
	file: str


CustomHandlerEntry = Annotated[
	Annotated[CustomHandlerExtendEntry, Tag('extend')] | Annotated[CustomHandlerDefineEntry, Tag('define')] | Annotated[CustomHandlerFileEntry, Tag('file')],
	key_discriminator({'extends': 'extend', 'spec': 'define', 'file': 'file'}),
]


class MCDReforgedConfig(BaseModel):
	model_config = ConfigDict(
		json_schema_extra={
			'$id': f'https://json.schemastore.org/mcdreforged-config.json',
			'$schema': 'http://json-schema.org/draft-07/schema#'
		},
	)

	# --------- Basic Configuration ---------
	language: str = core_constant.DEFAULT_LANGUAGE

	# --------- Server Configuration ---------
	working_directory: str = 'server'
	start_command: Union[str, List[str]] = 'echo Hello world from MCDReforged'
	handler: str = 'vanilla_handler'
	encoding: Optional[str] = 'utf8'
	decoding: Optional[Union[str, List[str]]] = 'utf8'
	environment: Optional[Union[List[str], Dict[str, str]]] = None
	environment_inherit: bool = True
	rcon: RconConfig = Field(default_factory=RconConfig)

	# --------- Plugin Configuration ---------
	plugin_directories: List[str] = Field(default_factory=lambda: ['plugins'])
	catalogue_meta_cache_ttl: int = 20 * 60  # 20min
	catalogue_meta_fetch_timeout: float = 15
	catalogue_meta_url: Optional[str] = None
	plugin_download_url: Optional[str] = None
	plugin_download_timeout: float = 15
	plugin_pip_install_extra_args: Optional[str] = None

	# --------- Misc Configuration ---------
	check_update: bool = True
	advanced_console: bool = True
	http_proxy: Optional[str] = None
	https_proxy: Optional[str] = None
	telemetry: bool = ENV_DISABLE_TELEMETRY.is_not_true()

	# --------- Advanced Configuration ---------
	disable_console_thread: bool = False
	disable_console_color: bool = False
	custom_handlers: Optional[List[Union[str, CustomHandlerEntry]]] = None
	custom_info_reactors: Optional[List[str]] = None
	watchdog_threshold: int = 10
	handler_detection: bool = True

	# --------- Debug Configuration ---------
	debug: Dict[str, bool] = Field(default_factory=lambda: {str(o.name).lower(): False for o in DebugOption})
	write_server_output_to_log_file: bool = False

	def is_debug_on(self) -> bool:
		return any(self.debug.values())


_T = TypeVar('_T')


class ConfigConsumer(Generic[_T], ABC):
	@abstractmethod
	def validate(self, config: MCDReforgedConfig) -> _T:
		...

	@abstractmethod
	def consume(self, config: MCDReforgedConfig, validated_data: _T, log: bool):
		...


class MCDReforgedConfigManager:
	DEFAULT_CONFIG_RESOURCE_PATH = 'resources/default_config.yml'

	def __init__(self, logger: Logger, config_file_path: str):
		from mcdreforged.utils.yaml_data_storage import YamlDataStorage
		self.logger = logger
		self.__storage = YamlDataStorage(logger, config_file_path, self.DEFAULT_CONFIG_RESOURCE_PATH)
		self.__config = MCDReforgedConfig()
		self.__config_change_lock = threading.Lock()
		self.__consumers: List[ConfigConsumer[Any]] = []

	def get_config(self) -> MCDReforgedConfig:
		return self.__config

	def add_config_consumer(self, consumer: ConfigConsumer[_T]):
		self.__consumers.append(consumer)

	def add_config_changed_callback(self, callback: Callable[[MCDReforgedConfig, bool], Any]):
		class Consumer(ConfigConsumer[None]):
			def validate(self, config: MCDReforgedConfig) -> None:
				pass

			def consume(self, config: MCDReforgedConfig, validated_data: None, log: bool):
				callback(config, log)

		self.add_config_consumer(Consumer())

	def __on_config_changed(self, config: MCDReforgedConfig, log: bool):
		validated = [(consumer, consumer.validate(config)) for consumer in self.__consumers]
		self.__config = config
		for consumer, validated_data in validated:
			consumer.consume(config, validated_data, log)

	def load(self, allowed_missing_file: bool, *, log: bool = True) -> bool:
		with self.__config_change_lock:
			config, has_missing = self.__read_config(allowed_missing_file)
			self.__on_config_changed(config, log)
			if has_missing:
				self.save()
			return has_missing

	def __read_config(self, allowed_missing_file: bool) -> Tuple[MCDReforgedConfig, bool]:
		has_missing = self.__storage.read_config(allowed_missing_file, save_on_missing=False)
		data = self.__storage.to_dict()
		try:
			config = MCDReforgedConfig.model_validate(data, strict=True)
		except (KeyError, ValueError, TypeError) as e:
			raise ValueError('config deserialization failed: {}'.format(e))
		return config, has_missing

	def save(self):
		data = self.__config.model_dump()
		self.__storage.merge_from_dict(data)
		self.__storage.save()

	def save_default(self):
		typ = TypeVar('typ', bound=dict)

		def config_processor(config: typ) -> typ:
			if ENV_DISABLE_TELEMETRY.is_true():
				config['telemetry'] = False
			return config

		self.__storage.save_default(config_processor)

	def file_presents(self) -> bool:
		return self.__storage.file_presents()

	def set_values(self, changes: Dict[Union[Tuple[str, ...], str], Any], *, log: bool = False):
		"""
		Example keys: 'path.to.value', ('path', 'to', 'value')
		:param changes: change map
		"""
		with self.__config_change_lock:
			config = self.__config.model_copy(deep=True)
			for keys, value in changes.items():
				if isinstance(keys, str):
					keys = tuple(keys.split('.'))
				assert len(keys) > 0
				obj = config
				for i, key in enumerate(keys):
					if key.startswith('_'):
						raise ValueError('Bad key to modify: {!r} at index {}'.format(key, i))
					if not hasattr(obj, key):
						raise KeyError('Unknown config key: {!r} at index {}'.format(key, i))
					if i < len(keys) - 1:
						obj = getattr(obj, key)
					else:
						setattr(obj, key, value)
			self.__on_config_changed(config, log)
