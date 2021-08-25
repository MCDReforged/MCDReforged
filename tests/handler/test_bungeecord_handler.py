import unittest

from mcdreforged.handler.impl.bungeecord_handler import BungeecordHandler


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.handler = BungeecordHandler()

	def test_0_general(self):
		self.assertEqual(self.handler.get_name(), 'bungeecord_handler')
		info = self.handler.parse_server_stdout(r'02:06:38 [信息] Discovered module: ModuleSpec(name=cmd_alert, file=modules\cmd_alert.jar, provider=JenkinsModuleSource())')
		self.assertEqual('信息', info.logging_level)
		self.assertEqual(r'Discovered module: ModuleSpec(name=cmd_alert, file=modules\cmd_alert.jar, provider=JenkinsModuleSource())', info.content)

		info = self.handler.parse_server_stdout('02:06:39 [警告] Forced host server pvp is not defined')
		self.assertEqual('Forced host server pvp is not defined', info.content)
		self.assertEqual('警告', info.logging_level)

	def test_1_player(self):
		# bungeecord doesn't output player chat messages
		pass

	def test_2_player_events(self):
		info = self.handler.parse_server_stdout('02:07:04 [信息] [Fallen_Breath,/127.0.0.1:13565] <-> InitialHandler has connected')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_joined(info))

		info = self.handler.parse_server_stdout('02:07:42 [信息] [Fallen_Breath] -> UpstreamBridge has disconnected')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_left(info))

	def test_3_server_info(self):
		# Proxy has no game version
		info = self.handler.parse_server_stdout('02:07:26 [信息] Listening on /0.0.0.0:25777')
		self.assertEqual(('0.0.0.0', 25777), self.handler.parse_server_address(info))

	def test_4_server_events(self):
		info = self.handler.parse_server_stdout('02:07:26 [信息] Listening on /0.0.0.0:25777')
		self.assertEqual(True, self.handler.test_server_startup_done(info))
		info = self.handler.parse_server_stdout('02:07:26 [信息] Listening on /0.0.0.0:25777')
		self.assertEqual(True, self.handler.test_rcon_started(info))  # it uses test_server_startup_done
		info = self.handler.parse_server_stdout('02:07:46 [信息] Closing listener [id: 0x8fc98cbe, L:/0:0:0:0:0:0:0:0:25777]')
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
				self.assertEqual(line.split('] ', 1)[1], info.content)


