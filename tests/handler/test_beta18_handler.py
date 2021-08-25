import unittest

from mcdreforged.handler.impl.beta18_handler import Beta18Handler


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.handler = Beta18Handler()

	def test_0_general(self):
		self.assertEqual(self.handler.get_name(), 'beta18_handler')
		info = self.handler.parse_server_stdout('2021-01-09 01:41:09 [INFO] Starting minecraft server version Beta 1.8.1')
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual('Starting minecraft server version Beta 1.8.1', info.content)

		info = self.handler.parse_server_stdout('2021-01-09 01:41:56 [INFO] CONSOLE: Stopping the server..')
		self.assertEqual('CONSOLE: Stopping the server..', info.content)

	def test_1_player(self):
		info = self.handler.parse_server_stdout('2021-01-09 01:41:49 [INFO] <Fallen_Breath> oopsi')
		self.assertEqual('Fallen_Breath', info.player)
		self.assertEqual('oopsi', info.content)

	def test_2_player_events(self):
		info = self.handler.parse_server_stdout('2021-01-09 01:41:42 [INFO] Fallen_Breath [/127.0.0.1:10679] logged in with entity id 7777 at (-250.5, 68.62000000476837, 227.5)')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_joined(info))

		info = self.handler.parse_server_stdout('2021-01-09 01:41:52 [INFO] _somebody_ lost connection: disconnect.quitting')
		self.assertEqual('_somebody_', self.handler.parse_player_left(info))

	def test_3_server_info(self):
		info = self.handler.parse_server_stdout('2021-01-09 01:41:09 [INFO] Starting minecraft server version Beta 1.8.1')
		self.assertEqual('Beta 1.8.1', self.handler.parse_server_version(info))
		info = self.handler.parse_server_stdout('2021-01-09 01:41:09 [INFO] Starting Minecraft server on *:25565')
		self.assertEqual(('*', 25565), self.handler.parse_server_address(info))

	def test_4_server_events(self):
		info = self.handler.parse_server_stdout('2021-01-09 01:41:17 [INFO] Done (7202843100ns)! For help, type "help" or "?"')
		self.assertEqual(True, self.handler.test_server_startup_done(info))
		# No rcon

		info = self.handler.parse_server_stdout('2021-01-09 01:41:56 [INFO] Stopping server')
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
2021-01-09 01:41:09 [INFO] Starting minecraft server version Beta 1.8.1
2021-01-09 01:41:09 [INFO] Loading properties
2021-01-09 01:41:09 [INFO] Starting Minecraft server on *:25565
2021-01-09 01:41:09 [WARNING] **** SERVER IS RUNNING IN OFFLINE/INSECURE MODE!
2021-01-09 01:41:09 [WARNING] While this makes the game possible to play without internet access, it also opens up the ability for hackers to connect with any username they choose.
2021-01-09 01:41:09 [WARNING] The server will make no attempt to authenticate usernames. Beware.
2021-01-09 01:41:09 [WARNING] To change this, set "online-mode" to "true" in the server.settings file.
2021-01-09 01:41:09 [WARNING] Failed to load ban list: java.io.FileNotFoundException: banned-players.txt (系统找不到指定的文件。)
2021-01-09 01:41:09 [WARNING] Failed to load ip ban list: java.io.FileNotFoundException: banned-ips.txt (系统找不到指定的文件。)
2021-01-09 01:41:09 [WARNING] Failed to load ip ban list: java.io.FileNotFoundException: ops.txt (系统找不到指定的文件。)
2021-01-09 01:41:09 [WARNING] Failed to load white-list: java.io.FileNotFoundException: white-list.txt (系统找不到指定的文件。)
2021-01-09 01:41:09 [INFO] Preparing level "world"
2021-01-09 01:41:09 [INFO] Default game type: 0
2021-01-09 01:41:10 [INFO] Preparing start region for level 0
2021-01-09 01:41:11 [INFO] Preparing spawn area: 20%
2021-01-09 01:41:12 [INFO] Preparing spawn area: 48%
2021-01-09 01:41:13 [INFO] Preparing spawn area: 77%
2021-01-09 01:41:13 [INFO] Preparing start region for level 1
2021-01-09 01:41:14 [INFO] Preparing spawn area: 8%
2021-01-09 01:41:15 [INFO] Preparing spawn area: 36%
2021-01-09 01:41:16 [INFO] Preparing spawn area: 69%
2021-01-09 01:41:17 [INFO] Done (7202843100ns)! For help, type "help" or "?"
2021-01-09 01:41:34 [INFO] Fallen_Breath [/127.0.0.1:10679] logged in with entity id 7777 at (-250.5, 68.62000000476837, 227.5)
2021-01-09 01:41:34 [INFO] Unknown console command. Type "help" for help.
2021-01-09 01:41:34 [INFO] Unknown console command. Type "help" for help.
2021-01-09 01:41:37 [INFO] <Fallen_Breath> qwq
2021-01-09 01:41:40 [INFO] <Fallen_Breath> !!qb
2021-01-09 01:41:49 [INFO] <Fallen_Breath> oopsi
2021-01-09 01:41:52 [INFO] Fallen_Breath lost connection: disconnect.quitting
2021-01-09 01:41:56 [INFO] CONSOLE: Stopping the server..
2021-01-09 01:41:56 [INFO] Stopping server
2021-01-09 01:41:56 [INFO] Saving chunks
2021-01-09 01:41:57 [INFO] Saving chunks
'''.strip()


if __name__ == '__main__':
	unittest.main()
