# -*- coding: utf-8 -*-
import os

from utils import tool, constant
from utils.rtext import *
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
			file_name = tool.format_plugin_file_name(obj)
			for plugin in self.plugins:
				if plugin.file_name == file_name:
					return plugin
		return None

	# load and append the plugin to the plugin list
	# call_event is to decide whether to call on_load or not
	# return the plugin instance or None
	def load_plugin(self, file_name, call_event=True):
		file_name = tool.format_plugin_file_name(file_name)
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

	# Multiple plugin manipulation

	def load_new_plugins(self):
		load_list = []
		list_fail = []
		name_dict = self.get_loaded_plugin_file_name_dict()
		new_plugins = []
		for file_name in self.get_plugin_file_list_all():
			if file_name not in name_dict:
				plugin = self.load_plugin(file_name, call_event=False)
				if plugin is not None:
					new_plugins.append(plugin)
					load_list.append(plugin.file_name)
				else:
					list_fail.append(file_name)
		for plugin in new_plugins:
			plugin.call_on_load()
		return load_list, list_fail

	# reduce repeat code
	def __manipulate_existed_plugins(self, check, func):
		done_list = []
		list_fail = []
		for plugin in self.plugins[:]:
			if check(plugin):
				if func(plugin):
					done_list.append(plugin.file_name)
				else:
					list_fail.append(plugin.file_name)
		return done_list, list_fail

	# reload plugins that are loaded and still existed in the plugin folder
	def __reload_existed_plugins(self):
		file_list = self.get_plugin_file_list_all()
		return self.__manipulate_existed_plugins(lambda p: p.file_name in file_list, self.reload_plugin)

	# reload plugins that are loaded and still existed in the plugin folder, and its file has been modified
	def __refresh_changed_plugins(self):
		file_list = self.get_plugin_file_list_all()
		return self.__manipulate_existed_plugins(lambda p: p.file_name in file_list and p.file_changed(), self.reload_plugin)

	def unload_removed_plugins(self):
		file_list = self.get_plugin_file_list_all()
		return self.__manipulate_existed_plugins(lambda p: p.file_name not in file_list, self.unload_plugin)

	def __refresh_plugins(self, reload_all):
		self.server.logger.info(self.server.t('plugin_manager.__refresh_plugins.loading'))

		load_list, load_fail_list = self.load_new_plugins()
		unload_list, unload_fail_list = self.unload_removed_plugins()
		reload_list, reload_fail_list = self.__reload_existed_plugins() if reload_all else self.__refresh_changed_plugins()
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

	def call(self, func, args=(), wait=False):
		thread_list = []
		for plugin in self.plugins:
			thread = plugin.call(func, args)
			if thread is not None:
				thread_list.append(thread)
		if wait:
			for thread in thread_list:
				thread.join()
