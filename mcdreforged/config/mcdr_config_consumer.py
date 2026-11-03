from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from mcdreforged.config.mcdr_config import MCDReforgedConfig


_T = TypeVar('_T')


class MCDReforgedConfigConsumer(Generic[_T], ABC):
	@abstractmethod
	def validate(self, config: MCDReforgedConfig) -> _T:
		...

	@abstractmethod
	def consume(self, config: MCDReforgedConfig, validated_data: _T, log: bool):
		...