TEXT = r'''
02:06:38 [信息] Using standard Java JCE cipher.
02:06:38 [信息] Using standard Java compressor.
02:06:38 [信息] Enabled BungeeCord version git:BungeeCord-Bootstrap:1.15-SNAPSHOT:f1c32f8:1489
02:06:38 [信息] Discovered module: ModuleSpec(name=cmd_alert, file=modules\cmd_alert.jar, provider=JenkinsModuleSource())
02:06:38 [信息] Discovered module: ModuleSpec(name=cmd_find, file=modules\cmd_find.jar, provider=JenkinsModuleSource())
02:06:38 [信息] Discovered module: ModuleSpec(name=cmd_list, file=modules\cmd_list.jar, provider=JenkinsModuleSource())
02:06:38 [信息] Discovered module: ModuleSpec(name=cmd_send, file=modules\cmd_send.jar, provider=JenkinsModuleSource())
02:06:38 [信息] Discovered module: ModuleSpec(name=cmd_server, file=modules\cmd_server.jar, provider=JenkinsModuleSource())
02:06:38 [信息] Discovered module: ModuleSpec(name=reconnect_yaml, file=modules\reconnect_yaml.jar, provider=JenkinsModuleSource())
02:06:39 [信息] Loaded plugin ViaVersion version 3.0.0-SNAPSHOT by _MylesC, creeper123123321, Gerrygames, KennyTV, Matsv
02:06:39 [信息] Loaded plugin ViaRewind version 1.5.0-SNAPSHOT by Gerrygames
02:06:39 [信息] Loaded plugin reconnect_yaml version git:reconnect_yaml:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [信息] Loaded plugin cmd_find version git:cmd_find:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [信息] Loaded plugin cmd_server version git:cmd_server:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [信息] Loaded plugin cmd_alert version git:cmd_alert:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [信息] Loaded plugin cmd_send version git:cmd_send:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [信息] Loaded plugin ViaBackwards version 3.0.0-SNAPSHOT by Matsv, KennyTV, Gerrygames, creeper123123321, ForceUpdate1
02:06:39 [信息] Loaded plugin cmd_list version git:cmd_list:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [警告] Forced host server pvp is not defined
02:06:39 [信息] [ViaVersion] Loading 1.12.2 -> 1.13 mappings...
02:06:39 [信息] [ViaVersion] Loading 1.13.2 -> 1.14 mappings...
02:06:39 [信息] [ViaVersion] Loading 1.14.4 -> 1.15 mappings...
02:06:39 [信息] [ViaVersion] Loading 1.15 -> 1.16 mappings...
02:06:39 [信息] Enabled plugin ViaVersion version 3.0.0-SNAPSHOT by _MylesC, creeper123123321, Gerrygames, KennyTV, Matsv
02:06:39 [信息] [ViaVersion] ViaVersion detected server version: 1.8.x(47)
02:06:39 [信息] Enabled plugin ViaRewind version 1.5.0-SNAPSHOT by Gerrygames
02:06:39 [信息] Enabled plugin reconnect_yaml version git:reconnect_yaml:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [信息] Enabled plugin cmd_find version git:cmd_find:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [信息] Enabled plugin cmd_server version git:cmd_server:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [信息] Enabled plugin cmd_alert version git:cmd_alert:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [信息] Enabled plugin cmd_send version git:cmd_send:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:39 [信息] [ViaBackwards] Loading translations...
02:06:39 [信息] [ViaBackwards] Registering protocols...
02:06:40 [信息] [ViaBackwards] Loading 1.13 -> 1.12.2 mappings...
02:06:40 [信息] Enabled plugin ViaBackwards version 3.0.0-SNAPSHOT by Matsv, KennyTV, Gerrygames, creeper123123321, ForceUpdate1
02:06:40 [信息] Enabled plugin cmd_list version git:cmd_list:1.15-SNAPSHOT:f1c32f8:1489 by SpigotMC
02:06:41 [信息] [ViaBackwards] Loading 1.14 -> 1.13.2 mappings...
02:06:41 [信息] [ViaBackwards] Loading 1.15 -> 1.14.4 mappings...
02:06:43 [信息] [ViaBackwards] Loading 1.16 -> 1.15.2 mappings...
02:06:46 [警告] [ViaVersion] There is a newer version available: 3.2.1, you're on: 3.0.0-SNAPSHOT
02:06:50 [信息] Listening on /0.0.0.0:25777
02:07:04 [信息] [Fallen_Breath,/127.0.0.1:13565] <-> InitialHandler has connected
02:07:04 [信息] [Alert] Hi Fallen_Breath
02:07:08 [信息] [Fallen_Breath] <-> ServerConnector [lobby] has connected
02:07:08 [信息] Netty is not using direct IO buffers.
02:07:26 [警告] Forced host server pvp is not defined
02:07:26 [信息] Closing listener [id: 0xff98d95d, L:/0:0:0:0:0:0:0:0:25777]
02:07:26 [信息] BungeeCord has been reloaded. This is NOT advisable and you will not be supported with any issues that arise! Please restart BungeeCord ASAP.
02:07:26 [信息] Listening on /0.0.0.0:25777
02:07:42 [信息] [Fallen_Breath] -> UpstreamBridge has disconnected
02:07:42 [信息] [Fallen_Breath] <-> DownstreamBridge <-> [lobby] has disconnected
02:07:42 [信息] [Alert] Bye Fallen_Breath
02:07:44 [信息] Command not found
02:07:46 [信息] Closing listener [id: 0x8fc98cbe, L:/0:0:0:0:0:0:0:0:25777]
02:07:46 [信息] Closing pending connections
02:07:46 [信息] Disconnecting 0 connections
02:07:47 [信息] Saving reconnect locations
02:07:47 [信息] Disabling plugins
02:07:47 [信息] Closing IO threads
02:07:49 [信息] Thank you and goodbye
'''.strip()


if __name__ == '__main__':
	unittest.main()
