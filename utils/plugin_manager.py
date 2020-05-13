# -*- coding: utf-8 -*-
import os
import threading

from utils import tool, constant
from utils.plugin_thread import PluginThreadPool
from utils.rtext import *
from utils.plugin import Plugin


class PluginManager:
	def __init__(self, server, plugin_folder):
		self.plugin_folder = plugin_folder
		self.server = server
		self.logger = server.logger
		self.plugins = []
		self.thread_pool = PluginThreadPool(self.server)
		tool.touch_folder(self.plugin_folder)
		tool.touch_folder(constant.PLUGIN_CONFIG_FOLDER)

	def __get_file_list(self, suffix):
		full_path_list = tool.list_file(self.plugin_folder, suffix)
		return [path.replace(self.plugin_folder + os.path.sep, '', 1) for path in full_path_list]

	def get_plugin_file_list_all(self):
		return self.__get_file_list(constant.PLUGIN_FILE_SUFFIX)

	def get_plugin_file_list_disabled(self):
		return self.__get_file_list(constant.PLUGIN_FILE_SUFFIX + constant.DISABLED_PLUGIN_FILE_SUFFIX)

	def get_loaded_plugin_file_name_dict(self):
		return {plugin.file_name: plugin for plugin in self.plugins}

	def get_loaded_plugin_file_name_list(self):
		return self.get_loaded_plugin_file_name_dict().keys()

	def get_plugin(self, obj):
		if type(obj) is Plugin:
			return obj
		elif type(obj) is str:
			file_name = tool.format_plugin_file_name(obj)
			return self.get_loaded_plugin_file_name_dict().get(file_name)
		else:
			raise TypeError('The object to load needs to be a Plugin or a str')

	# --------------------------
	# Single plugin manipulation
	# --------------------------

	# load and append the plugin to the plugin list
	# reload if it's already loaded
	# call_event is to decide whether to call on_load or not
	# return the plugin instance or None
	def load_plugin(self, obj, call_on_load=True):
		plugin = self.get_plugin(obj)
		try:
			# get the existed one or create a new one
			if type(plugin) is Plugin:
				plugin.unload()
			else:
				plugin = Plugin(self.server, os.path.join(self.plugin_folder, obj))
			plugin.load()
			if plugin not in self.plugins:
				self.plugins.append(plugin)
			if call_on_load:
				plugin.call_on_load()
			self.logger.info(self.server.t('plugin_manager.load_plugin.success', plugin.file_name))
			return plugin
		except:
			self.logger.exception(self.server.t('plugin_manager.load_plugin.fail', plugin.file_name))
			if plugin in self.plugins:
				self.plugins.remove(plugin)
			return None

	# remove the plugin from the plugin list
	# obj can be Plugin instance of a str like my_plugin or my_plugin.py
	def unload_plugin(self, obj):
		plugin = self.get_plugin(obj)
		try:
			plugin.unload()
			self.plugins.remove(plugin)
			self.logger.info(self.server.t('plugin_manager.unload_plugin.unload_success', plugin.file_name))
			return True
		except:
			self.logger.exception(self.server.t('plugin_manager.unload_plugin.unload_fail', plugin.file_name))
			return False

	# enable and load
	def enable_plugin(self, file_name) -> bool:
		file_name = tool.format_plugin_file_name_disabled(file_name)
		file_path = os.path.join(self.plugin_folder, file_name)
		new_file_path = tool.remove_suffix(file_path, constant.DISABLED_PLUGIN_FILE_SUFFIX)
		if os.path.isfile(file_path):
			os.rename(file_path, new_file_path)
			return bool(self.load_plugin(os.path.basename(new_file_path)))
		return False

	# unload and disable
	def disable_plugin(self, file_name):
		plugin = self.get_plugin(file_name)
		if plugin is not None:
			self.unload_plugin(plugin)
		file_path = os.path.join(self.plugin_folder, file_name)
		if os.path.isfile(file_path):
			os.rename(file_path, file_path + constant.DISABLED_PLUGIN_FILE_SUFFIX)

	# ----------------------------
	# Multiple plugin manipulation
	# ----------------------------

	def __load_new_plugins(self, except_list=None):
		if except_list is None:
			except_list = []
		load_list = []
		list_fail = []
		name_dict = self.get_loaded_plugin_file_name_dict()
		for file_name in self.get_plugin_file_list_all():
			if file_name not in name_dict and file_name not in except_list:
				plugin = self.load_plugin(file_name, call_on_load=False)
				if plugin is not None:
					load_list.append(plugin.file_name)
				else:
					list_fail.append(file_name)
		return load_list, list_fail

	# reduce repeat code
	def __manipulate_existed_plugins(self, check, func, **kwargs):
		done_list = []
		list_fail = []
		for plugin in self.plugins[:]:
			if check(plugin):
				if func(plugin, **kwargs):
					done_list.append(plugin.file_name)
				else:
					list_fail.append(plugin.file_name)
		return done_list, list_fail

	# reload plugins that are loaded and still existed in the plugin folder
	def __reload_existed_plugins(self):
		file_list = self.get_plugin_file_list_all()
		return self.__manipulate_existed_plugins(lambda p: p.file_name in file_list, self.load_plugin, call_on_load=False)

	# reload plugins that are loaded and still existed in the plugin folder, and its file has been modified
	def __refresh_changed_plugins(self):
		file_list = self.get_plugin_file_list_all()
		return self.__manipulate_existed_plugins(lambda p: p.file_name in file_list and p.file_changed(), self.load_plugin, call_on_load=False)

	def __unload_removed_plugins(self):
		file_list = self.get_plugin_file_list_all()
		return self.__manipulate_existed_plugins(lambda p: p.file_name not in file_list, self.unload_plugin)

	def __refresh_plugins(self, reload_all):
		self.server.logger.info(self.server.t('plugin_manager.__refresh_plugins.loading'))

		# 1. reload existed (and changed) plugins. if reload fail unload it
		reload_list, reload_fail_list = self.__reload_existed_plugins() if reload_all else self.__refresh_changed_plugins()

		# 2. load new plugins, and ignore those plugins which just got unloaded because reloading failed
		load_list, load_fail_list = self.__load_new_plugins(except_list=reload_fail_list)

		# 3. unload removed plugins
		unload_list, unload_fail_list = self.__unload_removed_plugins()

		# 4. call on_load for new loaded plugins
		for name in reload_list + load_list:
			self.get_plugin(name).call_on_load()

		# result information prepare
		fail_list = \
			['[§6{}§r]'.format(self.server.t('plugin_manager.load'))] + load_fail_list + \
			['[§6{}§r]'.format(self.server.t('plugin_manager.unload'))] + unload_fail_list + \
			['[§6{}§r]'.format(self.server.t('plugin_manager.reload'))] + reload_fail_list

		msg = []
		if load_list:
			msg.extend([RText(self.server.t('plugin_manager.__refresh_plugins.info_loaded', len(load_list))).h('\n'.join(load_list)), '; '])
		if unload_list:
			msg.extend([RText(self.server.t('plugin_manager.__refresh_plugins.info_unloaded', len(unload_list))).h('\n'.join(unload_list)), '; '])
		if reload_list:
			msg.extend([RText(self.server.t('plugin_manager.__refresh_plugins.info_reloaded', len(reload_list))).h('\n'.join(reload_list)), '; '])
		if load_fail_list or unload_fail_list or reload_fail_list:
			msg.extend([RText(self.server.t('plugin_manager.__refresh_plugins.info_fail', len(fail_list) - 3)).h('\n'.join(fail_list)), '; '])
		if len(msg) == 0:
			msg = [self.server.t('plugin_manager.__refresh_plugins.info_none'), '; ']
		msg.append(RText(self.server.t('plugin_manager.__refresh_plugins.info_plugin_amount', len(self.plugins)))
			.h('\n'.join([plugin.file_name for plugin in self.plugins]))
			.c(RAction.suggest_command, '!!MCDR plugin list')
		)
		return RTextList(*tuple(msg))

	# an interface to call, load / reload / unload all plugins
	def refresh_all_plugins(self):
		return self.__refresh_plugins(True)

	# an interface to call, load / reload / unload all changed plugins
	def refresh_changed_plugins(self):
		return self.__refresh_plugins(False)

	# -----------------
	# Plugin event call
	# -----------------

	def call(self, func, args=(), wait=False):
		thread_list = []
		for plugin in self.plugins:
			thread = plugin.call(func, args)
			if isinstance(thread, threading.Thread):
				thread_list.append(thread)
		if wait:
			self.thread_pool.join()
