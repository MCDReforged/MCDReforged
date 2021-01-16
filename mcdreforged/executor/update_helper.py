"""
MCDR update things
"""
import time
from threading import Lock
from typing import Callable, Any, Union

import requests

from mcdreforged import constant
from mcdreforged.executor.thread_executor import ThreadExecutor
from mcdreforged.minecraft.rtext import RText, RAction, RColor, RStyle, RTextBase
from mcdreforged.utils import misc_util


class UpdateHelper(ThreadExecutor):
	def __init__(self, mcdr_server):
		super().__init__(mcdr_server)
		self.update_lock = Lock()
		self.__last_query_time = 0

	def tick(self):
		if time.time() - self.__last_query_time >= 60 * 60 * 24:
			self.check_update(lambda: self.mcdr_server.config['check_update'] is True, self.mcdr_server.logger.info)
		time.sleep(1)

	def check_update(self, condition_check: Callable[[], bool], reply_func: Callable[[Union[str or RTextBase]], Any]):
		self.__last_query_time = time.time()
		misc_util.start_thread(self.__check_update, (condition_check, reply_func), 'CheckUpdate')

	def __check_update(self, condition_check: Callable[[], bool], reply_func: Callable[[Union[str or RTextBase]], Any]):
		if not condition_check():
			return
		acquired = self.update_lock.acquire(blocking=False)
		if not acquired:
			reply_func(self.mcdr_server.tr('update_helper.check_update.already_checking'))
			return
		try:
			response = None
			try:
				response = requests.get(constant.GITHUB_API_LATEST, timeout=5).json()
				latest_version = response['tag_name']  # type: str
				update_log = response['body']
			except Exception as e:
				reply_func(self.mcdr_server.tr('update_helper.check_update.check_fail', repr(e)))
				if isinstance(e, KeyError) and type(response) is dict and 'message' in response:
					reply_func(response['message'])
					if 'documentation_url' in response:
						reply_func(
							RText(response['documentation_url'], color=RColor.blue, styles=RStyle.underlined)
							.h(response['documentation_url'])
							.c(RAction.open_url, response['documentation_url'])
						)
			else:
				try:
					cmp_result = misc_util.version_compare(constant.VERSION, latest_version.lstrip('v'))
				except:
					self.mcdr_server.logger.exception('Fail to compare between versions "{}" and "{}"'.format(constant.VERSION, latest_version))
					return
				if cmp_result == 0:
					reply_func(self.mcdr_server.tr('update_helper.check_update.is_already_latest'))
				elif cmp_result == 1:
					reply_func(self.mcdr_server.tr('update_helper.check_update.newer_than_latest', constant.VERSION, latest_version))
				else:
					reply_func(self.mcdr_server.tr('update_helper.check_update.new_version_detected', latest_version))
					for line in update_log.splitlines():
						reply_func('    {}'.format(line))
		finally:
			self.update_lock.release()
