import unittest

from mcdreforged.parser.impl.forge_handler import ForgeHandler


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.handler = ForgeHandler()

	def test_0_general(self):
		self.assertEqual(self.handler.get_name(), 'forge_handler')
		info = self.handler.parse_server_stdout('[00:53:00] [modloading-worker-9/INFO] [ne.mi.co.ForgeMod/FORGEMOD]: Forge mod loading, version 31.1.0, for MC 1.15.2 with MCP 20200122.131323')
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual('Forge mod loading, version 31.1.0, for MC 1.15.2 with MCP 20200122.131323', info.content)

		info = self.handler.parse_server_stdout('[00:53:01] [Forge Version Check/INFO] [ne.mi.fm.VersionChecker/]: [forge] Starting version check at https://files.minecraftforge.net/maven/net/minecraftforge/forge/promotions_slim.json')
		self.assertEqual('[forge] Starting version check at https://files.minecraftforge.net/maven/net/minecraftforge/forge/promotions_slim.json', info.content)

		info = self.handler.parse_server_stdout('[00:53:15] [Server thread/INFO] [minecraft/DedicatedServer]: Starting remote control listener')
		self.assertEqual('Starting remote control listener', info.content)

	def test_1_player(self):
		info = self.handler.parse_server_stdout('[00:55:36] [Server thread/INFO] [minecraft/DedicatedServer]: <Fallen_Breath> hi forge')
		self.assertEqual('Fallen_Breath', info.player)
		self.assertEqual('hi forge', info.content)

	def test_2_player_events(self):
		info = self.handler.parse_server_stdout('[00:55:26] [Server thread/INFO] [minecraft/PlayerList]: _awa_[/127.0.0.1:2115] logged in with entity id 314 at (154.2220250783568, 279.4052172954894, 134.95837063704676)')
		self.assertEqual('_awa_', self.handler.parse_player_joined(info))

		info = self.handler.parse_server_stdout('[01:00:31] [Server thread/INFO] [minecraft/DedicatedServer]: _ovo_ left the game')
		self.assertEqual('_ovo_', self.handler.parse_player_left(info))

	def test_3_server_events(self):
		info = self.handler.parse_server_stdout('[01:00:17] [Server thread/INFO] [minecraft/DedicatedServer]: Done (3.985s)! For help, type "help"')
		self.assertEqual(True, self.handler.test_server_startup_done(info))
		info = self.handler.parse_server_stdout('[01:00:17] [RCON Listener #1/INFO] [minecraft/MinecraftServer]: RCON running on 0.0.0.0:25575')
		self.assertEqual(True, self.handler.test_rcon_started(info))
		info = self.handler.parse_server_stdout('[01:01:13] [Server thread/INFO] [minecraft/MinecraftServer]: Stopping server')
		self.assertEqual(True, self.handler.test_server_stopping(info))

	def test_4_lifecycle(self):
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
[00:52:42] [main/INFO] [cp.mo.mo.Launcher/MODLAUNCHER]: ModLauncher running: args [--gameDir, ., --launchTarget, fmlserver, --fml.forgeVersion, 31.1.0, --fml.mcpVersion, 20200122.131323, --fml.mcVersion, 1.15.2, --fml.forgeGroup, net.minecraftforge, nogui]
[00:52:42] [main/INFO] [cp.mo.mo.Launcher/MODLAUNCHER]: ModLauncher 5.0.0-milestone.4+67+b1a340b starting: java version 1.8.0_241 by Oracle Corporation
[00:52:49] [main/INFO] [ne.mi.fm.lo.FixSSL/CORE]: Added Lets Encrypt root certificates as additional trust
[00:52:50] [main/INFO] [cp.mo.mo.LaunchServiceHandler/MODLAUNCHER]: Launching target 'fmlserver' with arguments [--gameDir, ., nogui]
[00:52:59] [main/WARN] [minecraft/Commands]: Ambiguity between arguments [teleport, destination] and [teleport, targets] with inputs: [Player, 0123, @e, dd12be42-52a9-4a91-a8a1-11c01849e498]
[00:52:59] [main/WARN] [minecraft/Commands]: Ambiguity between arguments [teleport, location] and [teleport, destination] with inputs: [0.1 -0.5 .9, 0 0 0]
[00:52:59] [main/WARN] [minecraft/Commands]: Ambiguity between arguments [teleport, location] and [teleport, targets] with inputs: [0.1 -0.5 .9, 0 0 0]
[00:52:59] [main/WARN] [minecraft/Commands]: Ambiguity between arguments [teleport, targets] and [teleport, destination] with inputs: [Player, 0123, dd12be42-52a9-4a91-a8a1-11c01849e498]
[00:52:59] [main/WARN] [minecraft/Commands]: Ambiguity between arguments [teleport, targets, location] and [teleport, targets, destination] with inputs: [0.1 -0.5 .9, 0 0 0]
[00:52:59] [Server thread/INFO] [minecraft/DedicatedServer]: Starting minecraft server version 1.15.2
[00:53:00] [modloading-worker-9/INFO] [ne.mi.co.ForgeMod/FORGEMOD]: Forge mod loading, version 31.1.0, for MC 1.15.2 with MCP 20200122.131323
[00:53:00] [modloading-worker-9/INFO] [ne.mi.co.MinecraftForge/FORGE]: MinecraftForge v31.1.0 Initialized
[00:53:01] [Forge Version Check/INFO] [ne.mi.fm.VersionChecker/]: [forge] Starting version check at https://files.minecraftforge.net/maven/net/minecraftforge/forge/promotions_slim.json
[00:53:01] [Server thread/INFO] [minecraft/DedicatedServer]: Loading properties
[00:53:01] [Server thread/INFO] [minecraft/DedicatedServer]: Default game type: SURVIVAL
[00:53:01] [Server thread/INFO] [minecraft/DedicatedServer]: Generating keypair
[00:53:01] [Server thread/INFO] [minecraft/DedicatedServer]: Starting Minecraft server on *:25565
[00:53:01] [Server thread/INFO] [minecraft/NetworkSystem]: Using default channel type
[00:53:04] [Forge Version Check/INFO] [ne.mi.fm.VersionChecker/]: [forge] Found status: OUTDATED Current: 31.1.0 Target: 31.2.0
[00:53:10] [Server thread/WARN] [minecraft/DedicatedServer]: **** SERVER IS RUNNING IN OFFLINE/INSECURE MODE!
[00:53:10] [Server thread/WARN] [minecraft/DedicatedServer]: While this makes the game possible to play without internet access, it also opens up the ability for hackers to connect with any username they choose.
[00:53:10] [Server thread/WARN] [minecraft/DedicatedServer]: The server will make no attempt to authenticate usernames. Beware.
[00:53:10] [Server thread/WARN] [minecraft/DedicatedServer]: To change this, set "online-mode" to "true" in the server.properties file.
[00:53:10] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Configuration file .\world\serverconfig\forge-server.toml is not correct. Correcting
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server was corrected from null to SimpleCommentedConfig:{}
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server.removeErroringEntities was corrected from null to false
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server.removeErroringTileEntities was corrected from null to false
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server.zombieBaseSummonChance was corrected from null to 0.1
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server.dimensionUnloadQueueDelay was corrected from null to 0
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server.treatEmptyTagsAsAir was corrected from null to false
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server.fixVanillaCascading was corrected from null to false
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server.clumpingThreshold was corrected from null to 64
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server.logCascadingWorldGeneration was corrected from null to true
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server.fullBoundingBoxLadders was corrected from null to false
[00:53:11] [Server thread/WARN] [ne.mi.co.ForgeConfigSpec/CORE]: Incorrect key server.zombieBabyChance was corrected from null to 0.05
[00:53:11] [Server thread/INFO] [minecraft/DedicatedServer]: Preparing level "world"
[00:53:11] [Server thread/INFO] [minecraft/SimpleReloadableResourceManager]: Reloading ResourceManager: Default, bukkit, forge-1.15.2-31.1.0-universal.jar
[00:53:11] [Server thread/INFO] [minecraft/RecipeManager]: Loaded 6 recipes
[00:53:12] [Server thread/INFO] [minecraft/AdvancementList]: Loaded 825 advancements
[00:53:12] [Server thread/INFO] [minecraft/MinecraftServer]: Preparing start region for dimension minecraft:overworld
[00:53:13] [Server thread/INFO] [minecraft/LoggingChunkStatusListener]: Preparing spawn area: 0%
[00:53:13] [Server thread/INFO] [minecraft/LoggingChunkStatusListener]: Preparing spawn area: 0%
[00:53:13] [Server-Worker-5/INFO] [minecraft/LoggingChunkStatusListener]: Preparing spawn area: 0%
[00:53:14] [Server thread/INFO] [minecraft/LoggingChunkStatusListener]: Preparing spawn area: 0%
[00:53:14] [Server thread/INFO] [minecraft/LoggingChunkStatusListener]: Preparing spawn area: 0%
[00:53:15] [Server thread/INFO] [minecraft/LoggingChunkStatusListener]: Preparing spawn area: 83%
[00:53:15] [Server thread/INFO] [minecraft/LoggingChunkStatusListener]: Time elapsed: 2846 ms
[00:53:15] [Server thread/INFO] [minecraft/DedicatedServer]: Done (4.505s)! For help, type "help"
[00:53:15] [Server thread/INFO] [minecraft/DedicatedServer]: Starting remote control listener
[00:53:15] [RCON Listener #1/INFO] [minecraft/MinecraftServer]: RCON running on 0.0.0.0:25575
[00:53:15] [Server thread/INFO] [minecraft/ChunkManager]: ThreadedAnvilChunkStorage (DIM-1): All chunks are saved
[00:53:15] [Server thread/INFO] [minecraft/ChunkManager]: ThreadedAnvilChunkStorage (DIM1): All chunks are saved
[00:55:00] [Server thread/INFO] [minecraft/PlayerList]: Fallen_Breath[/127.0.0.1:1079] logged in with entity id 312 at (154.2220250783568, 279.4052172954894, 134.95837063704676)
[00:55:00] [Server thread/INFO] [minecraft/DedicatedServer]: Fallen_Breath joined the game
[00:55:00] [Netty Server IO #2/ERROR] [minecraft/ArgumentTypes]: Could not serialize net.minecraftforge.server.command.ModIdArgument@17e3976a (class net.minecraftforge.server.command.ModIdArgument) - will not be sent to client!
[00:55:00] [Netty Server IO #2/ERROR] [minecraft/ArgumentTypes]: Could not serialize net.minecraftforge.server.command.EnumArgument@50b19f8c (class net.minecraftforge.server.command.EnumArgument) - will not be sent to client!
[00:55:00] [Server thread/INFO] [minecraft/ServerPlayNetHandler]: Fallen_Breath lost connection: Disconnected
[00:55:00] [Server thread/INFO] [minecraft/DedicatedServer]: Fallen_Breath left the game
[00:55:00] [Server thread/INFO] [minecraft/DedicatedServer]: No player was found
[00:55:26] [Server thread/INFO] [minecraft/PlayerList]: Fallen_Breath[/127.0.0.1:2115] logged in with entity id 314 at (154.2220250783568, 279.4052172954894, 134.95837063704676)
[00:55:26] [Server thread/INFO] [minecraft/DedicatedServer]: Fallen_Breath joined the game
[00:55:26] [Netty Server IO #4/ERROR] [minecraft/ArgumentTypes]: Could not serialize net.minecraftforge.server.command.ModIdArgument@17e3976a (class net.minecraftforge.server.command.ModIdArgument) - will not be sent to client!
[00:55:26] [Netty Server IO #4/ERROR] [minecraft/ArgumentTypes]: Could not serialize net.minecraftforge.server.command.EnumArgument@50b19f8c (class net.minecraftforge.server.command.EnumArgument) - will not be sent to client!
[00:55:27] [Server thread/ERROR] [ne.mi.fm.ne.si.IndexedMessageCodec/SIMPLENET]: Received empty payload on channel fml:handshake
[00:55:36] [Server thread/INFO] [minecraft/DedicatedServer]: <Fallen_Breath> hi forge
[00:55:46] [Server thread/INFO] [minecraft/DedicatedServer]: [Fallen_Breath: Gave 1 [Acacia Button] to Fallen_Breath]
[00:55:51] [Server thread/INFO] [minecraft/DedicatedServer]: [Fallen_Breath: Stopping the server]
[00:55:51] [Server thread/INFO] [minecraft/MinecraftServer]: Stopping server
[00:55:51] [Server thread/INFO] [minecraft/MinecraftServer]: Saving players
[00:55:51] [Server thread/INFO] [minecraft/MinecraftServer]: Saving worlds
[00:55:51] [Server thread/INFO] [minecraft/MinecraftServer]: Saving chunks for level 'world'/minecraft:overworld
[00:55:51] [Server thread/INFO] [minecraft/ChunkManager]: ThreadedAnvilChunkStorage (world): All chunks are saved
[00:55:51] [Server thread/INFO] [minecraft/ChunkManager]: ThreadedAnvilChunkStorage (world): All chunks are saved
'''.strip()


if __name__ == '__main__':
	unittest.main()
