import unittest

from mcdreforged.handler.impl.cat_server_handler import CatServerHandler


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.handler = CatServerHandler()

	def test_0_general(self):
		self.assertEqual(self.handler.get_name(), 'cat_server_handler')
		info = self.handler.parse_server_stdout('[01:08:29] [main/INFO]: Calling tweak class net.minecraftforge.fml.common.launcher.TerminalTweaker')
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual('Calling tweak class net.minecraftforge.fml.common.launcher.TerminalTweaker', info.content)

		info = self.handler.parse_server_stdout('[01:08:27] [main/WARN]: The coremod FMLForgePlugin (net.minecraftforge.classloading.FMLForgePlugin) is not signed!')
		self.assertEqual('The coremod FMLForgePlugin (net.minecraftforge.classloading.FMLForgePlugin) is not signed!', info.content)

	def test_1_player(self):
		info = self.handler.parse_server_stdout('[01:09:31] [Netty Server IO #2/INFO]: <Fallen_Breath> hey cat')
		self.assertEqual('Fallen_Breath', info.player)
		self.assertEqual('hey cat', info.content)

	def test_2_player_events(self):
		info = self.handler.parse_server_stdout('[01:09:11] [Server thread/INFO]: Fallen_Breath[/127.0.0.1:5165] logged in with entity id 2179 at ([world]-240.5, 66.0, 166.5)')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_joined(info))

		info = self.handler.parse_server_stdout('[01:09:36] [Server thread/INFO]: §eSteve left the game§r')  # color code warning
		self.assertEqual('Steve', self.handler.parse_player_left(info))

	def test_3_server_info(self):
		info = self.handler.parse_server_stdout('[01:08:32] [Server thread/INFO]: Starting minecraft server version 1.12.2')
		self.assertEqual('1.12.2', self.handler.parse_server_version(info))
		info = self.handler.parse_server_stdout('[01:08:34] [Server thread/INFO]: Starting Minecraft server on *:25565')
		self.assertEqual(('*', 25565), self.handler.parse_server_address(info))

	def test_4_server_events(self):
		info = self.handler.parse_server_stdout('[01:08:59] [Server thread/INFO]: Done (17.241s)! For help, type "help" or "?"')
		self.assertEqual(True, self.handler.test_server_startup_done(info))
		info = self.handler.parse_server_stdout('[01:08:59] [RCON Listener #1/INFO]: RCON running on 0.0.0.0:25575')
		self.assertEqual(True, self.handler.test_rcon_started(info))
		info = self.handler.parse_server_stdout('[01:09:38] [Server thread/INFO]: Stopping server')
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
[01:08:27] [main/INFO]: Loading tweak class name net.minecraftforge.fml.common.launcher.FMLServerTweaker
[01:08:27] [main/INFO]: Using primary tweak class name net.minecraftforge.fml.common.launcher.FMLServerTweaker
[01:08:27] [main/INFO]: Forge Mod Loader version 14.23.5.2855 for Minecraft 1.12.2 loading
[01:08:27] [main/WARN]: The coremod CatCorePlugin (catserver.server.CatCorePlugin) is not signed!
[01:08:27] [main/INFO]: Calling tweak class net.minecraftforge.fml.common.launcher.FMLInjectionAndSortingTweaker
[01:08:29] [main/INFO]: Calling tweak class net.minecraftforge.fml.common.launcher.FMLDeobfTweaker
[01:08:32] [Server thread/INFO]: Starting minecraft server version 1.12.2
[01:08:29] [main/INFO]: Launching wrapped minecraft {net.minecraft.server.MinecraftServer}
[01:08:29] [main/INFO]: Calling tweak class net.minecraftforge.fml.common.launcher.TerminalTweaker
[01:08:29] [main/INFO]: Calling tweak class net.minecraftforge.fml.relauncher.CoreModManager$FMLPluginWrapper
[01:08:29] [main/INFO]: Loading tweak class name net.minecraftforge.fml.common.launcher.TerminalTweaker
[01:08:29] [main/INFO]: Calling tweak class net.minecraftforge.fml.relauncher.CoreModManager$FMLPluginWrapper
[01:08:27] [main/INFO]: Calling tweak class net.minecraftforge.fml.relauncher.CoreModManager$FMLPluginWrapper
[01:08:27] [main/INFO]: Calling tweak class net.minecraftforge.fml.common.launcher.FMLInjectionAndSortingTweaker
[01:08:27] [main/INFO]: Loading tweak class name net.minecraftforge.fml.common.launcher.FMLDeobfTweaker
[01:08:27] [main/INFO]: Loading tweak class name net.minecraftforge.fml.common.launcher.FMLInjectionAndSortingTweaker
[01:08:27] [main/WARN]: The coremod FMLForgePlugin (net.minecraftforge.classloading.FMLForgePlugin) is not signed!
[01:08:27] [main/INFO]: Searching blabla\mods for mods
[01:08:27] [main/WARN]: The coremod FMLCorePlugin (net.minecraftforge.fml.relauncher.FMLCorePlugin) is not signed!
[01:08:27] [main/INFO]: Calling tweak class net.minecraftforge.fml.common.launcher.FMLServerTweaker
[01:08:27] [main/INFO]: Java is Java HotSpot(TM) 64-Bit Server VM, version 1.8.0_241, running on Windows 10:amd64:10.0, installed at blabla
[01:08:32] [Server thread/INFO]: MinecraftForge v14.23.5.2855 Initialized
[01:08:32] [Server thread/INFO]: Starts to replace vanilla recipe ingredients with ore ingredients.
[01:08:32] [Server thread/INFO]: Invalid recipe found with multiple oredict ingredients in the same ingredient...
[01:08:32] [Server thread/INFO]: Replaced 1227 ore ingredients
[01:08:32] [Server thread/INFO]: Searching blabla\mods for mods
[01:08:33] [Server thread/INFO]: Forge Mod Loader has identified 4 mods to load
[01:08:33] [Server thread/WARN]: Missing English translation for FML: assets/fml/lang/en_us.lang
[01:08:33] [Server thread/INFO]: Attempting connection with missing mods [minecraft, mcp, FML, forge] at CLIENT
[01:08:33] [Server thread/INFO]: Attempting connection with missing mods [minecraft, mcp, FML, forge] at SERVER
[01:08:33] [Server thread/INFO]: Processing ObjectHolder annotations
[01:08:33] [Server thread/INFO]: Found 1168 ObjectHolder annotations
[01:08:33] [Server thread/INFO]: Identifying ItemStackHolder annotations
[01:08:33] [Server thread/INFO]: Found 0 ItemStackHolder annotations
[01:08:33] [Server thread/INFO]: Configured a dormant chunk cache size of 0
[01:08:34] [Server thread/INFO]: Applying holder lookups
[01:08:34] [Server thread/INFO]: Holder lookups applied
[01:08:34] [Server thread/INFO]: Applying holder lookups
[01:08:34] [Server thread/INFO]: Holder lookups applied
[01:08:34] [Server thread/INFO]: Applying holder lookups
[01:08:34] [Server thread/INFO]: Holder lookups applied
[01:08:34] [Server thread/INFO]: Applying holder lookups
[01:08:34] [Server thread/INFO]: Holder lookups applied
[01:08:34] [Server thread/INFO]: Itemstack injection complete
[01:08:34] [Server thread/INFO]: Injecting itemstacks
[01:08:34] [Server thread/INFO]: Loading properties
[01:08:34] [Server thread/INFO]: Default game type: SURVIVAL
[01:08:34] [Server thread/INFO]: This server is running CatServer version git-CatServer-1.12.2-2a9163f (MC: 1.12.2) (Implementing API version 1.12.2-R0.1-SNAPSHOT)
[01:08:34] [Server thread/INFO]: Debug logging is enabled
[01:08:34] [Server thread/INFO]: Server Ping Player Sample Count: 12
[01:08:34] [Server thread/INFO]: Using 4 threads for Netty based IO
[01:08:34] [Server thread/INFO]: Generating keypair
[01:08:34] [Server thread/INFO]: Starting Minecraft server on *:25565
[01:08:34] [Server thread/INFO]: Using default channel type
[01:08:41] [Server thread/WARN]: **** SERVER IS RUNNING IN OFFLINE/INSECURE MODE!
[01:08:41] [Server thread/WARN]: The server will make no attempt to authenticate usernames. Beware.
[01:08:41] [Server thread/WARN]: While this makes the game possible to play without internet access, it also opens up the ability for hackers to connect with any username they choose.
[01:08:41] [Server thread/WARN]: To change this, set "online-mode" to "true" in the server.properties file.
[01:08:41] [Server thread/INFO]: Applying holder lookups
[01:08:41] [Server thread/INFO]: Holder lookups applied
[01:08:41] [Server thread/INFO]: Injecting itemstacks
[01:08:41] [Server thread/INFO]: Itemstack injection complete
[01:08:41] [Server thread/INFO]: Forge Mod Loader has successfully loaded 4 mods
[01:08:41] [Server thread/INFO]: Preparing level "world"
[01:08:43] [Server thread/INFO]: [ViaVersion] Loading ViaVersion v3.0.0-SNAPSHOT
[01:08:43] [Server thread/INFO]: [ViaVersion] ViaVersion 3.0.0-SNAPSHOT is now loaded, injecting!
[01:08:44] [pool-9-thread-1/INFO]: [ViaVersion] Loading 1.12.2 -> 1.13 mappings...
[01:08:45] [pool-9-thread-2/INFO]: [ViaVersion] Loading 1.13.2 -> 1.14 mappings...
[01:08:45] [pool-9-thread-3/INFO]: [ViaVersion] Loading 1.14.4 -> 1.15 mappings...
[01:08:45] [pool-9-thread-4/INFO]: [ViaVersion] Loading 1.15 -> 1.16 mappings...
[01:08:45] [Server thread/INFO]: [ViaBackwards] Loading ViaBackwards v3.0.0-SNAPSHOT
[01:08:45] [Server thread/INFO]: [ViaRewind] Loading ViaRewind v1.5.0-SNAPSHOT
[01:08:45] [Server thread/INFO]: [ViaBackwards] Enabling ViaBackwards v3.0.0-SNAPSHOT
[01:08:45] [Server thread/INFO]: [ViaBackwards] Loading translations...
[01:08:45] [Server thread/INFO]: [ViaBackwards] Registering protocols...
[01:08:46] [pool-9-thread-5/INFO]: [ViaBackwards] Loading 1.13 -> 1.12.2 mappings...
[01:08:46] [pool-9-thread-3/INFO]: [ViaBackwards] Loading 1.14 -> 1.13.2 mappings...
[01:08:47] [pool-9-thread-5/INFO]: [ViaBackwards] Loading 1.15 -> 1.14.4 mappings...
[01:08:47] [Server thread/INFO]: [ViaRewind] Enabling ViaRewind v1.5.0-SNAPSHOT
[01:08:47] [pool-9-thread-2/INFO]: [ViaBackwards] Loading 1.16 -> 1.15.2 mappings...
[01:08:48] [Server thread/INFO]: -------- World Settings For [world] --------
[01:08:48] [Server thread/INFO]: Custom Map Seeds:  Village: 10387312 Feature: 14357617 Monument: 10387313 Slime: 987234911
[01:08:48] [Server thread/INFO]: Allow Zombie Pigmen to spawn from portal blocks: true
[01:08:48] [Server thread/INFO]: Zombie Aggressive Towards Villager: true
[01:08:48] [Server thread/INFO]: Arrow Despawn Rate: 1200
[01:08:48] [Server thread/INFO]: Item Despawn Rate: 6000
[01:08:48] [Server thread/INFO]: Nerfing mobs spawned from spawners: false
[01:08:48] [Server thread/INFO]: Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Other 64
[01:08:48] [Server thread/INFO]: Item Merge Radius: 2.5
[01:08:48] [Server thread/INFO]: Experience Merge Radius: 3.0
[01:08:48] [Server thread/INFO]: Hopper Transfer: 8 Hopper Check: 1 Hopper Amount: 1
[01:08:48] [Server thread/INFO]: Random Lighting Updates: false
[01:08:48] [Server thread/INFO]: Cactus Growth Modifier: 100%
[01:08:48] [Server thread/INFO]: Pumpkin Growth Modifier: 100%
[01:08:48] [Server thread/INFO]: Mob Spawn Range: 8
[01:08:48] [Server thread/INFO]: Tile Max Tick Time: 50ms Entity max Tick Time: 50ms
[01:08:48] [Server thread/INFO]: Max TNT Explosions: 100
[01:08:48] [Server thread/INFO]: View Distance: 10
[01:08:48] [Server thread/INFO]: Entity Activation Range: An 32 / Mo 32 / Mi 16 / Tiv true
[01:08:48] [Server thread/INFO]: Cocoa Growth Modifier: 100%
[01:08:48] [Server thread/INFO]: Vine Growth Modifier: 100%
[01:08:48] [Server thread/INFO]: NetherWart Growth Modifier: 100%
[01:08:48] [Server thread/INFO]: Wheat Growth Modifier: 100%
[01:08:48] [Server thread/INFO]: Mushroom Growth Modifier: 100%
[01:08:48] [Server thread/INFO]: Sapling Growth Modifier: 100%
[01:08:48] [Server thread/INFO]: Melon Growth Modifier: 100%
[01:08:48] [Server thread/INFO]: Structure Info Saving: true
[01:08:48] [Server thread/INFO]: Cane Growth Modifier: 100%
[01:08:48] [Server thread/INFO]: Loading dimension 0 (world) (net.minecraft.server.dedicated.DedicatedServer@20a4a4d8)
[01:08:48] [Server thread/INFO]: Loaded 488 advancements
[01:08:49] [Server thread/INFO]: -------- World Settings For [DIM-1] --------
[01:08:49] [Server thread/INFO]: Custom Map Seeds:  Village: 10387312 Feature: 14357617 Monument: 10387313 Slime: 987234911
[01:08:49] [Server thread/INFO]: Item Merge Radius: 2.5
[01:08:49] [Server thread/INFO]: Experience Merge Radius: 3.0
[01:08:49] [Server thread/INFO]: Allow Zombie Pigmen to spawn from portal blocks: true
[01:08:49] [Server thread/INFO]: Item Despawn Rate: 6000
[01:08:49] [Server thread/INFO]: Hopper Transfer: 8 Hopper Check: 1 Hopper Amount: 1
[01:08:49] [Server thread/INFO]: Cactus Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Wheat Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: View Distance: 10
[01:08:49] [Server thread/INFO]: Tile Max Tick Time: 50ms Entity max Tick Time: 50ms
[01:08:49] [Server thread/INFO]: Max TNT Explosions: 100
[01:08:49] [Server thread/INFO]: Entity Activation Range: An 32 / Mo 32 / Mi 16 / Tiv true
[01:08:49] [Server thread/INFO]: Mob Spawn Range: 8
[01:08:49] [Server thread/INFO]: Cocoa Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Vine Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Sapling Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: NetherWart Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Pumpkin Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Mushroom Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Melon Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Cane Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Structure Info Saving: true
[01:08:49] [Server thread/INFO]: Arrow Despawn Rate: 1200
[01:08:49] [Server thread/INFO]: Random Lighting Updates: false
[01:08:49] [Server thread/INFO]: Nerfing mobs spawned from spawners: false
[01:08:49] [Server thread/INFO]: Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Other 64
[01:08:49] [Server thread/INFO]: Zombie Aggressive Towards Villager: true
[01:08:49] [Server thread/INFO]: Loading dimension -1 (DIM-1) (net.minecraft.server.dedicated.DedicatedServer@20a4a4d8)
[01:08:49] [Server thread/INFO]: -------- World Settings For [DIM1] --------
[01:08:49] [Server thread/INFO]: Custom Map Seeds:  Village: 10387312 Feature: 14357617 Monument: 10387313 Slime: 987234911
[01:08:49] [Server thread/INFO]: Item Merge Radius: 2.5
[01:08:49] [Server thread/INFO]: Allow Zombie Pigmen to spawn from portal blocks: true
[01:08:49] [Server thread/INFO]: Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Other 64
[01:08:49] [Server thread/INFO]: Arrow Despawn Rate: 1200
[01:08:49] [Server thread/INFO]: Hopper Transfer: 8 Hopper Check: 1 Hopper Amount: 1
[01:08:49] [Server thread/INFO]: Sapling Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: View Distance: 10
[01:08:49] [Server thread/INFO]: Tile Max Tick Time: 50ms Entity max Tick Time: 50ms
[01:08:49] [Server thread/INFO]: Max TNT Explosions: 100
[01:08:49] [Server thread/INFO]: Entity Activation Range: An 32 / Mo 32 / Mi 16 / Tiv true
[01:08:49] [Server thread/INFO]: Mob Spawn Range: 8
[01:08:49] [Server thread/INFO]: Cocoa Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Vine Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: NetherWart Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Pumpkin Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Wheat Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Mushroom Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Melon Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Cane Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Cactus Growth Modifier: 100%
[01:08:49] [Server thread/INFO]: Structure Info Saving: true
[01:08:49] [Server thread/INFO]: Nerfing mobs spawned from spawners: false
[01:08:49] [Server thread/INFO]: Random Lighting Updates: false
[01:08:49] [Server thread/INFO]: Zombie Aggressive Towards Villager: true
[01:08:49] [Server thread/INFO]: Experience Merge Radius: 3.0
[01:08:49] [Server thread/INFO]: Item Despawn Rate: 6000
[01:08:49] [Server thread/INFO]: Loading dimension 1 (DIM1) (net.minecraft.server.dedicated.DedicatedServer@20a4a4d8)
[01:08:49] [Server thread/INFO]: Preparing start region for level 0
[01:08:50] [Server thread/INFO]: Preparing spawn area: 8%
[01:08:51] [Server thread/INFO]: Preparing spawn area: 13%
[01:08:52] [Server thread/INFO]: Preparing spawn area: 21%
[01:08:53] [Server thread/INFO]: Preparing spawn area: 33%
[01:08:54] [Server thread/INFO]: Preparing spawn area: 46%
[01:08:55] [Server thread/INFO]: Preparing spawn area: 60%
[01:08:56] [Server thread/INFO]: Preparing spawn area: 71%
[01:08:57] [Server thread/INFO]: Preparing spawn area: 82%
[01:08:58] [Server thread/INFO]: Preparing spawn area: 93%
[01:08:59] [Server thread/INFO]: [ViaVersion] Enabling ViaVersion v3.0.0-SNAPSHOT
[01:08:59] [Server thread/INFO]: Server permissions file permissions.yml is empty, ignoring it
[01:08:59] [Server thread/INFO]: Done (17.241s)! For help, type "help" or "?"
[01:08:59] [Server thread/INFO]: Starting remote control listener
[01:08:59] [RCON Listener #1/INFO]: RCON running on 0.0.0.0:25575
[01:08:59] [Server thread/INFO]: [ViaVersion] ViaVersion detected server version: 1.12.2(340)
[01:09:05] [Server thread/WARN]: [ViaVersion] There is a newer version available: 3.2.1, you're on: 3.0.0-SNAPSHOT
[01:09:11] [User Authenticator #1/INFO]: UUID of player Fallen_Breath is 85dbd009-69ed-3cc4-b6b6-ac1e6d07202e
[01:09:11] [Server thread/INFO]: Connection received without FML marker, assuming vanilla.
[01:09:11] [Server thread/INFO]: Opening channel which already seems to have a state set. This is a vanilla connection. Handshake handler will stop now
[01:09:11] [Server thread/INFO]: [Server thread] Server side vanilla connection established
[01:09:11] [Server thread/INFO]: Fallen_Breath[/127.0.0.1:5165] logged in with entity id 2179 at ([world]-240.5, 66.0, 166.5)
[01:09:12] [Server thread/INFO]: Player '[01:09:11]' cannot be found
[01:09:18] [Server thread/INFO]: Fallen_Breath issued server command: /gamemode creative
[01:09:18] [Server thread/INFO]: [Fallen_Breath: Set own game mode to Creative Mode]
[01:09:27] [Netty Server IO #2/INFO]: <Fallen_Breath> ww
[01:09:31] [Netty Server IO #2/INFO]: <Fallen_Breath> hey cat
[01:09:36] [Server thread/INFO]: Fallen_Breath lost connection: Disconnected
[01:09:36] [Server thread/INFO]: Fallen_Breath left the game
[01:09:38] [Server thread/INFO]: Stopping the server
[01:09:38] [Server thread/INFO]: Stopping server
[01:09:38] [Server thread/INFO]: [ViaRewind] Disabling ViaRewind v1.5.0-SNAPSHOT
[01:09:38] [Server thread/INFO]: [ViaBackwards] Disabling ViaBackwards v3.0.0-SNAPSHOT
[01:09:38] [Server thread/INFO]: [ViaVersion] Disabling ViaVersion v3.0.0-SNAPSHOT
[01:09:38] [Server thread/INFO]: [ViaVersion] ViaVersion is disabling, if this is a reload and you experience issues consider rebooting.
[01:09:38] [Server thread/INFO]: Saving players
[01:09:38] [Server thread/INFO]: Saving worlds
[01:09:38] [Server thread/INFO]: Saving chunks for level 'world'/overworld
[01:09:38] [Server thread/INFO]: Saving chunks for level 'DIM-1'/the_nether
[01:09:38] [Server thread/INFO]: Saving chunks for level 'DIM1'/the_end
[01:09:39] [Server thread/INFO]: Unloading dimension 0
[01:09:39] [Server thread/INFO]: Unloading dimension -1
[01:09:39] [Server thread/INFO]: Unloading dimension 1
'''.strip()


if __name__ == '__main__':
	unittest.main()
