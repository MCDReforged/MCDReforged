"""
MCDR update things
"""
import time
from threading import Lock
from typing import Callable, Any, Union, Optional

import requests

from mcdreforged.constants import core_constant
from mcdreforged.executor.thread_executor import ThreadExecutor
from mcdreforged.minecraft.rtext import RText, RAction, RColor, RStyle, RTextBase
from mcdreforged.plugin.meta.version import Version
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import misc_util


class UpdateHelper(ThreadExecutor):
	def __init__(self, mcdr_server):
		super().__init__(mcdr_server)
		self.__api_fetcher = GithubApiFetcher(core_constant.GITHUB_API_LATEST)
		self.__update_lock = Lock()
		self.__last_query_time = 0

	def tick(self):
		if time.monotonic() - self.__last_query_time >= 60 * 60 * 24:
			self.check_update(lambda: self.mcdr_server.config['check_update'] is True, self.mcdr_server.logger.info)
		time.sleep(1)

	def check_update(self, condition_check: Callable[[], bool], reply_func: Callable[[Union[str or RTextBase]], Any]):
		self.__last_query_time = time.monotonic()
		misc_util.start_thread(self.__check_update, (condition_check, reply_func), 'CheckUpdate')

	def tr(self, key: str, *args, **kwargs) -> RTextBase:
		return RTextMCDRTranslation(key, *args, **kwargs).set_translator(self.mcdr_server.tr)

	def __check_update(self, condition_check: Callable[[], bool], reply_func: Callable[[Union[str or RTextBase]], Any]):
		if not condition_check():
			return
		acquired = self.__update_lock.acquire(blocking=False)
		if not acquired:
			reply_func(self.tr('update_helper.check_update.already_checking'))
			return
		try:
			response = None
			try:
				response = self.__api_fetcher.fetch()
				latest_version: str = response['tag_name']
				update_log: str = response['body']
			except Exception as e:
				reply_func(self.tr('update_helper.check_update.check_fail', repr(e)))
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
				except:
					self.mcdr_server.logger.exception('Fail to compare between versions "{}" and "{}"'.format(core_constant.VERSION, latest_version))
					return
				if version_current == version_fetched:
					reply_func(self.tr('update_helper.check_update.is_already_latest'))
				elif version_current > version_fetched:
					reply_func(self.tr('update_helper.check_update.newer_than_latest', core_constant.VERSION, latest_version))
				else:
					reply_func(self.tr('update_helper.check_update.new_version_detected', latest_version))
					for line in update_log.splitlines():
						reply_func('    {}'.format(line))
		finally:
			self.__update_lock.release()


class GithubApiFetcher:
	def __init__(self, url: str):
		self.url = url
		self.__etag = 'dummy'
		self.__cached_response: Optional[dict] = None

	def fetch(self) -> dict:
		response = requests.get(self.url, headers={'If-None-Match': self.__etag}, timeout=10)
		self.__etag = response.headers.get('ETag', self.__etag)
		if response.status_code != 304:  # 304 means content keeps unchanged
			if response.status_code != 200:
				raise Exception('Un-expected status code {}: {}'.format(response.status_code, response.content))
			self.__cached_response = response.json()
		return self.__cached_response
