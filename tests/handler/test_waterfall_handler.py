import unittest

from mcdreforged.handler.impl.waterfall_handler import WaterfallHandler


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.handler = WaterfallHandler()

	def test_0_general(self):
		self.assertEqual(self.handler.get_name(), 'waterfall_handler')
		info = self.handler.parse_server_stdout(r'[02:18:29 INFO]: Loaded plugin cmd_list version git:cmd_list:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC')
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual(r'Loaded plugin cmd_list version git:cmd_list:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC', info.content)

	def test_1_player(self):
		# bungeecord doesn't output player chat messages
		pass

	def test_2_player_events(self):
		# waterfall doesn't display player name during connection

		info = self.handler.parse_server_stdout('[02:21:36 INFO]: [/127.0.0.1:14426|Fallen_Breath] -> UpstreamBridge has disconnected')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_left(info))

	def test_3_server_info(self):
		# Proxy has no game version
		info = self.handler.parse_server_stdout('[02:18:40 INFO]: Listening on /0.0.0.0:25777')
		self.assertEqual(('0.0.0.0', 25777), self.handler.parse_server_ip(info))

	def test_4_server_events(self):
		info = self.handler.parse_server_stdout('[02:18:40 INFO]: Listening on /0.0.0.0:25777')
		self.assertEqual(True, self.handler.test_server_startup_done(info))
		info = self.handler.parse_server_stdout('[02:18:40 INFO]: Listening on /0.0.0.0:25777')
		self.assertEqual(True, self.handler.test_rcon_started(info))  # it uses test_server_startup_done
		info = self.handler.parse_server_stdout('[02:21:39 INFO]: Closing listener [id: 0x7c536f18, L:/0:0:0:0:0:0:0:0:25777]')
		self.assertEqual(True, self.handler.test_server_stopping(info))

	def test_5_lifecycle(self):
		for line in TEXT.splitlines():
			try:
				info = self.handler.parse_server_stdout(line)
			except:
				print('error when parsing line "{}"'.format(line))
				raise
			# no exception
			if not info.is_player:
				self.assertEqual(line.split(']: ', 1)[1], info.content)


TEXT = r'''
[02:18:29 INFO]: Loaded plugin ViaVersion version 3.0.0-SNAPSHOT by _MylesC, creeper123123321, Gerrygames, KennyTV, Matsv
[02:18:29 INFO]: Loaded plugin ViaRewind version 1.5.0-SNAPSHOT by Gerrygames
[02:18:29 INFO]: Loaded plugin reconnect_yaml version git:reconnect_yaml:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 INFO]: Loaded plugin cmd_find version git:cmd_find:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 INFO]: Loaded plugin cmd_server version git:cmd_server:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 INFO]: Loaded plugin cmd_alert version git:cmd_alert:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 INFO]: Loaded plugin cmd_send version git:cmd_send:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 INFO]: Loaded plugin ViaBackwards version 3.0.0-SNAPSHOT by Matsv, KennyTV, Gerrygames, creeper123123321, ForceUpdate1
[02:18:29 INFO]: Loaded plugin cmd_list version git:cmd_list:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 WARN]: Forced host server pvp is not defined
[02:18:29 INFO] [ViaVersion]: Loading 1.12.2 -> 1.13 mappings...
[02:18:29 INFO] [ViaVersion]: Loading 1.13.2 -> 1.14 mappings...
[02:18:29 INFO] [ViaVersion]: Loading 1.14.4 -> 1.15 mappings...
[02:18:29 INFO] [ViaVersion]: Loading 1.15 -> 1.16 mappings...
[02:18:29 INFO]: Enabled plugin ViaVersion version 3.0.0-SNAPSHOT by _MylesC, creeper123123321, Gerrygames, KennyTV, Matsv
[02:18:29 INFO] [ViaVersion]: ViaVersion detected server version: 1.8.x(47)
[02:18:29 INFO]: Enabled plugin ViaRewind version 1.5.0-SNAPSHOT by Gerrygames
[02:18:29 INFO]: Enabled plugin reconnect_yaml version git:reconnect_yaml:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 INFO]: Enabled plugin cmd_find version git:cmd_find:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 INFO]: Enabled plugin cmd_server version git:cmd_server:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 INFO]: Enabled plugin cmd_alert version git:cmd_alert:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 INFO]: Enabled plugin cmd_send version git:cmd_send:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:29 INFO] [ViaBackwards]: Loading translations...
[02:18:29 INFO] [ViaBackwards]: Registering protocols...
[02:18:30 INFO]: Enabled plugin ViaBackwards version 3.0.0-SNAPSHOT by Matsv, KennyTV, Gerrygames, creeper123123321, ForceUpdate1
[02:18:30 INFO]: Enabled plugin cmd_list version git:cmd_list:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
[02:18:30 INFO] [ViaBackwards]: Loading 1.13 -> 1.12.2 mappings...
[02:18:31 WARN] [ViaVersion]: There is a newer version available: 3.2.1, you're on: 3.0.0-SNAPSHOT
[02:18:32 INFO] [ViaBackwards]: Loading 1.14 -> 1.13.2 mappings...
[02:18:33 INFO] [ViaBackwards]: Loading 1.15 -> 1.14.4 mappings...
[02:18:35 INFO] [ViaBackwards]: Loading 1.16 -> 1.15.2 mappings...
[02:18:40 INFO]: Listening on /0.0.0.0:25777
[02:18:52 INFO]: [/127.0.0.1:14426] <-> InitialHandler has connected
[02:19:04 INFO]: [Fallen_Breath|/127.0.0.1:14426] <-> ServerConnector [lobby] has connected
[02:20:34 INFO]: an alertraw message www
[02:21:35 INFO]: [Fallen_Breath] disconnected with: Internal Exception: java.lang.StackOverflowError
[02:21:35 WARN]: [/127.0.0.1:14426|Fallen_Breath] <-> DownstreamBridge <-> [lobby] - IOException: 你的主机中的软件中止了一个已建立的连接。
[02:21:35 INFO]: [/127.0.0.1:14426|Fallen_Breath] <-> DownstreamBridge <-> [lobby] has disconnected
[02:21:36 INFO]: [/127.0.0.1:14426|Fallen_Breath] -> UpstreamBridge has disconnected
[02:21:39 INFO]: Closing listener [id: 0x7c536f18, L:/0:0:0:0:0:0:0:0:25777]
[02:21:39 INFO]: Closing pending connections
[02:21:39 INFO]: Disconnecting 0 connections
[02:21:39 INFO]: Saving reconnect locations
[02:21:39 INFO]: Disabling plugins
[02:21:39 INFO]: Closing IO threads
[02:21:41 INFO]: Thank you and goodbye
'''.strip()


if __name__ == '__main__':
	unittest.main()
