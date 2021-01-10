"""
MCDR update things
"""
import os
import time
from threading import Lock
from typing import TYPE_CHECKING, Callable, Any, Union

import requests

from mcdreforged import constant
from mcdreforged.minecraft.rtext import RText, RAction, RColor, RStyle, RTextBase
from mcdreforged.utils import misc_util, file_util

if TYPE_CHECKING:
	from mcdreforged import MCDReforgedServer


class UpdateHelper:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.check_update_thread = None
		self.update_lock = Lock()

	def check_update_start(self):
		self.check_update_thread = misc_util.start_thread(self.check_update_loop, (), type(self).__name__)

	def check_update_loop(self):
		while True:
			self.check_update(lambda: self.mcdr_server.config['check_update'] is True, self.mcdr_server.logger.info)
			time.sleep(24 * 60 * 60)

	def check_update(self, condition_check: Callable[[], bool], reply_func: Callable[[Union[str or RTextBase]], Any]):
		misc_util.start_thread(self.__check_update, (condition_check, reply_func), 'CheckUpdate')

	def __check_update(self, condition_check: Callable[[], bool], reply_func: Callable[[Union[str or RTextBase]], Any]):
		if not condition_check():
			return
		acquired = self.update_lock.acquire(blocking=False)
		if not acquired:
			reply_func(self.mcdr_server.tr('update_helper.check_update.already_checking'))
			return False
		try:
			response = None
			try:
				response = requests.get(constant.GITHUB_API_LATEST, timeout=5).json()
				latest_version = response['tag_name']
				url = response['html_url']
				download_url = response['assets'][0]['browser_download_url']
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
					cmp_result = misc_util.version_compare(constant.VERSION, latest_version)
				except:
					self.mcdr_server.logger.exception('Fail to compare between versions "{}" and "{}"'.format(constant.VERSION, latest_version))
					return False
				if cmp_result == 0:
					reply_func(self.mcdr_server.tr('update_helper.check_update.is_already_latest'))
				elif cmp_result == 1:
					reply_func(self.mcdr_server.tr('update_helper.check_update.newer_than_latest', constant.VERSION, latest_version))
				else:
					reply_func(self.mcdr_server.tr('update_helper.check_update.new_version_detected', latest_version))
					for line in update_log.splitlines():
						reply_func('    {}'.format(line))
					reply_func(self.mcdr_server.tr('update_helper.check_update.new_version_url', url))
					if self.mcdr_server.config['download_update']:
						try:
							file_util.touch_folder(constant.UPDATE_DOWNLOAD_FOLDER)
							file_name = os.path.join(constant.UPDATE_DOWNLOAD_FOLDER, os.path.basename(download_url))
							if not os.path.isfile(file_name):
								file_data = requests.get(download_url, timeout=5)
								with open(file_name, 'wb') as file:
									file.write(file_data.content)
							reply_func(self.mcdr_server.tr('update_helper.check_update.download_finished', file_name))
						except:
							reply_func(self.mcdr_server.tr('update_helper.check_update.download_fail'))
						else:
							return True
			return False
		finally:
			self.update_lock.release()
