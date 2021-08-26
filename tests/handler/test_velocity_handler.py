import unittest

from mcdreforged.handler.impl import VelocityHandler


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.handler = VelocityHandler()

	def test_0_general(self):
		self.assertEqual(self.handler.get_name(), 'velocity_handler')
		info = self.handler.parse_server_stdout(r'[00:16:33 WARN]: Player info forwarding is disabled! All players will appear to be connecting from the proxy and will have offline-mode UUIDs.')
		self.assertEqual('WARN', info.logging_level)
		self.assertEqual(r'Player info forwarding is disabled! All players will appear to be connecting from the proxy and will have offline-mode UUIDs.', info.content)
		info = self.handler.parse_server_stdout(r'[00:16:35 INFO] [viaversion]: ViaVersion detected lowest supported version by the proxy: 1.7-1.7.5 (4)')
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual(r'ViaVersion detected lowest supported version by the proxy: 1.7-1.7.5 (4)', info.content)

	def test_1_player(self):
		# bungeecord doesn't output player chat messages
		pass

	def test_2_player_events(self):
		info = self.handler.parse_server_stdout('[00:19:07 INFO]: [connected player] Fallen_Breath (/127.0.0.1:13394) has connected')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_joined(info))
		info = self.handler.parse_server_stdout('[00:20:32 INFO]: [connected player] TestName (/127.0.0.1:13456) has disconnected')
		self.assertEqual('TestName', self.handler.parse_player_left(info))

	def test_3_server_info(self):
		# Proxy has no game version
		info = self.handler.parse_server_stdout('[00:23:40 INFO]: Listening on /[0:0:0:0:0:0:0:0]:25577')
		self.assertEqual(('[0:0:0:0:0:0:0:0]', 25577), self.handler.parse_server_address(info))

	def test_4_server_events(self):
		info = self.handler.parse_server_stdout('[00:19:04 INFO]: Done (3.11s)!')
		self.assertEqual(True, self.handler.test_server_startup_done(info))
		info = self.handler.parse_server_stdout('[00:21:40 INFO]: Shutting down the proxy...')
		self.assertEqual(True, self.handler.test_server_stopping(info))

	def test_5_lifecycle(self):
		for line in TEXT.splitlines():
			try:
				info = self.handler.parse_server_stdout(line)
			except:
				print('error when parsing line "{}"'.format(line))
				raise


