"""
MCDR update things
"""
import json
import time
from threading import Lock
from typing import Callable, Any, Union, Optional, TYPE_CHECKING, List

from typing_extensions import override

from mcdreforged.constants import core_constant
from mcdreforged.executor.background_thread_executor import BackgroundThreadExecutor
from mcdreforged.minecraft.rtext.style import RAction, RColor, RStyle
from mcdreforged.minecraft.rtext.text import RText, RTextBase
from mcdreforged.plugin.meta.version import Version
from mcdreforged.utils import misc_utils, request_utils
from mcdreforged.utils.types.message import MessageText

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class UpdateHelper(BackgroundThreadExecutor):
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		super().__init__(mcdr_server.logger)
		self.mcdr_server = mcdr_server
		self.__api_fetcher = GithubApiFetcher(core_constant.GITHUB_API_LATEST_URLS)
		self.__update_lock = Lock()
		self.__last_query_time = 0
		self.__tr = mcdr_server.create_internal_translator('update_helper')

	@override
	def tick(self):
		if time.monotonic() - self.__last_query_time >= 60 * 60 * 24:
			self.check_update(lambda: self.mcdr_server.config.check_update, self.mcdr_server.logger.info)
		time.sleep(1)

	def check_update(self, condition_check: Callable[[], bool], reply_func: Callable[[Union[str or RTextBase]], Any]):
		self.__last_query_time = time.monotonic()
		misc_utils.start_thread(self.__check_update, (condition_check, reply_func), 'CheckUpdate')

	def __check_update(self, condition_check: Callable[[], bool], reply_func: Callable[[MessageText], Any]):
		if not condition_check():
			return
		acquired = self.__update_lock.acquire(blocking=False)
		if not acquired:
			reply_func(self.__tr('check_update.already_checking'))
			return
		try:
			response = None
			try:
				response = self.__api_fetcher.fetch()
				latest_version: str = response['tag_name']
				update_log: str = response['body']
			except Exception as e:
				reply_func(self.__tr('check_update.check_fail', repr(e)))
				if isinstance(e, KeyError) and isinstance(response, dict) and 'message' in response:
					reply_func(response['message'])
					if 'documentation_url' in response:
						reply_func(
							RText(response['documentation_url'], color=RColor.blue, styles=RStyle.underlined).
							h(response['documentation_url']).
							c(RAction.open_url, response['documentation_url'])
						)
			else:
				try:
					version_current = Version(core_constant.VERSION, allow_wildcard=False)
					version_fetched = Version(latest_version.lstrip('vV'), allow_wildcard=False)
				except Exception:
					self.mcdr_server.logger.exception('Fail to compare between versions "{}" and "{}"'.format(core_constant.VERSION, latest_version))
					return
				if version_current == version_fetched:
					reply_func(self.__tr('check_update.is_already_latest'))
				elif version_current > version_fetched:
					reply_func(self.__tr('check_update.newer_than_latest', core_constant.VERSION, latest_version))
				else:
					reply_func(self.__tr('check_update.new_version_detected', latest_version))
					for line in update_log.splitlines():
						reply_func('    {}'.format(line))
		finally:
			self.__update_lock.release()


class GithubApiFetcher:
	def __init__(self, urls: List[str]):
		self.urls = urls.copy()
		self.__etag = 'dummy'
		self.__cached_response: Optional[dict] = None

	def fetch(self) -> Optional[dict]:
		buf = request_utils.get_buf_multi(self.urls, 'UpdateHelper', timeout=10, max_size=32 * 1024)
		return json.loads(buf)
