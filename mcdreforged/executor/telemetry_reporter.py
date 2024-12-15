import collections
import functools
import json
import logging
import os
import platform
import sys
import time
import uuid
from typing import TYPE_CHECKING, Optional

from typing_extensions import override

from mcdreforged.constants import core_constant
from mcdreforged.constants.environment_variables import ENV_DISABLE_TELEMETRY
from mcdreforged.executor.background_thread_executor import BackgroundThreadExecutor
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.utils import request_utils, math_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_config import MCDReforgedConfig
	from mcdreforged.mcdr_server import MCDReforgedServer


class TelemetryReporterScheduler(BackgroundThreadExecutor):
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		super().__init__(mcdr_server.logger)
		self.__mcdr_server = mcdr_server
		self.__reporter = TelemetryReporter(mcdr_server)
		self.__report_hour_offset = self.__calc_report_hour_offset()
		self.__tr = mcdr_server.create_internal_translator('telemetry_reporter')
		self.__was_enabled_on_start = False

		mcdr_server.add_config_changed_callback(self.__on_mcdr_config_loaded)

	def __on_mcdr_config_loaded(self, _1: 'MCDReforgedConfig', _2: bool):
		if self.__was_enabled_on_start and super().should_keep_looping() and not self.__telemetry_enabled:
			# This should be a hot-reload on the config. Let's inform the user
			self.logger.info(self.__tr('disabled'))
			self.stop()

	def set_launched_from_source(self, flag: bool):
		self.__reporter.set_launched_from_source(flag)

	@classmethod
	def __calc_report_hour_offset(cls) -> float:
		# add a [2min, 10min] startup random offset
		next_ts = time.time() + math_utils.ramdom_range(120, 600)
		# we don't want to report at the edge of each hour
		# this makes sure all reports happen within [1min, 59min] of each hour
		k = next_ts % 3600 / 3600
		return math_utils.lerp(60, 3600 - 60, k)

	@property
	def __telemetry_enabled(self) -> bool:
		if ENV_DISABLE_TELEMETRY.is_true():
			return False
		if not self.__mcdr_server.config.telemetry:
			return False
		return True

	@override
	def should_keep_looping(self) -> bool:
		return super().should_keep_looping() and self.__telemetry_enabled

	@override
	def start(self):
		if self.__telemetry_enabled:
			self.logger.mdebug('Telemetry enabled, report scheduled at *:{}'.format(time.strftime('%M:%S', time.localtime(self.__report_hour_offset))), option=DebugOption.TELEMETRY)
			self.__was_enabled_on_start = True
			super().start()
		else:
			self.logger.debug('Telemetry is disabled at startup')
			self.stop()

	@override
	def tick(self):
		# report once per hour, at fixed time
		now = time.time()
		this_hour_start = now // 3600 * 3600
		this_hour_report_ts = this_hour_start + self.__report_hour_offset
		wait_sec = (this_hour_report_ts - now + 3600) % 3600
		self._wait_for_stop(wait_sec)

		if self.should_keep_looping():
			self.__reporter.report()


