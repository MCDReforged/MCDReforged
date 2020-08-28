"""
Plugin management
"""
import os
import threading

from utils import tool, constant
from utils.plugin.plugin import Plugin
from utils.plugin.plugin_thread import PluginThreadPool
from utils.rtext import *


class PluginManager:
	def __init__(self, server, plugin_folder):
		self.plugin_folder = plugin_folder
		self.server = server
		self.logger = server.logger
		self.plugins = []
		self.thread_pool = PluginThreadPool(self.server, max_thread=constant.PLUGIN_THREAD_POOL_SIZE)
		self.plugin_load_lock = threading.Lock()
		tool.touch_folder(self.plugin_folder)
		tool.touch_folder(constant.PLUGIN_CONFIG_FOLDER)

	# --------------------------
	# Single plugin manipulation
	# --------------------------

	def load_plugin(self, obj, call_on_load=True):
		"""
		Load and append the plugin to the plugin list
		Reload if it's already loaded
		Call_event is to decide whether to call on_load or not
		Return the plugin instance or None
		:param obj:
		:param call_on_load:
		:return: Plugin instance if success else None
		"""

	def unload_plugin(self, obj):
		"""
		Remove the plugin from the plugin list
		Obj can be Plugin instance of a str like my_plugin or my_plugin.py
		:param obj:
		:return: a bool, if success
		"""

	def enable_plugin(self, file_name) -> bool:
		"""
		Enable and load
		:param obj:
		:return: a bool, if success
		"""

	def disable_plugin(self, file_name):
		"""
		Unload and disable
		:param obj:
		:return: a bool, if success
		"""

	# ----------------------------
	# Multiple plugin manipulation
	# ----------------------------

	def __refresh_plugins(self, reload_all):
		"""
		1. reload existed (and changed) plugins. if reload fail unload it
		2. load new plugins, and ignore those plugins which just got unloaded because reloading failed
		3. unload removed plugins
		4. call on_load for new loaded plugins
		:param reload_all:
		:return:
		"""
		self.server.logger.info(self.server.t('plugin_manager.__refresh_plugins.loading'))

		reload_list, reload_fail_list = self.__reload_existed_plugins() if reload_all else self.__refresh_changed_plugins()
		load_list, load_fail_list = self.__load_new_plugins(except_list=reload_fail_list)
		unload_list, unload_fail_list = self.__unload_removed_plugins()

		for name in reload_list + load_list:
			self.get_plugin(name).call_on_load()

		# result information prepare
		fail_list = \
			['[§6{}§r]'.format(self.server.t('plugin_manager.load'))] + load_fail_list + \
			['[§6{}§r]'.format(self.server.t('plugin_manager.unload'))] + unload_fail_list + \
			['[§6{}§r]'.format(self.server.t('plugin_manager.reload'))] + reload_fail_list

		msg = RTextList()
		if load_list:
			msg.append(RText(self.server.t('plugin_manager.__refresh_plugins.info_loaded', len(load_list))).h('\n'.join(load_list)), '; ')
		if unload_list:
			msg.append(RText(self.server.t('plugin_manager.__refresh_plugins.info_unloaded', len(unload_list))).h('\n'.join(unload_list)), '; ')
		if reload_list:
			msg.append(RText(self.server.t('plugin_manager.__refresh_plugins.info_reloaded', len(reload_list))).h('\n'.join(reload_list)), '; ')
		if load_fail_list or unload_fail_list or reload_fail_list:
			msg.append(RText(self.server.t('plugin_manager.__refresh_plugins.info_fail', len(fail_list) - 3)).h('\n'.join(fail_list)), '; ')
		if msg.empty():
			msg = [self.server.t('plugin_manager.__refresh_plugins.info_none'), '; ']
		msg.append(
			RText(self.server.t('plugin_manager.__refresh_plugins.info_plugin_amount', len(self.plugins)))
			.h('\n'.join([plugin.file_name for plugin in self.plugins]))
			.c(RAction.suggest_command, '!!MCDR plugin list')
		)
		return msg

	def refresh_all_plugins(self):
		"""
		An interface to call, load / reload / unload all plugins
		:return: Message of this action
		"""
		return self.__refresh_plugins(True)

	def refresh_changed_plugins(self):
		"""
		An interface to call, load / reload / unload all changed plugins
		:return: Message of this action
		"""
		return self.__refresh_plugins(False)

	# -----------------
	# Plugin event call
	# -----------------

	def call(self, func, args=(), wait=False):
		thread_list = []
		for plugin in self.plugins:
			thread = plugin.call(func, args, forced_new_thread=wait)
			if isinstance(thread, threading.Thread):
				thread_list.append(thread)
		if wait:
			for thread in thread_list:
				thread.join()
