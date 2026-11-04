import threading
from logging import Logger
from typing import Any, Tuple, Dict, Union, List, TypeVar, Callable

from mcdreforged.config.mcdr_config import MCDReforgedConfig
from mcdreforged.config.mcdr_config_consumer import MCDReforgedConfigConsumer
from mcdreforged.constants.environment_variables import ENV_DISABLE_TELEMETRY

_T = TypeVar('_T')


class MCDReforgedConfigManager:
	DEFAULT_CONFIG_RESOURCE_PATH = 'resources/default_config.yml'

	def __init__(self, logger: Logger, config_file_path: str):
		from mcdreforged.utils.yaml_data_storage import YamlDataStorage
		self.logger = logger
		self.__storage = YamlDataStorage(logger, config_file_path, self.DEFAULT_CONFIG_RESOURCE_PATH)
		self.__config = MCDReforgedConfig()
		self.__config_change_lock = threading.Lock()
		self.__consumers: List[MCDReforgedConfigConsumer[Any]] = []

	def get_config(self) -> MCDReforgedConfig:
		return self.__config

	def add_config_consumer(self, consumer: MCDReforgedConfigConsumer[_T]):
		self.__consumers.append(consumer)

	def add_config_changed_callback(self, callback: Callable[[MCDReforgedConfig, bool], Any]):
		class Consumer(MCDReforgedConfigConsumer[None]):
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
			data = self.__config.model_dump()
			for keys, value in changes.items():
				if isinstance(keys, str):
					keys = tuple(keys.split('.'))
				assert len(keys) > 0
				obj = data
				for i, key in enumerate(keys):
					if key.startswith('_'):
						raise ValueError('Bad key to modify: {!r} at index {}'.format(key, i))
					if not isinstance(obj, dict) or key not in obj:
						raise KeyError('Unknown config key: {!r} at index {}'.format(key, i))
					if i < len(keys) - 1:
						obj = obj[key]
					else:
						obj[key] = value
			config = MCDReforgedConfig.model_validate(data, strict=True)
			self.__on_config_changed(config, log)
