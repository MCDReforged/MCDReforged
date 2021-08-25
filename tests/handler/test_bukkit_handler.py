import unittest

from mcdreforged.handler.impl.bukkit_handler import BukkitHandler


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.handler = BukkitHandler()

	def test_0_general(self):
		self.assertEqual(self.handler.get_name(), 'bukkit_handler')
		info = self.handler.parse_server_stdout('[00:11:34 INFO]: Found new data pack file/bukkit, loading it automatically')
		self.assertEqual(0, info.hour)
		self.assertEqual(11, info.min)
		self.assertEqual(34, info.sec)
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual('Found new data pack file/bukkit, loading it automatically', info.content)

		info = self.handler.parse_server_stdout('[00:11:37 INFO]: ---- Migration of old nether folder complete ----')
		self.assertEqual(0, info.hour)
		self.assertEqual(11, info.min)
		self.assertEqual(37, info.sec)
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual('---- Migration of old nether folder complete ----', info.content)

		self.assertRaises(Exception, self.handler.parse_server_stdout, '[16:56:48] [main/INFO]: Loaded 0 advancements')  # vanilla thing

	def test_1_player(self):
		info = self.handler.parse_server_stdout('[00:12:10 INFO]: <Fallen_Breath> test')
		self.assertEqual('Fallen_Breath', info.player)
		self.assertEqual('test', info.content)
		info = self.handler.parse_server_stdout('[09:00:04 INFO]: [world_nether]<Alex> hello')
		self.assertEqual('Alex', info.player)
		self.assertEqual('hello', info.content)

	def test_2_player_events(self):
		info = self.handler.parse_server_stdout('[00:11:54 INFO]: Fallen_Breath[/127.0.0.1:11115] logged in with entity id 665 at ([world]124.37274191311167, 279.4052172954894, 141.89424426399407)')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_joined(info))

		info = self.handler.parse_server_stdout('[00:12:25 INFO]: Fallen_Breath left the game')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_left(info))

	def test_3_server_info(self):
		info = self.handler.parse_server_stdout('[00:11:21 INFO]: Starting minecraft server version 1.13.2')
		self.assertEqual('1.13.2', self.handler.parse_server_version(info))
		info = self.handler.parse_server_stdout('[00:11:22 INFO]: Starting Minecraft server on *:25565')
		self.assertEqual(('*', 25565), self.handler.parse_server_address(info))

	def test_4_server_events(self):
		info = self.handler.parse_server_stdout('[00:11:46 INFO]: Done (12.080s)! For help, type "help"')
		self.assertEqual(True, self.handler.test_server_startup_done(info))
		info = self.handler.parse_server_stdout('[00:11:46 INFO]: RCON running on 0.0.0.0:25575')
		self.assertEqual(True, self.handler.test_rcon_started(info))
		info = self.handler.parse_server_stdout('[00:12:27 INFO]: Stopping server')
		self.assertEqual(True, self.handler.test_server_stopping(info))

	def test_5_lifecycle(self):
		for line in TEXT.splitlines():
			info = self.handler.parse_server_stdout(line)
			# no exception
			if not info.is_player:
				self.assertEqual(line.split(']: ', 1)[1], info.content)
			self.assertIn(info.logging_level, {'INFO', 'WARN'})


