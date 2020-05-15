# -*- coding: utf-8 -*-
import os
import time
from threading import Lock

import requests
from utils import tool, constant


class UpdateHelper:
	def __init__(self, server):
		self.server = server
		self.check_update_thread = None
		self.update_lock = Lock()

	def check_update_start(self):
		self.check_update_thread = tool.start_thread(self.check_update_loop, (), type(self).__name__)

	def check_update_loop(self):
		while True:
			self.check_update()
			time.sleep(24 * 60 * 60)

	def check_update(self, reply_func=None):
		acquired = self.update_lock.acquire(blocking=False)
		if not acquired:
			reply_func(self.server.t('update_helper.check_update.already_checking'))
			return False
		try:
			if reply_func is None:
				reply_func = self.server.logger.info
			try:
				response = requests.get(constant.GITHUB_API_LATEST, timeout=5).json()
				latest_version = response['tag_name']
				url = response['html_url']
				download_url = response['assets'][0]['browser_download_url']
			except Exception as e:
				reply_func(self.server.t('update_helper.check_update.check_fail', repr(e)))
			else:
				cmp_result = tool.version_compare(constant.VERSION, latest_version)
				if cmp_result == 0:
					reply_func(self.server.t('update_helper.check_update.is_already_latest'))
				elif cmp_result == 1:
					reply_func(self.server.t('update_helper.check_update.newer_than_latest', constant.VERSION, latest_version))
				else:
					reply_func(self.server.t('update_helper.check_update.new_version_detected', latest_version))
					for line in response['body'].splitlines():
						reply_func('    {}'.format(line))
					reply_func(self.server.t('update_helper.check_update.new_version_url', url))
					if self.server.config['download_update']:
						try:
							tool.touch_folder(constant.UPDATE_DOWNLOAD_FOLDER)
							file_name = os.path.join(constant.UPDATE_DOWNLOAD_FOLDER, os.path.basename(download_url))
							if not os.path.isfile(file_name):
								file_data = requests.get(download_url, timeout=5)
								with open(file_name, 'wb') as file:
									file.write(file_data.content)
							reply_func(self.server.t('update_helper.check_update.download_finished', file_name))
						except:
							reply_func(self.server.t('update_helper.check_update.download_fail'))
						else:
							return True
			return False
		finally:
			self.update_lock.release()
