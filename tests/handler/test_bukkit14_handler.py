import unittest

from mcdreforged.handler.impl.bukkit14_handler import Bukkit14Handler


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.handler = Bukkit14Handler()

	def test_0_general(self):
		self.assertEqual(self.handler.get_name(), 'bukkit14_handler')
		info = self.handler.parse_server_stdout('[00:38:57] [pool-4-thread-5/INFO]: [ViaBackwards] Loading 1.13 -> 1.12.2 mappings...')
		self.assertEqual(0, info.hour)
		self.assertEqual(38, info.min)
		self.assertEqual(57, info.sec)
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual('[ViaBackwards] Loading 1.13 -> 1.12.2 mappings...', info.content)

		info = self.handler.parse_server_stdout('[00:38:57] [Server thread/INFO]: Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Other 64')
		self.assertEqual('Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Other 64', info.content)
		info = self.handler.parse_server_stdout('[00:38:57] [Server thread/INFO]: Tile Max Tick Time: 50ms Entity max Tick Time: 50ms')
		self.assertEqual('Tile Max Tick Time: 50ms Entity max Tick Time: 50ms', info.content)

	def test_1_player(self):
		info = self.handler.parse_server_stdout('[00:39:30] [Async Chat Thread - #0/INFO]: <Fallen_Breath> a test text')
		self.assertEqual('Fallen_Breath', info.player)
		self.assertEqual('a test text', info.content)
		self.assertEqual('INFO', info.logging_level)

	def test_2_player_events(self):
		info = self.handler.parse_server_stdout('[00:39:24] [Server thread/INFO]: Fallen_Breath[/127.0.0.1:13635] logged in with entity id 451 at ([world]157.89301978882165, 279.4052172954894, 137.07224455363863)')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_joined(info))

		info = self.handler.parse_server_stdout('[00:39:33] [Server thread/INFO]: Fallen_Breath left the game')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_left(info))

	def test_3_server_info(self):
		info = self.handler.parse_server_stdout('[00:38:41] [Server thread/INFO]: Starting minecraft server version 1.14.4')
		self.assertEqual('1.14.4', self.handler.parse_server_version(info))
		info = self.handler.parse_server_stdout('[00:38:42] [Server thread/INFO]: Starting Minecraft server on *:25565')
		self.assertEqual(('*', 25565), self.handler.parse_server_ip(info))

	def test_4_server_events(self):
		info = self.handler.parse_server_stdout('[00:39:13] [Server thread/INFO]: Done (17.555s)! For help, type "help"')
		self.assertEqual(True, self.handler.test_server_startup_done(info))
		info = self.handler.parse_server_stdout('[00:39:13] [RCON Listener #1/INFO]: RCON running on 0.0.0.0:25575')
		self.assertEqual(True, self.handler.test_rcon_started(info))
		info = self.handler.parse_server_stdout('[00:39:38] [Server thread/INFO]: Stopping server')
		self.assertEqual(True, self.handler.test_server_stopping(info))

	def test_5_lifecycle(self):
		for line in TEXT.splitlines():
			info = self.handler.parse_server_stdout(line)
			# no exception
			if not info.is_player:
				self.assertEqual(line.split(']: ', 1)[1], info.content)
			self.assertIn(info.logging_level, {'INFO', 'WARN', 'ERROR'})