TEXT = r'''
[00:11:21 INFO]: Loaded 0 recipes
[00:11:21 INFO]: Starting minecraft server version 1.13.2
[00:11:21 INFO]: Loading properties
[00:11:21 INFO]: Default game type: SURVIVAL
[00:11:21 INFO]: Generating keypair
[00:11:22 INFO]: Starting Minecraft server on *:25565
[00:11:22 INFO]: Using default channel type
[00:11:31 INFO]: This server is running CraftBukkit version git-Bukkit-84f3da3 (MC: 1.13.2) (Implementing API version 1.13.2-R0.1-SNAPSHOT)
[00:11:33 INFO]: [ViaVersion] Loading ViaVersion v3.0.0-SNAPSHOT
[00:11:33 INFO]: [ViaVersion] ViaVersion 3.0.0-SNAPSHOT is now loaded, injecting!
[00:11:33 INFO]: [ViaVersion] Loading 1.12.2 -> 1.13 mappings...
[00:11:33 INFO]: [ViaVersion] Loading 1.13.2 -> 1.14 mappings...
[00:11:33 INFO]: [ViaVersion] Loading 1.14.4 -> 1.15 mappings...
[00:11:33 INFO]: [ViaVersion] Loading 1.15 -> 1.16 mappings...
[00:11:33 INFO]: [ViaBackwards] Loading ViaBackwards v3.0.0-SNAPSHOT
[00:11:33 INFO]: [ViaRewind] Loading ViaRewind v1.5.0-SNAPSHOT
[00:11:33 INFO]: [ViaBackwards] Enabling ViaBackwards v3.0.0-SNAPSHOT
[00:11:33 INFO]: [ViaBackwards] Loading translations...
[00:11:33 INFO]: [ViaBackwards] Registering protocols...
[00:11:34 INFO]: [ViaRewind] Enabling ViaRewind v1.5.0-SNAPSHOT
[00:11:34 WARN]: **** SERVER IS RUNNING IN OFFLINE/INSECURE MODE!
[00:11:34 WARN]: The server will make no attempt to authenticate usernames. Beware.
[00:11:34 WARN]: While this makes the game possible to play without internet access, it also opens up the ability for hackers to connect with any username they choose.
[00:11:34 WARN]: To change this, set "online-mode" to "true" in the server.properties file.
[00:11:34 INFO]: Preparing level "world"
[00:11:34 INFO]: Found new data pack file/bukkit, loading it automatically
[00:11:34 INFO]: Reloading ResourceManager: Default, bukkit
[00:11:34 INFO]: [ViaBackwards] Loading 1.13 -> 1.12.2 mappings...
[00:11:35 INFO]: [ViaBackwards] Loading 1.14 -> 1.13.2 mappings...
[00:11:36 INFO]: Loaded 524 recipes
[00:11:36 INFO]: [ViaBackwards] Loading 1.15 -> 1.14.4 mappings...
[00:11:37 INFO]: ---- Migration of old nether folder required ----
[00:11:37 INFO]: We will move this folder for you, but it will mean that you need to move it back should you wish to stop using Bukkit in the future.
[00:11:37 INFO]: Unfortunately due to the way that Minecraft implemented multiworld support in 1.6, Bukkit requires that you move your nether folder to a new location in order to operate correctly.
[00:11:37 INFO]: Attempting to move world\DIM-1 to world_nether\DIM-1...
[00:11:37 INFO]: Success! To restore nether in the future, simply move world_nether\DIM-1 to world\DIM-1
[00:11:37 INFO]: ---- Migration of old nether folder complete ----
[00:11:37 INFO]: ---- Migration of old the_end folder required ----
[00:11:37 INFO]: We will move this folder for you, but it will mean that you need to move it back should you wish to stop using Bukkit in the future.
[00:11:37 INFO]: Unfortunately due to the way that Minecraft implemented multiworld support in 1.6, Bukkit requires that you move your the_end folder to a new location in order to operate correctly.
[00:11:37 INFO]: Attempting to move world\DIM1 to world_the_end\DIM1...
[00:11:37 INFO]: Success! To restore the_end in the future, simply move world_the_end\DIM1 to world\DIM1
[00:11:37 INFO]: ---- Migration of old the_end folder complete ----
[00:11:37 INFO]: Preparing start region for level minecraft:overworld (Seed: 5139262497043506185)
[00:11:37 INFO]: Preparing spawn area: 4%
[00:11:38 INFO]: Preparing spawn area: 8%
[00:11:38 INFO]: [ViaBackwards] Loading 1.16 -> 1.15.2 mappings...
[00:11:38 INFO]: Preparing spawn area: 12%
[00:11:39 INFO]: Preparing spawn area: 92%
[00:11:39 INFO]: Preparing spawn area: 96%
[00:11:39 INFO]: Preparing start region for level minecraft:the_nether (Seed: 5139262497043506185)
[00:11:39 INFO]: Preparing spawn area: 4%
[00:11:39 INFO]: Preparing spawn area: 8%
[00:11:39 INFO]: Preparing spawn area: 12%
[00:11:39 INFO]: Preparing spawn area: 16%
[00:11:44 INFO]: Preparing spawn area: 96%
[00:11:44 INFO]: Preparing spawn area: 100%
[00:11:44 INFO]: Preparing start region for level minecraft:the_end (Seed: 5139262497043506185)
[00:11:45 INFO]: Preparing spawn area: 4%
[00:11:45 INFO]: Preparing spawn area: 8%
[00:11:46 INFO]: Preparing spawn area: 100%
[00:11:46 INFO]: Time elapsed: 8582 ms
[00:11:46 INFO]: [ViaVersion] Enabling ViaVersion v3.0.0-SNAPSHOT
[00:11:46 INFO]: [ViaVersion] You have anti-xray on in your config, since you're not using spigot it won't fix xray!
[00:11:46 INFO]: Server permissions file permissions.yml is empty, ignoring it
[00:11:46 INFO]: Done (12.080s)! For help, type "help"
[00:11:46 INFO]: Starting remote control listener
[00:11:46 INFO]: RCON running on 0.0.0.0:25575
[00:11:46 INFO]: [ViaVersion] ViaVersion detected server version: 1.13.2(404)
[00:11:53 WARN]: [ViaVersion] There is a newer version available: 3.2.1, you're on: 3.0.0-SNAPSHOT
[00:11:54 INFO]: Fallen_Breath[/127.0.0.1:11115] logged in with entity id 665 at ([world]124.37274191311167, 279.4052172954894, 141.89424426399407)
[00:11:58 INFO]: Invalid name or UUID
[00:11:58 WARN]: Can't keep up! Is the server overloaded? Running 3931ms or 78 ticks behind
[00:12:10 INFO]: <Fallen_Breath> test
[00:12:13 INFO]: <Fallen_Breath> !!qwq
[00:12:25 INFO]: Fallen_Breath lost connection: Disconnected
[00:12:25 INFO]: Fallen_Breath left the game
[00:12:27 INFO]: Stopping the server
[00:12:27 INFO]: Stopping server
[00:12:27 INFO]: [ViaRewind] Disabling ViaRewind v1.5.0-SNAPSHOT
[00:12:27 INFO]: [ViaBackwards] Disabling ViaBackwards v3.0.0-SNAPSHOT
[00:12:27 INFO]: [ViaVersion] Disabling ViaVersion v3.0.0-SNAPSHOT
[00:12:27 INFO]: [ViaVersion] ViaVersion is disabling, if this is a reload and you experience issues consider rebooting.
[00:12:27 INFO]: Saving players
[00:12:27 INFO]: Saving worlds
[00:12:27 INFO]: Saving chunks for level 'world'/minecraft:overworld
[00:12:27 INFO]: Saving chunks for level 'world_nether'/minecraft:the_nether
[00:12:27 INFO]: Saving chunks for level 'world_the_end'/minecraft:the_end
'''.strip()


if __name__ == '__main__':
	unittest.main()
