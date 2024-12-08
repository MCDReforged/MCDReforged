import dataclasses
import os


@dataclasses.dataclass(frozen=True)
class EnvironmentVariable:
	name: str

	def get_value(self) -> str:
		return os.environ.get(self.name, '')

	def has_value(self) -> bool:
		return self.get_value() != ''

	def is_true(self) -> bool:
		return self.get_value().lower() in ['true', '1']  # fuzzy match

	def is_not_true(self) -> bool:
		return not self.is_true()

	def is_false(self) -> bool:
		return self.get_value().lower() in ['false', '0']  # fuzzy match

	def is_not_false(self) -> bool:
		return not self.is_false()


ENV_DISABLE_TELEMETRY = EnvironmentVariable(name='MCDREFORGED_TELEMETRY_DISABLED')
