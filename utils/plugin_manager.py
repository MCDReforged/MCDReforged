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
			self.logger.warning(f'Fail to load plugin {file_name}')
			self.logger.warning(traceback.format_exc())
			return False
		else:
			self.plugins.append(plugin)
			self.logger.info('Plugin {} loaded'.format(plugin.file_name))
			return True

	def unload_plugin(self, plugin):
		try:
			plugin.unload()
		except:
			self.logger.warning(f'Fail to unload plugin {plugin.file_name}')
			self.logger.warning(traceback.format_exc())
			ret = False
		else:
			self.logger.info('Plugin {} unloaded'.format(plugin.file_name))
			ret = True
		finally:
			self.plugins.remove(plugin)
		return ret

	def reload_plugin(self, plugin):
		try:
			plugin.reload()
		except:
			self.logger.warning(f'Fail to reload plugin {plugin.file_name}')
			self.logger.warning(traceback.format_exc())
			self.plugins.remove(plugin)
			return False
		else:
			self.logger.info('Plugin {} reloaded'.format(plugin.file_name))
			return True

	def load_plugins(self):
		self.server.logger.info('Loading plugins')

		# init
		self.command_prefix_listeners = {}
		if not os.path.isdir(constant.PLUGIN_FOLDER):
			os.makedirs(constant.PLUGIN_FOLDER)
		file_list = tool.list_py_file(constant.PLUGIN_FOLDER)
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
		for plugin in self.plugins:
			if plugin.file_name not in file_list:
				counter_unload += self.unload_plugin(plugin)
				counter_all += 1
		# end
		counter_fail = counter_all - counter_load - counter_unload - counter_reload
		msg = []
		if counter_load > 0:
			msg.append('Loaded: {} plugins'.format(counter_load))
		if counter_unload > 0:
			msg.append('Unloaded: {} plugins'.format(counter_unload))
		if counter_reload > 0:
			msg.append('Reloaded: {} plugins'.format(counter_reload))
		if counter_fail > 0:
			msg.append('Failed: {} plugins'.format(counter_fail))
		if len(msg) == 0:
			msg = 'No plugin operation has occurred'
		else:
			msg = '; '.join(msg)
		return msg

	def call(self, func, args=(), new_thread=True):
		for plugin in self.plugins:
			plugin.call(func, args, new_thread)
