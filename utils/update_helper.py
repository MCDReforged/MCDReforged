# -*- coding: utf-8 -*-
import os
import requests
from utils import tool, constant


class UpdateHelper:
	def __init__(self, server):
		self.server = server
		self.check_update_thread = None

	def check_update(self):
		self.check_update_thread = tool.start_thread(self._check_update, (), type(self).__name__)

	def _check_update(self):
		try:
			response = requests.get('https://api.github.com/repos/Fallen-Breath/MCDReforged/releases/latest').json()
			latest_version = response['tag_name']
			url = response['html_url']
			download_url = response['assets'][0]['browser_download_url']
		except:
			self.server.logger.info(self.server.t('update_helper._check_update.check_fail'))
		else:
			if latest_version == constant.VERSION:
				self.server.logger.info(self.server.t('update_helper._check_update.is_already_latest'))
				return
			self.server.logger.info(self.server.t('update_helper._check_update.new_version_detected', latest_version))
			self.server.logger.info(self.server.t('update_helper._check_update.new_version_url', url))
			if self.server.config['download_update']:
				try:
					file_name = os.path.join(constant.UPDATE_DOWNLOAD_FOLDER, os.path.basename(download_url))
					if not os.path.isdir(constant.UPDATE_DOWNLOAD_FOLDER):
						os.makedirs(constant.UPDATE_DOWNLOAD_FOLDER)
					if not os.path.isfile(file_name):
						file_data = requests.get(download_url)
						with open(file_name, 'wb') as file:
							file.write(file_data.content)
					self.server.logger.info(self.server.t('update_helper._check_update.download_finished', file_name))
				except:
					self.server.logger.info(self.server.t('update_helper._check_update.download_fail'))