TEXT = r'''
[00:38:41] [Server thread/INFO]: Starting minecraft server version 1.14.4
[00:38:41] [Server thread/INFO]: Loading properties
[00:38:41] [Server thread/INFO]: This server is running CraftBukkit version git-Spigot-9de398a-9c887d4 (MC: 1.14.4) (Implementing API version 1.14.4-R0.1-SNAPSHOT)
[00:38:41] [Server thread/INFO]: Debug logging is disabled
[00:38:41] [Server thread/INFO]: Server Ping Player Sample Count: 12
[00:38:41] [Server thread/INFO]: Using 4 threads for Netty based IO
[00:38:41] [Server thread/INFO]: Default game type: SURVIVAL
[00:38:41] [Server thread/INFO]: Generating keypair
[00:38:42] [Server thread/INFO]: Starting Minecraft server on *:25565
[00:38:42] [Server thread/INFO]: Using default channel type
[00:38:54] [Server thread/INFO]: [ViaVersion] Loading ViaVersion v3.0.0-SNAPSHOT
[00:38:54] [Server thread/INFO]: [ViaVersion] ViaVersion 3.0.0-SNAPSHOT is now loaded, injecting!
[00:38:54] [pool-4-thread-1/INFO]: [ViaVersion] Loading 1.12.2 -> 1.13 mappings...
[00:38:55] [pool-4-thread-2/INFO]: [ViaVersion] Loading 1.13.2 -> 1.14 mappings...
[00:38:55] [pool-4-thread-3/INFO]: [ViaVersion] Loading 1.14.4 -> 1.15 mappings...
[00:38:56] [pool-4-thread-4/INFO]: [ViaVersion] Loading 1.15 -> 1.16 mappings...
[00:38:56] [Server thread/INFO]: [ViaBackwards] Loading ViaBackwards v3.0.0-SNAPSHOT
[00:38:56] [Server thread/INFO]: [ViaRewind] Loading ViaRewind v1.5.0-SNAPSHOT
[00:38:56] [Server thread/INFO]: [ViaBackwards] Enabling ViaBackwards v3.0.0-SNAPSHOT
[00:38:56] [Server thread/INFO]: [ViaBackwards] Loading translations...
[00:38:56] [Server thread/INFO]: [ViaBackwards] Registering protocols...
[00:38:56] [Server thread/INFO]: [ViaRewind] Enabling ViaRewind v1.5.0-SNAPSHOT
[00:38:56] [Server thread/WARN]: **** SERVER IS RUNNING IN OFFLINE/INSECURE MODE!
[00:38:56] [Server thread/WARN]: The server will make no attempt to authenticate usernames. Beware.
[00:38:56] [Server thread/WARN]: While this makes the game possible to play without internet access, it also opens up the ability for hackers to connect with any username they choose.
[00:38:56] [Server thread/WARN]: To change this, set "online-mode" to "true" in the server.properties file.
[00:38:56] [Server thread/INFO]: Preparing level "world"
[00:38:56] [Server thread/INFO]: Reloading ResourceManager: Default, bukkit
[00:38:57] [Server thread/INFO]: Loaded 6 recipes
[00:38:57] [pool-4-thread-5/INFO]: [ViaBackwards] Loading 1.13 -> 1.12.2 mappings...
[00:38:57] [Server thread/INFO]: -------- World Settings For [world] --------
[00:38:57] [Server thread/INFO]: View Distance: 10
[00:38:57] [Server thread/INFO]: Arrow Despawn Rate: 1200
[00:38:57] [Server thread/INFO]: Item Despawn Rate: 6000
[00:38:57] [Server thread/INFO]: Allow Zombie Pigmen to spawn from portal blocks: true
[00:38:57] [Server thread/INFO]: Entity Activation Range: An 32 / Mo 32 / Ra 48 / Mi 16 / Tiv true
[00:38:57] [Server thread/INFO]: Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Other 64
[00:38:57] [Server thread/INFO]: Pumpkin Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Carrot Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Tile Max Tick Time: 50ms Entity max Tick Time: 50ms
[00:38:57] [Server thread/INFO]: Custom Map Seeds:  Village: 10387312 Desert: 14357617 Igloo: 14357618 Jungle: 14357619 Swamp: 14357620 Monument: 10387313Ocean: 14357621 Shipwreck: 165745295 Slime: 987234911
[00:38:57] [Server thread/INFO]: Hopper Transfer: 8 Hopper Check: 1 Hopper Amount: 1
[00:38:57] [Server thread/INFO]: Max TNT Explosions: 100
[00:38:57] [Server thread/INFO]: Kelp Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: SweetBerry Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Bamboo Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Cocoa Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Vine Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: NetherWart Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Wheat Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Beetroot Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Potato Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Sapling Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Mushroom Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Melon Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Cane Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Cactus Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Experience Merge Radius: 3.0
[00:38:57] [Server thread/INFO]: Mob Spawn Range: 8
[00:38:57] [Server thread/INFO]: Nerfing mobs spawned from spawners: false
[00:38:57] [Server thread/INFO]: Item Merge Radius: 2.5
[00:38:57] [Server thread/INFO]: Zombie Aggressive Towards Villager: true
[00:38:57] [Server thread/INFO]: -------- World Settings For [world_nether] --------
[00:38:57] [Server thread/INFO]: View Distance: 10
[00:38:57] [Server thread/INFO]: Arrow Despawn Rate: 1200
[00:38:57] [Server thread/INFO]: Item Despawn Rate: 6000
[00:38:57] [Server thread/INFO]: Allow Zombie Pigmen to spawn from portal blocks: true
[00:38:57] [Server thread/INFO]: Experience Merge Radius: 3.0
[00:38:57] [Server thread/INFO]: Mushroom Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Beetroot Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Custom Map Seeds:  Village: 10387312 Desert: 14357617 Igloo: 14357618 Jungle: 14357619 Swamp: 14357620 Monument: 10387313Ocean: 14357621 Shipwreck: 165745295 Slime: 987234911
[00:38:57] [Server thread/INFO]: Hopper Transfer: 8 Hopper Check: 1 Hopper Amount: 1
[00:38:57] [Server thread/INFO]: Max TNT Explosions: 100
[00:38:57] [Server thread/INFO]: Tile Max Tick Time: 50ms Entity max Tick Time: 50ms
[00:38:57] [Server thread/INFO]: Kelp Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: SweetBerry Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Bamboo Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Cocoa Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Vine Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: NetherWart Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Wheat Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Potato Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Sapling Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Carrot Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Pumpkin Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Melon Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Cane Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: -------- World Settings For [world_the_end] --------
[00:38:57] [Server thread/INFO]: Allow Zombie Pigmen to spawn from portal blocks: true
[00:38:57] [Server thread/INFO]: Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Other 64
[00:38:57] [Server thread/INFO]: NetherWart Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Cocoa Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Custom Map Seeds:  Village: 10387312 Desert: 14357617 Igloo: 14357618 Jungle: 14357619 Swamp: 14357620 Monument: 10387313Ocean: 14357621 Shipwreck: 165745295 Slime: 987234911
[00:38:57] [Server thread/INFO]: Hopper Transfer: 8 Hopper Check: 1 Hopper Amount: 1
[00:38:57] [Server thread/INFO]: Max TNT Explosions: 100
[00:38:57] [Server thread/INFO]: Tile Max Tick Time: 50ms Entity max Tick Time: 50ms
[00:38:57] [Server thread/INFO]: Kelp Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: SweetBerry Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Bamboo Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Wheat Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Vine Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Potato Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Carrot Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Beetroot Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Sapling Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Pumpkin Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Mushroom Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Melon Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Cane Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Cactus Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Mob Spawn Range: 8
[00:38:57] [Server thread/INFO]: Experience Merge Radius: 3.0
[00:38:57] [Server thread/INFO]: Entity Activation Range: An 32 / Mo 32 / Ra 48 / Mi 16 / Tiv true
[00:38:57] [Server thread/INFO]: Nerfing mobs spawned from spawners: false
[00:38:57] [Server thread/INFO]: Item Despawn Rate: 6000
[00:38:57] [Server thread/INFO]: Zombie Aggressive Towards Villager: true
[00:38:57] [Server thread/INFO]: Item Merge Radius: 2.5
[00:38:57] [Server thread/INFO]: Arrow Despawn Rate: 1200
[00:38:57] [Server thread/INFO]: View Distance: 10
[00:38:57] [Server thread/INFO]: Cactus Growth Modifier: 100%
[00:38:57] [Server thread/INFO]: Mob Spawn Range: 8
[00:38:57] [Server thread/INFO]: Entity Activation Range: An 32 / Mo 32 / Ra 48 / Mi 16 / Tiv true
[00:38:57] [Server thread/INFO]: Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Other 64
[00:38:57] [Server thread/INFO]: Nerfing mobs spawned from spawners: false
[00:38:57] [Server thread/INFO]: Item Merge Radius: 2.5
[00:38:57] [Server thread/INFO]: Zombie Aggressive Towards Villager: true
[00:38:57] [Server thread/INFO]: Preparing start region for dimension 'world'/minecraft:overworld
[00:38:58] [pool-4-thread-5/INFO]: [ViaBackwards] Loading 1.14 -> 1.13.2 mappings...
[00:38:59] [pool-4-thread-2/INFO]: [ViaBackwards] Loading 1.15 -> 1.14.4 mappings...
[00:39:00] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:00] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:00] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:00] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:00] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:00] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:00] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:00] [pool-4-thread-5/INFO]: [ViaBackwards] Loading 1.16 -> 1.15.2 mappings...
[00:39:03] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:03] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:03] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:03] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:03] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:03] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:06] [Server thread/INFO]: Preparing spawn area: 47%
[00:39:06] [Server thread/INFO]: Preparing spawn area: 47%
[00:39:06] [Server thread/INFO]: Preparing spawn area: 47%
[00:39:06] [Server thread/INFO]: Preparing spawn area: 47%
[00:39:06] [Server thread/INFO]: Preparing spawn area: 47%
[00:39:06] [Server thread/INFO]: Time elapsed: 8913 ms
[00:39:06] [Server thread/INFO]: Preparing start region for dimension 'world_nether'/minecraft:the_nether
[00:39:07] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:07] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:07] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:08] [Server thread/INFO]: Preparing spawn area: 9%
[00:39:08] [Server thread/INFO]: Preparing spawn area: 21%
[00:39:09] [Server thread/INFO]: Preparing spawn area: 30%
[00:39:09] [Server thread/INFO]: Preparing spawn area: 39%
[00:39:10] [Server thread/INFO]: Preparing spawn area: 44%
[00:39:10] [Server thread/INFO]: Preparing spawn area: 54%
[00:39:11] [Server thread/INFO]: Preparing spawn area: 65%
[00:39:11] [Server thread/INFO]: Preparing spawn area: 76%
[00:39:12] [Server thread/INFO]: Preparing spawn area: 85%
[00:39:12] [Server thread/INFO]: Preparing spawn area: 95%
[00:39:12] [Server thread/INFO]: Time elapsed: 6218 ms
[00:39:12] [Server thread/INFO]: Preparing start region for dimension 'world_the_end'/minecraft:the_end
[00:39:12] [Server thread/INFO]: Preparing spawn area: 0%
[00:39:13] [Server thread/INFO]: Preparing spawn area: 26%
[00:39:13] [Server thread/INFO]: Preparing spawn area: 76%
[00:39:13] [Server thread/INFO]: Time elapsed: 1221 ms
[00:39:13] [Server thread/INFO]: [ViaVersion] Enabling ViaVersion v3.0.0-SNAPSHOT
[00:39:13] [Server thread/INFO]: Server permissions file permissions.yml is empty, ignoring it
[00:39:13] [Server thread/INFO]: Done (17.555s)! For help, type "help"
[00:39:13] [Server thread/INFO]: Starting remote control listener
[00:39:13] [RCON Listener #1/INFO]: RCON running on 0.0.0.0:25575
[00:39:13] [Server thread/INFO]: [ViaVersion] ViaVersion detected server version: 1.14.4(498)
[00:39:15] [Server thread/WARN]: [ViaVersion] There is a newer version available: 3.2.1, you're on: 3.0.0-SNAPSHOT
[00:39:24] [User Authenticator #1/INFO]: UUID of player Fallen_Breath is 85dbd009-69ed-3cc4-b6b6-ac1e6d07202e
[00:39:24] [Server thread/WARN]: Ignored advancement 'minecraft:recipes/misc/cactus_green' in progress file .\world\advancements\85dbd009-69ed-3cc4-b6b6-ac1e6d07202e.json - it doesn't exist anymore?
[00:39:24] [Server thread/ERROR]: Tried to load unrecognized recipe: minecraft:cactus_green removed now.
[00:39:24] [Server thread/ERROR]: Tried to load unrecognized recipe: minecraft:cactus_green removed now.
[00:39:24] [Server thread/INFO]: Fallen_Breath[/127.0.0.1:13635] logged in with entity id 451 at ([world]157.89301978882165, 279.4052172954894, 137.07224455363863)
[00:39:30] [Async Chat Thread - #0/INFO]: <Fallen_Breath> a test text
[00:39:33] [Server thread/INFO]: Fallen_Breath lost connection: Disconnected
[00:39:33] [Server thread/INFO]: Fallen_Breath left the game
[00:39:33] [Server thread/INFO]: No player was found
[00:39:35] [Server thread/INFO]: Unknown command. Type "/help" for help.
[00:39:38] [Server thread/INFO]: Stopping the server
[00:39:38] [Server thread/INFO]: Stopping server
[00:39:38] [Server thread/INFO]: [ViaRewind] Disabling ViaRewind v1.5.0-SNAPSHOT
[00:39:38] [Server thread/INFO]: [ViaBackwards] Disabling ViaBackwards v3.0.0-SNAPSHOT
[00:39:38] [Server thread/INFO]: [ViaVersion] Disabling ViaVersion v3.0.0-SNAPSHOT
[00:39:38] [Server thread/INFO]: [ViaVersion] ViaVersion is disabling, if this is a reload and you experience issues consider rebooting.
[00:39:38] [Server thread/INFO]: Saving players
[00:39:38] [Server thread/INFO]: Saving worlds
[00:39:38] [Server thread/INFO]: Saving chunks for level 'world'/minecraft:overworld
[00:39:39] [Server thread/INFO]: ThreadedAnvilChunkStorage (world): All chunks are saved
[00:39:39] [Server thread/INFO]: Saving chunks for level 'world_nether'/minecraft:the_nether
[00:39:40] [Server thread/INFO]: ThreadedAnvilChunkStorage (DIM-1): All chunks are saved
[00:39:40] [Server thread/INFO]: Saving chunks for level 'world_the_end'/minecraft:the_end
[00:39:40] [Server thread/INFO]: ThreadedAnvilChunkStorage (DIM1): All chunks are saved
[00:39:40] [Server thread/INFO]: ThreadedAnvilChunkStorage (world): All chunks are saved
[00:39:40] [Server thread/INFO]: ThreadedAnvilChunkStorage (DIM-1): All chunks are saved
[00:39:40] [Server thread/INFO]: ThreadedAnvilChunkStorage (DIM1): All chunks are saved
'''.strip()


if __name__ == '__main__':
	unittest.main()