class TelemetryReporter:
	"""
	The class to collect and report telemetry data
	"""
	REPORT_URL = 'https://telemetry.mcdreforged.com/report'
	REPORT_TIMEOUT_SEC = 15
	SCHEMA_VERSION = 1

	def __init__(self, mcdr_server: Optional['MCDReforgedServer']):
		self.__mcdr_server = mcdr_server
		self.__logger = mcdr_server.logger if mcdr_server is not None else None
		self.__verbose_log = False

		self.__uuid = uuid.uuid4()
		self.__start_time = time.time()
		self.__launched_from_source = False

	def set_logging(self, *, verbose_log: bool = False, logger: Optional[logging.Logger] = None):
		self.__logger = logger
		self.__verbose_log = verbose_log

	def set_launched_from_source(self, flag: bool):
		self.__launched_from_source = flag

	def __log_info(self, msg: str):
		if self.__verbose_log and self.__logger:
			self.__logger.info(msg)
		else:
			self.__logger.mdebug(msg, option=DebugOption.TELEMETRY)

	def __log_error(self, msg: str):
		if self.__verbose_log and self.__logger:
			self.__logger.error(msg)
		else:
			self.__logger.mdebug(msg, option=DebugOption.TELEMETRY)

	def report(self):
		try:
			telemetry_data = self.__collect_telemetry_data()
		except Exception as e:
			self.__log_error('Failed to collect telemetry data: {}'.format(e))
			return
		self.__log_info('Telemetry data to report: {!r}'.format(telemetry_data))

		for i in range(3):
			if i > 0:
				time.sleep(1)
			try:
				rsp, rsp_buf = request_utils.post_json(self.REPORT_URL, 'TelemetryReporter', payload=telemetry_data, timeout=self.REPORT_TIMEOUT_SEC, max_size=10 * 1024)
				break
			except Exception as e:
				self.__log_error('Failed to report telemetry data, post failed (attempt {}): {}'.format(i + 1, e))
		else:
			return

		try:
			rsp.raise_for_status()
			rsp_json = json.loads(rsp_buf)
		except Exception as e:
			self.__log_error('Failed to process telemetry result, bad response: {!r}, rsp_buf[:100] {!r}'.format(str(e), rsp_buf[:100]))
			return

		self.__log_info('Telemetry report successful, rsp {}'.format(rsp_json))

	# -----------------------------------------------
	#				 Data Collectors
	# -----------------------------------------------

	def __collect_telemetry_data(self) -> dict:
		telemetry_data = {
			'schema_version': self.SCHEMA_VERSION,
			'reporter': core_constant.NAME,
			'uuid': str(self.__uuid),
			'platform': {
				'mcdr_version': core_constant.VERSION,
				'mcdr_version_pypi': core_constant.VERSION_PYPI,
				'python_version': platform.python_version(),
				'python_implementation': platform.python_implementation(),
				'system_type': platform.system(),
				'system_release': platform.release(),
				'system_architecture': platform.machine(),
			},
			'data': {
				'uptime': time.time() - self.__start_time,
				'container_environment': self.__guess_container_environment(),
				'python_package_isolation': self.__guess_python_package_isolation_method(),
				'launched_from_source': self.__launched_from_source,
				'plugin_type_counts': self.__get_plugin_type_counts(),
				'server_handler_name': self.__get_server_handler_name(),
			},
		}
		return telemetry_data

	@classmethod
	@functools.lru_cache(maxsize=None)
	def __guess_container_environment(cls) -> str:
		if os.path.isfile('/.dockerenv'):
			return 'docker'
		elif os.path.isfile('/run/.containerenv'):
			return 'podman'
		elif os.environ.get('KUBERNETES_SERVICE_HOST', '') != '' and os.environ.get('KUBERNETES_SERVICE_PORT', '') != '':
			return 'kubernetes'
		return 'none'

	@classmethod
	@functools.lru_cache(maxsize=None)
	def __guess_python_package_isolation_method(cls) -> str:
		if sys.prefix != sys.base_prefix:
			if os.path.isfile(os.path.join(sys.prefix, 'pipx_metadata.json')):
				return 'pipx'
			return 'venv'
		return 'host'

	def __get_plugin_type_counts(self) -> dict:
		if self.__mcdr_server is None:
			return {}
		from mcdreforged.plugin.type.common import PluginType
		counter = collections.Counter(plg.get_type() for plg in self.__mcdr_server.plugin_manager.get_all_plugins())
		return {pt.name: counter.get(pt, 0) for pt in PluginType}

	def __get_server_handler_name(self) -> str:
		if self.__mcdr_server is None:
			return ''
		return self.__mcdr_server.server_handler_manager.get_current_handler_name() or ''
