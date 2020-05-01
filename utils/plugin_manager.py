# -*- coding: utf-8 -*-
import os

from utils import tool, constant
from utils.plugin import Plugin


class PluginManager:
	def __init__(self, server, plugin_folder):
		self.plugin_folder = plugin_folder
		self.server = server
		self.logger = server.logger
		self.plugins = []

	def __get_file_list(self, suffix):
		if not os.path.isdir(self.plugin_folder):
			os.makedirs(self.plugin_folder)
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
		else:
			if not obj.endswith(constant.PLUGIN_FILE_SUFFIX):
				obj += constant.PLUGIN_FILE_SUFFIX
			for plugin in self.plugins:
				if plugin.file_name == obj:
					return plugin
		return None

	# load and append the plugin to the plugin list
	# file_name is a str like my_plugin.py
	# call_event is to decide whether to call on_load or not
	# return the plugin instance or None
	def load_plugin(self, file_name, call_event=True):
		try:
			# get the existed one or create a new one
			plugin = self.get_loaded_plugin_file_name_dict().get(file_name, Plugin(self.server, os.path.join(self.plugin_folder, file_name)))
			plugin.load()
			if plugin not in self.plugins:
				self.plugins.append(plugin)
			if call_event:
				plugin.call_on_load()
			self.logger.info(self.server.t('plugin_manager.load_plugin.success', file_name))
			return plugin
		except:
			self.logger.exception(self.server.t('plugin_manager.load_plugin.fail', file_name))
			return None

	# reload the plugin
	# if loading fail remove the plugin from the plugin list
	def reload_plugin(self, plugin, call_event=True):
		try:
			if call_event:
				plugin.call_on_unload()
			plugin.load()
			if call_event:
				plugin.call_on_load()
			self.logger.info(self.server.t('plugin_manager.load_plugin.success', plugin.file_name))
			return True
		except:
			self.logger.exception(self.server.t('plugin_manager.load_plugin.fail', plugin.file_name))
			self.plugins.remove(plugin)
			return False

	# remove the plugin from the plugin list
	# obj can be Plugin instance of a str like my_plugin or my_plugin.py
	def unload_plugin(self, obj, call_event=True):
		plugin = self.get_plugin(obj)
		try:
			if call_event:
				plugin.call_on_unload()
			self.plugins.remove(plugin)
			self.logger.info(self.server.t('plugin_manager.unload_plugin.unload_success', plugin.file_name))
			return True
		except:
			self.logger.exception(self.server.t('plugin_manager.unload_plugin.unload_fail', plugin.file_name))
			return False

	# enable and load
	# file_name is my_plugin.py.disabled
	def enable_plugin(self, file_name) -> bool:
		file_path = os.path.join(self.plugin_folder, file_name)
		new_file_path = tool.remove_suffix(file_path, constant.DISABLED_PLUGIN_FILE_SUFFIX)
		if os.path.isfile(file_path):
			os.rename(file_path, new_file_path)
		return bool(self.load_plugin(os.path.basename(new_file_path)))

	# unload and disable
	# file_name is my_plugin.py
	def disable_plugin(self, file_name):
		plugin = self.get_plugin(file_name)
		if plugin is not None:
			self.unload_plugin(plugin)
		file_path = os.path.join(self.plugin_folder, file_name)
		if os.path.isfile(file_path):
			os.rename(file_path, file_path + constant.DISABLED_PLUGIN_FILE_SUFFIX)

	# Multiple plugin manipulation

	def load_new_plugins(self):
		counter_load = 0
		counter_all = 0
		name_dict = self.get_loaded_plugin_file_name_dict()
		new_plugins = []
		for file_name in self.get_plugin_file_list_all():
			if file_name not in name_dict:
				plugin = self.load_plugin(file_name, call_event=False)
				if plugin is not None:
					new_plugins.append(plugin)
				counter_load += bool(plugin)
				counter_all += 1
		for plugin in new_plugins:
			plugin.call_on_load()
		return counter_load, counter_all

	# reduce repeat code
	def __manipulate_existed_plugins(self, check, func):
		counter_done = 0
		counter_all = 0
		for plugin in self.plugins[:]:
			if check(plugin):
				counter_done += func(plugin)
				counter_all += 1
		return counter_done, counter_all

	def reload_existed_plugins(self):
		file_list = self.get_loaded_plugin_file_name_list()
		return self.__manipulate_existed_plugins(lambda p: p.file_name in file_list, self.reload_plugin)

	def reload_changed_plugins(self):
		file_list = self.get_loaded_plugin_file_name_list()
		return self.__manipulate_existed_plugins(lambda p: p.file_name in file_list and p.file_changed(), self.reload_plugin)

	def unload_removed_plugins(self):
		file_list = self.get_loaded_plugin_file_name_list()
		return self.__manipulate_existed_plugins(lambda p: p.file_name not in file_list, self.unload_plugin)

	def __refresh_plugins(self, reload_all):
		self.server.logger.info(self.server.t('plugin_manager.__refresh_plugins.loading'))

		counter_reload, counter_all1 = self.reload_existed_plugins() if reload_all else self.reload_changed_plugins()
		counter_load, counter_all2 = self.load_new_plugins()
		counter_unload, counter_all3 = self.unload_removed_plugins()

		counter_all = counter_all1 + counter_all2 + counter_all3
		counter_fail = counter_all - counter_load - counter_unload - counter_reload
		msg = []
		if counter_load > 0:
			msg.append(self.server.t('plugin_manager.__refresh_plugins.info_loaded', counter_load))
		if counter_unload > 0:
			msg.append(self.server.t('plugin_manager.__refresh_plugins.info_unloaded', counter_unload))
		if counter_reload > 0:
			msg.append(self.server.t('plugin_manager.__refresh_plugins.info_reloaded', counter_reload))
		if counter_fail > 0:
			msg.append(self.server.t('plugin_manager.__refresh_plugins.info_fail', counter_fail))
		if len(msg) == 0:
			msg = [self.server.t('plugin_manager.__refresh_plugins.info_none')]
		msg.append(self.server.t('plugin_manager.__refresh_plugins.info_plugin_amount', len(self.plugins)))
		return '; '.join(msg)

	def refresh_all_plugins(self):
		return self.__refresh_plugins(True)

	def refresh_changed_plugins(self):
		return self.__refresh_plugins(False)

	def call(self, func, args=(), wait=False):
		thread_list = []
		for plugin in self.plugins:
			thread = plugin.call(func, args)
			if thread is not None:
				thread_list.append(thread)
		if wait:
			for thread in thread_list:
				thread.join()