TEXT = r'''
[00:23:38 INFO]: Booting up Velocity 3.0.0...
[00:23:38 INFO]: Loading localizations...
[00:23:38 INFO]: Connections will use NIO channels, Java compression, Java ciphers
[00:23:38 WARN]: Player info forwarding is disabled! All players will appear to be connecting from the proxy and will have offline-mode UUIDs.
[00:23:38 INFO]: Loading plugins...
[00:23:38 INFO]: Loaded plugin viaversion 4.0.1 by _MylesC, creeper123123321, Gerrygames, KennyTV, Matsv
[00:23:38 INFO]: Loaded plugin viabackwards 4.0.1 by Matsv, KennyTV, Gerrygames, creeper123123321, ForceUpdate1
[00:23:38 INFO]: Loaded plugin viarewind 2.0.2-SNAPSHOT by Gerrygames
[00:23:38 INFO]: Loaded 3 plugins
[00:23:39 INFO] [viaversion]: Loading 1.12 -> 1.13 mappings...
[00:23:39 INFO] [viaversion]: Loading 1.13 -> 1.13.2 mappings...
[00:23:39 INFO] [viaversion]: Loading 1.13.2 -> 1.14 mappings...
[00:23:39 INFO] [viaversion]: Loading 1.14 -> 1.15 mappings...
[00:23:39 INFO] [viaversion]: Loading 1.15 -> 1.16 mappings...
[00:23:39 INFO] [viaversion]: Loading 1.16 -> 1.16.2 mappings...
[00:23:39 INFO] [viaversion]: Replacing channel initializers; you can safely ignore the following two warnings.
[00:23:39 WARN]: The server channel initializer has been replaced by java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
[00:23:39 WARN]: The backend channel initializer has been replaced by java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
[00:23:39 ERROR]: java.io.FileNotFoundException: plugins\viabackwards\config.yml\config.yml (系统找不到指定的路径。)
[00:23:39 ERROR]: 	at java.base/java.io.FileOutputStream.open0(Native Method)
[00:23:39 ERROR]: 	at java.base/java.io.FileOutputStream.open(FileOutputStream.java:291)
[00:23:39 ERROR]: 	at java.base/java.io.FileOutputStream.<init>(FileOutputStream.java:234)
[00:23:39 ERROR]: 	at java.base/java.io.FileOutputStream.<init>(FileOutputStream.java:184)
[00:23:39 ERROR]: 	at java.base/java.io.FileWriter.<init>(FileWriter.java:96)
[00:23:39 ERROR]: 	at com.viaversion.viaversion.util.CommentStore.writeComments(CommentStore.java:178)
[00:23:39 ERROR]: 	at com.viaversion.viaversion.util.Config.saveConfig(Config.java:122)
[00:23:39 ERROR]: 	at com.viaversion.viaversion.util.Config.loadConfig(Config.java:113)
[00:23:39 ERROR]: 	at com.viaversion.viaversion.util.Config.reloadConfig(Config.java:144)
[00:23:39 ERROR]: 	at com.viaversion.viabackwards.ViaBackwardsConfig.reloadConfig(ViaBackwardsConfig.java:41)
[00:23:39 ERROR]: 	at com.viaversion.viabackwards.api.ViaBackwardsPlatform.init(ViaBackwardsPlatform.java:66)
[00:23:39 ERROR]: 	at com.viaversion.viabackwards.VelocityPlugin.lambda$onProxyStart$0(VelocityPlugin.java:56)
[00:23:39 ERROR]: 	at com.viaversion.viaversion.ViaManagerImpl.init(ViaManagerImpl.java:105)
[00:23:39 ERROR]: 	at com.viaversion.viaversion.VelocityPlugin.onProxyLateInit(VelocityPlugin.java:116)
[00:23:39 ERROR]: 	at com.viaversion.viaversion.Lmbda$1.execute(Unknown Source)
[00:23:39 ERROR]: 	at com.velocitypowered.proxy.event.UntargetedEventHandler$VoidHandler.lambda$buildHandler$0(UntargetedEventHandler.java:47)
[00:23:39 ERROR]: 	at com.velocitypowered.proxy.event.VelocityEventManager.fire(VelocityEventManager.java:587)
[00:23:39 ERROR]: 	at com.velocitypowered.proxy.event.VelocityEventManager.lambda$fire$6(VelocityEventManager.java:468)
[00:23:39 ERROR]: 	at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1130)
[00:23:39 ERROR]: 	at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:630)
[00:23:39 ERROR]: 	at java.base/java.lang.Thread.run(Thread.java:831)
[00:23:39 INFO] [viabackwards]: Loading translations...
[00:23:39 INFO] [viaversion]: Loading 1.16.2 -> 1.17 mappings...
[00:23:39 INFO] [viabackwards]: Loading 1.10 -> 1.9.4 mappings...
[00:23:39 INFO] [viabackwards]: Loading 1.11 -> 1.10 mappings...
[00:23:39 INFO] [viabackwards]: Loading 1.13.2 -> 1.13 mappings...
[00:23:39 INFO] [viabackwards]: Loading 1.13 -> 1.12 mappings...
[00:23:39 INFO] [viabackwards]: Loading 1.15 -> 1.14 mappings...
[00:23:39 INFO] [viabackwards]: Loading 1.14 -> 1.13.2 mappings...
[00:23:39 INFO] [viaversion]: ViaVersion detected lowest supported version by the proxy: 1.7-1.7.5 (4)
[00:23:39 INFO] [viaversion]: Highest supported version by the proxy: 1.17.1 (756)
[00:23:39 INFO] [viabackwards]: Loading 1.16.2 -> 1.16 mappings...
[00:23:40 INFO] [viabackwards]: Loading 1.16 -> 1.15 mappings...
[00:23:40 INFO] [viabackwards]: Loading 1.17 -> 1.16.2 mappings...
[00:23:40 INFO] [viaversion]: Finished mapping loading, shutting down loader executor!
[00:23:40 INFO]: Listening on /[0:0:0:0:0:0:0:0]:25577
[00:23:40 INFO]: Done (3.17s)!
[00:23:45 INFO]: [connected player] Fallen_Breath (/127.0.0.1:13580) has connected
[00:23:45 INFO]: [server connection] Fallen_Breath -> lobby has connected
[00:23:50 INFO]: [server connection] Fallen_Breath -> factions has connected
[00:23:50 INFO]: [server connection] Fallen_Breath -> lobby has disconnected
[00:23:52 INFO]: [connected player] Fallen_Breath (/127.0.0.1:13580) has disconnected: 您的连接发生内部错误。
[00:23:52 ERROR]: [connected player] Fallen_Breath (/127.0.0.1:13580): exception encountered in com.velocitypowered.proxy.connection.client.ClientPlaySessionHandler@51366e5
[00:23:52 INFO]: [server connection] Fallen_Breath -> factions has disconnected
'''.strip()


if __name__ == '__main__':
	unittest.main()
