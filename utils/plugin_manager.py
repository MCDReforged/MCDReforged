# -*- coding: utf-8 -*-
import os
import traceback

from utils import tool, constant
from utils.plugin import Plugin


class PluginManager:
	def __init__(self, server, plugin_folder):
		self.plugin_folder = plugin_folder
		self.server = server
		self.logger = server.logger
		self.plugins = []
		self.command_prefix_listeners = None

	def load_plugin(self, file_name):
		try:
			plugin = Plugin(self.server, file_name)
			plugin.load()
		except:
			self.logger.warning(self.server.t('plugin_manager.load_plugin.load_fail', file_name))
			self.logger.warning(traceback.format_exc())
			return False
		else:
			self.plugins.append(plugin)
			self.logger.info(self.server.t('plugin_manager.load_plugin.load_success', file_name))
			return True

	def unload_plugin(self, plugin):
		try:
			plugin.unload()
		except:
			self.logger.warning(self.server.t('plugin_manager.unload_plugin.unload_fail', plugin.plugin_name))
			self.logger.warning(traceback.format_exc())
			ret = False
		else:
			self.logger.info(self.server.t('plugin_manager.unload_plugin.unload_success', plugin.plugin_name))
			ret = True
		return ret

	def reload_plugin(self, plugin):
		try:
			plugin.reload()
		except:
			self.logger.warning(self.server.t('plugin_manager.reload_plugin.reload_fail', plugin.plugin_name))
			self.logger.warning(traceback.format_exc())
			self.plugins.remove(plugin)
			return False
		else:
			self.logger.info(self.server.t('plugin_manager.reload_plugin.reload_success', plugin.plugin_name))
			return True

	def load_plugins(self):
		self.server.logger.info(self.server.t('plugin_manager.load_plugins.loading'))

		# init
		self.server.command_manager.clean_help_message()
		self.command_prefix_listeners = {}
		if not os.path.isdir(constant.PLUGIN_FOLDER):
			os.makedirs(constant.PLUGIN_FOLDER)
		file_list = tool.list_file(constant.PLUGIN_FOLDER, '.py')
		name_dict = {plugin.file_name: plugin for plugin in self.plugins}
		counter_all = counter_load = counter_unload = counter_reload = 0

		# load and reload
		for file_name in file_list:
			if file_name in name_dict:
				plugin = name_dict[file_name]
				counter_reload += self.reload_plugin(plugin)
				counter_all += 1
			else:
				counter_load += self.load_plugin(file_name)
				counter_all += 1
		# unload
		unload_list = []
		for plugin in self.plugins:
			if plugin.file_name not in file_list:
				counter_unload += self.unload_plugin(plugin)
				counter_all += 1
				unload_list.append(plugin)
		for plugin in unload_list:
			self.plugins.remove(plugin)
		# end
		counter_fail = counter_all - counter_load - counter_unload - counter_reload
		msg = []
		if counter_load > 0:
			msg.append(self.server.t('plugin_manager.load_plugins.info_loaded', counter_load))
		if counter_unload > 0:
			msg.append(self.server.t('plugin_manager.load_plugins.info_unloaded', counter_unload))
		if counter_reload > 0:
			msg.append(self.server.t('plugin_manager.load_plugins.info_reloaded', counter_reload))
		if counter_fail > 0:
			msg.append(self.server.t('plugin_manager.load_plugins.info_fail', counter_fail))
		if len(msg) == 0:
			msg = self.server.t('plugin_manager.load_plugins.info_none')
		else:
			msg = '; '.join(msg)
		return msg

	def call(self, func, args=(), wait=False):
		self.logger.debug('Calling function "{}" in plugins with {} parameters'.format(func, len(args)))
		thread_list = []
		for plugin in self.plugins:
			thread = plugin.call(func, args)
			if thread is not None:
				thread_list.append(thread)
		if wait:
			for thread in thread_list:
				thread.join()

	def get_plugin(self, plugin_name):
		for plugin in self.plugins:
			if plugin.plugin_name == plugin_name:
				return plugin
		return None
