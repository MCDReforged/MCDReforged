# An interface class for plugins to control the server

# -*- coding: utf-8 -*-

import threading
import time

from utils import tool
from utils.info import Info
from utils.server_status import ServerStatus
from utils.stext import *


def log_call(func):
	def wrap(self, *args, **kwargs):
		if kwargs.get('is_plugin_call', True):
			self.logger.debug('Plugin called {}(), args amount: {}'.format(func.__name__, len(args)))
			for arg in args:
				self.logger.debug('  - type: {}, content: {}'.format(type(arg).__name__, arg))
		return func(self, *args)
	return wrap


def return_if_success(func):
	def wrap(self, *args, **kwargs):
		try:
			func(self, *args, **kwargs)
			return True
		except:
			self.logger.debug('Exception occurred when calling {}: ', exc_info=True)
			return False
	return wrap


class ServerInterface:
	MCDR = True  # Identifier for plugins

	def __init__(self, server):
		self.__server = server
		self.logger = server.logger

	# ------------------------
	#      Server Control
	# ------------------------

	@log_call
	def start(self):
		"""
		Start the server
		:return: a bool, if the action succeed it's True. If the server is running or being starting by other plugin return False
		"""
		return self.__server.start_server()

	@log_call
	def stop(self):
		"""
		Soft shutting down the server by sending the correct stop command to the server

		:return: None
		"""
		self.__server.stop(forced=False, new_server_status=ServerStatus.STOPPING_BY_PLUGIN)

	@log_call
	def wait_for_start(self):
		"""
		Wait until the server is stopped, or is able to start

		:return: None
		"""
		while self.is_server_running(is_plugin_call=False):
			time.sleep(0.01)

	@log_call
	def restart(self):
		"""
		Restart the server
		It will first soft stop the server and then wait until the server is stopped, then start the server up

		:return: None
		"""
		self.stop(is_plugin_call=False)
		self.wait_for_start(is_plugin_call=False)
		self.start(is_plugin_call=False)

	@log_call
	def stop_exit(self):
		"""
		Soft stop the server and exit MCDR

		:return: None
		"""
		self.__server.stop(forced=False)

	@log_call
	def is_server_running(self):
		"""
		:return: a bool, if the server is running
		"""
		return self.__server.is_server_running()

	@log_call
	def is_server_startup(self):
		"""
		:return: a bool, if the server has started up
		"""
		return self.__server.is_server_startup()

	@log_call
	def is_rcon_running(self):
		"""
		:return: a bool, if MCDR's rcon is running
		"""
		return self.__server.rcon_manager.is_running()

	# ------------------------
	#     Text Interaction
	# ------------------------

	@log_call
	def execute(self, text):
		"""
		Execute a command by sending the command content to server's standard input stream

		:param text: a str, The content of the command you want to send
		:return: None
		"""
		self.__server.send(text)

	@log_call
	def tell(self, player, text):
		"""
		Use /tellraw <target> to send the message to the specific player

		:param text: a str or a STextBase, the message you want to send
		:return: None
		"""
		if isinstance(text, STextBase):
			content = text.to_json_str()
		else:
			content = json.dumps(text)
		self.execute('tellraw {} {}'.format(player, content), is_plugin_call=False)

	@log_call
	def say(self, text):
		"""
		Use /tellraw @a to broadcast the message in game

		:param text: a str or a STextBase, the message you want to send
		:return: None
		"""
		self.tell('@a', text, is_plugin_call=False)

	# reply to the info source, auto detects
	@log_call
	def reply(self, info, text):
		"""
		Reply to the source of the Info
		If the Info is from a player then use tell to reply the player
		Otherwise use logger.info to output to the console

		:param info: the Info you want to reply to
		:param text: a str or a STextBase, the message you want to send
		:param kwargs:
		:return: None
		"""
		if info.is_player:
			self.tell(info.player, text, is_plugin_call=False)
		else:
			for line in str(text).splitlines():
				self.logger.info(tool.clean_minecraft_color_code(line))

	# ------------------------
	#          Other
	# ------------------------

	@log_call
	def get_permission_level(self, obj):
		"""
		return the permission level number the parameter object has
		The object can be Info instance or a str, a player name

		:param obj: The object your are querying
		:return: An int, representing the permission level
		"""
		if type(obj) is Info:  # Info instance
			return self.__server.permission_manager.get_info_permission_level(obj)
		elif type(obj) is str:  # player name
			return self.__server.permission_manager.get_player_permission_level(obj)
		else:
			return None

	@log_call
	def rcon_query(self, command):
		"""
		Send command to the server through rcon

		:param command: The command you want to send to the rcon server
		:return: The result server returned from rcon. Return None if rcon is not running or rcon query fail
		"""
		return self.__server.rcon_manager.send_command(command)

	@log_call
	def get_plugin_instance(self, plugin_name):
		"""
		Return the current loaded plugin instance. with this your plugin can access the same plugin instance as MCDR
		It's quite important to use this instead of manually import the plugin you want if the target plugin needs to
		react to events of MCDR
		The plugin need to be in plugins/plugin_name.py

		:param plugin_name: The name of the plugin you want. It can be "my_plugin" or "my_plugin.py"
		:return: A current loaded plugin instance. Return None if plugin not found
		"""
		plugin = self.__server.plugin_manager.get_plugin(plugin_name)
		if plugin is not None:
			plugin = plugin.module
		return plugin

	@log_call
	def add_help_message(self, prefix, message, is_plugin_call=True):
		"""
		Add help message for you plugin
		It's used in !!help command

		:param prefix: A str, the help command of your plugin.
		When player click on the displayed message it will suggest this prefix parameter to the player
		:param message: A str or a STextBase, a neat command description
		:return: None
		"""
		threading.current_thread().plugin.add_help_message(prefix, message)

	# ------------------------
	#          Plugin
	# ------------------------

	@log_call
	def load_plugin(self, plugin_name: str) -> bool:
		"""
		Load a plugin from the given plugin name
		If the plugin is not loaded, load the plugin. Otherwise reload the plugin

		:param plugin_name: a str, The name of the plugin. it can be "my_plugin.py" or "my_plugin"
		:return: A bool, if action succeeded
		"""
		return bool(self.__server.plugin_manager.load_plugin(plugin_name))

	@log_call
	@return_if_success
	def enable_plugin(self, plugin_name: str):
		"""
		Enable the plugin. Removed the ".disabled" suffix and load it

		:param plugin_name: a str, The name of the displayed plugin. it can be "my_plugin.py.disabled" or "my_plugin.py" or "my_plugin"
		:return: A bool, if action succeeded
		"""
		self.__server.plugin_manager.enable_plugin(plugin_name)

	@log_call
	@return_if_success
	def disable_plugin(self, plugin_name):
		"""
		Disable the plugin. Unload it and add a ".disabled" suffix to its file name

		:param plugin_name: a str, The name of the plugin. it can be "my_plugin.py" or "my_plugin"
		:return: A bool, if action succeeded
		"""
		self.__server.plugin_manager.disable_plugin(plugin_name)

	@log_call
	def reload_all_plugins(self):
		"""
		Reload all plugins, load all new plugins and then unload all removed plugins

		:return: None
		"""
		self.__server.plugin_manager.reload_all_plugins()

	@log_call
	def reload_changed_plugins(self):
		"""
		Reload all changed plugins, load all new plugins and then unload all removed plugins

		:return: None
		"""
		self.__server.plugin_manager.reload_changed_plugins()

	@log_call
	def get_plugin_list(self):
		"""
		Return a list containing all loaded plugin name like ["pluginA.py", "pluginB.py"]

		:return: a str list
		"""
		return self.__server.plugin_manager.get_plugin_file_list_all()
