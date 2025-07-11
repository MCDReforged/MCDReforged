import unittest

from mcdreforged.handler.impl import ArclightHandler


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.handler = ArclightHandler()

	def test_0_general(self):
		self.assertEqual(self.handler.get_name(), 'arclight_handler')
		info = self.handler.parse_server_stdout("[13:35:13 INFO] [c.m.m.LaunchServiceHandler/MODLAUNCHER]: Launching target 'arclightserver' with arguments [nogui]")
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual("Launching target 'arclightserver' with arguments [nogui]", info.content)

		info = self.handler.parse_server_stdout('[13:35:44 INFO]: Time elapsed: 6274 ms')
		self.assertEqual('Time elapsed: 6274 ms', info.content)

	def test_1_player(self):
		info = self.handler.parse_server_stdout('[13:36:33 INFO]: [Not Secure] <Fallen_Breath> 123')
		self.assertEqual('Fallen_Breath', info.player)
		self.assertEqual('123', info.content)

	def test_2_player_events(self):
		info = self.handler.parse_server_stdout('[13:36:31 INFO]: Fallen_Breath[/127.0.0.1:1279] logged in with entity id 247 at (-2.5, 103.0, 4.5)')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_joined(info))

		info = self.handler.parse_server_stdout('[13:37:04 INFO]: foobar left the game')
		self.assertEqual('foobar', self.handler.parse_player_left(info))

	def test_3_server_info(self):
		info = self.handler.parse_server_stdout('[13:35:32 INFO]: Starting minecraft server version 1.20.1')
		self.assertEqual('1.20.1', self.handler.parse_server_version(info))
		info = self.handler.parse_server_stdout('[13:35:32 INFO]: Starting Minecraft server on *:25565')
		self.assertEqual(('*', 25565), self.handler.parse_server_address(info))

	def test_4_server_events(self):
		info = self.handler.parse_server_stdout('[13:35:44 INFO]: Done (8.761s)! For help, type "help"')
		self.assertEqual(True, self.handler.test_server_startup_done(info))
		info = self.handler.parse_server_stdout('[13:35:44 INFO]: RCON running on 0.0.0.0:25575')
		self.assertEqual(True, self.handler.test_rcon_started(info))
		info = self.handler.parse_server_stdout('[13:38:44 INFO]: Stopping server')
		self.assertEqual(True, self.handler.test_server_stopping(info))

	def test_5_lifecycle(self):
		for line in TEXT.splitlines():
			try:
				info = self.handler.parse_server_stdout(line)
			except Exception:
				print('error when parsing line {!r}'.format(line))
				raise
			# no exception
			if not info.is_player:
				self.assertEqual(line.split(']: ', 1)[1], info.content)


TEXT = r'''
[13:21:44 INFO] [c.m.m.Launcher/MODLAUNCHER]: ModLauncher running: args [--launchTarget, arclightserver, --fml.forgeVersion, 47.1.1, --fml.mcVersion, 1.20.1, --fml.forgeGroup, net.minecraftforge, --fml.mcpVersion, 20230612.114412, nogui]
[13:21:44 INFO] [c.m.m.Launcher/MODLAUNCHER]: ModLauncher 10.0.9+10.0.9+main.dcd20f30 starting: java version 17.0.8 by Oracle Corporation; OS Windows 10 arch amd64 version 10.0
[13:21:44 INFO]: ImmediateWindowProvider not loading because launch target is arclightserver
[13:21:44 INFO] [mixin]: SpongePowered MIXIN Subsystem Version=0.8.5 Source=union:/MCDReforged/server/libraries/org/spongepowered/mixin/0.8.5/mixin-0.8.5.jar%2399!/ Service=ModLauncher Env=S
[13:21:44 WARN]: Mod file D:\MCDReforged\server\libraries\net\minecraftforge\fmlcore\1.20.1-47.1.1\fmlcore-1.20.1-47.1.1.jar is missing mods.toml file
[13:21:44 WARN]: Mod file D:\MCDReforged\server\libraries\net\minecraftforge\javafmllanguage\1.20.1-47.1.1\javafmllanguage-1.20.1-47.1.1.jar is missing mods.toml file
[13:21:44 WARN]: Mod file D:\MCDReforged\server\libraries\net\minecraftforge\lowcodelanguage\1.20.1-47.1.1\lowcodelanguage-1.20.1-47.1.1.jar is missing mods.toml file
[13:21:44 WARN]: Mod file D:\MCDReforged\server\libraries\net\minecraftforge\mclanguage\1.20.1-47.1.1\mclanguage-1.20.1-47.1.1.jar is missing mods.toml file
[13:21:44 INFO]: No dependencies to load found. Skipping!
[13:21:46 INFO] [mixin]: Successfully loaded Mixin Connector [io.izzel.arclight.common.mod.ArclightConnector]
[13:21:46 INFO] [mixin]: Compatibility level set to JAVA_17
[13:21:46 INFO] [Arclight]: 核心 Mixin 配置已加载
[13:21:46 INFO] [Arclight]: 服务端优化 Mixin 配置已加载
[13:21:46 INFO] [c.m.m.LaunchServiceHandler/MODLAUNCHER]: Launching target 'arclightserver' with arguments [nogui]
[13:21:59 INFO] [Arclight]: Arclight Mod 已加载
[13:21:59 INFO]: Forge mod loading, version 47.1.1, for MC 1.20.1 with MCP 20230612.114412
[13:21:59 INFO]: MinecraftForge v47.1.1 Initialized
[13:21:59 INFO] [Arclight]: Arclight 事件系统已注册
[13:21:59 INFO]: [forge] Starting version check at https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json
[13:22:01 INFO]: [forge] Found status: OUTDATED Current: 47.1.1 Target: 47.2.0
[13:22:01 INFO]: Environment: authHost='https://authserver.mojang.com', accountsHost='https://api.mojang.com', sessionHost='https://sessionserver.mojang.com', servicesHost='https://api.minecraftservices.com', name='PROD'
[13:22:02 WARN]: Assets URL 'union:/MCDReforged/server/libraries/net/minecraft/server/1.20.1-20230612.114412/server-1.20.1-20230612.114412-srg.jar%23165!/assets/.mcassetsroot' uses unexpected schema
[13:22:02 WARN]: Assets URL 'union:/MCDReforged/server/libraries/net/minecraft/server/1.20.1-20230612.114412/server-1.20.1-20230612.114412-srg.jar%23165!/data/.mcassetsroot' uses unexpectedschema
[13:22:04 INFO]: Loaded 7 recipes
[13:22:04 INFO]: Loaded 1271 advancements
[13:22:05 INFO]: Starting minecraft server version 1.20.1
[13:22:05 INFO]: Loading properties
[13:22:05 INFO]: Default game type: SURVIVAL
[13:22:05 INFO]: Generating keypair
[13:22:05 INFO]: Starting Minecraft server on *:25565
[13:22:05 INFO]: Using default channel type
[13:22:05 WARN]: **** SERVER IS RUNNING IN OFFLINE/INSECURE MODE!
[13:22:05 WARN]: The server will make no attempt to authenticate usernames. Beware.
[13:22:05 WARN]: While this makes the game possible to play without internet access, it also opens up the ability for hackers to connect with any username they choose.
[13:22:05 WARN]: To change this, set "online-mode" to "true" in the server.properties file.
[13:22:05 INFO] [Minecraft]: This server is running Arclight version arclight-1.20.1-1.0.1-c3fc1d3 (MC: 1.20.1) (Implementing API version 1.20.1-R0.1-SNAPSHOT)
[13:22:06 INFO] [Arclight]: 正在向 Bukkit 注册 ...
[13:22:06 INFO] [Arclight]: 注册了 0 个材料，其中 0 个方块 0 个物品
[13:22:06 INFO] [Arclight]: 注册了 1 个新的药水效果
[13:22:06 INFO] [Arclight]: 注册了 39 个新的附魔
[13:22:06 INFO] [Arclight]: 注册了 0 个新的生物类型
[13:22:06 INFO] [Arclight]: 注册了 0 个新的村民职业
[13:22:06 INFO] [Arclight]: 注册了 0 个新的生物群系
[13:22:06 INFO] [Minecraft]: Debug logging is enabled
[13:22:06 INFO] [Minecraft]: Using 4 threads for Netty based IO
[13:22:06 INFO] [STDOUT]: Server Ping Player Sample Count: 12
[13:22:07 INFO] [Arclight]: 正在加载混淆数据 ...
[13:22:07 INFO] [Arclight]: 正在加载 Plugin Patcher ...
[13:22:07 INFO] [Arclight/CLCACHE]: Obsolete plugin class cache is cleared
[13:22:08 ERROR] [Minecraft]: Could not load 'plugins\ViaVersion-4.0.1.jar' in folder 'plugins'
[13:22:08 WARN]: Configuration file .\world12\serverconfig\forge-server.toml is not correct. Correcting
[13:22:08 WARN]: Incorrect key server was corrected from null to its default, SimpleCommentedConfig:{}.
[13:22:08 WARN]: Incorrect key server.removeErroringBlockEntities was corrected from null to its default, false.
[13:22:08 WARN]: Incorrect key server.removeErroringEntities was corrected from null to its default, false.
[13:22:08 WARN]: Incorrect key server.fullBoundingBoxLadders was corrected from null to its default, false.
[13:22:08 WARN]: Incorrect key server.zombieBaseSummonChance was corrected from null to its default, 0.1.
[13:22:08 WARN]: Incorrect key server.zombieBabyChance was corrected from null to its default, 0.05.
[13:22:08 WARN]: Incorrect key server.permissionHandler was corrected from null to its default, forge:default_handler.
[13:22:08 INFO]: Preparing level "world12"
[13:22:08 INFO] [Arclight]: 注册了 0 个新的世界类型
[13:22:09 INFO] [Minecraft]: -------- World Settings For [world12] --------
[13:22:09 INFO] [Minecraft]: Zombie Aggressive Towards Villager: true
[13:22:09 INFO] [Minecraft]: Allow Zombie Pigmen to spawn from portal blocks: true
[13:22:09 INFO] [Minecraft]: Nerfing mobs spawned from spawners: false
[13:22:09 INFO] [Minecraft]: View Distance: 10
[13:22:09 INFO] [Minecraft]: Item Merge Radius: 2.5
[13:22:09 INFO] [Minecraft]: Item Despawn Rate: 6000
[13:22:09 INFO] [Minecraft]: Simulation Distance: 10
[13:22:09 INFO] [Minecraft]: Arrow Despawn Rate: 1200 Trident Respawn Rate:1200
[13:22:09 INFO] [Minecraft]: Experience Merge Radius: 3.0
[13:22:09 INFO] [Minecraft]: Mob Spawn Range: 8
[13:22:09 INFO] [Minecraft]: Cactus Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Cane Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Melon Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Mushroom Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Pumpkin Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Sapling Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Beetroot Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Carrot Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Potato Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Wheat Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: NetherWart Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Vine Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Cocoa Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Bamboo Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: SweetBerry Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Kelp Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: TwistingVines Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: WeepingVines Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: CaveVines Growth Modifier: 100%
[13:22:09 INFO] [Minecraft]: Entity Activation Range: An 32 / Mo 32 / Ra 48 / Mi 16 / Tiv true / Isa false
[13:22:09 INFO] [Minecraft]: Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Di 128 / Other 64
[13:22:09 INFO] [Minecraft]: Custom Map Seeds:  Village: 10387312 Desert: 14357617 Igloo: 14357618 Jungle: 14357619 Swamp: 14357620 Monument: 10387313 Ocean: 14357621 Shipwreck: 165745295 End City: 10387313 Slime: 987234911 Nether: 30084232 Mansion: 10387319 Fossil: 14357921 Portal: 34222645
[13:22:09 INFO] [Minecraft]: Hopper Transfer: 8 Hopper Check: 1 Hopper Amount: 1 Hopper Can Load Chunks: false
[13:22:09 INFO] [Minecraft]: Max TNT Explosions: 100
[13:22:09 INFO] [Minecraft]: Tile Max Tick Time: 50ms Entity max Tick Time: 50ms
[13:22:15 INFO] [Minecraft]: -------- World Settings For [world12/DIM1] --------
[13:22:15 INFO] [Minecraft]: Zombie Aggressive Towards Villager: true
[13:22:15 INFO] [Minecraft]: Allow Zombie Pigmen to spawn from portal blocks: true
[13:22:15 INFO] [Minecraft]: Nerfing mobs spawned from spawners: false
[13:22:15 INFO] [Minecraft]: View Distance: 10
[13:22:15 INFO] [Minecraft]: Item Merge Radius: 2.5
[13:22:15 INFO] [Minecraft]: Item Despawn Rate: 6000
[13:22:15 INFO] [Minecraft]: Simulation Distance: 10
[13:22:15 INFO] [Minecraft]: Arrow Despawn Rate: 1200 Trident Respawn Rate:1200
[13:22:15 INFO] [Minecraft]: Experience Merge Radius: 3.0
[13:22:15 INFO] [Minecraft]: Mob Spawn Range: 8
[13:22:15 INFO] [Minecraft]: Cactus Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Cane Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Melon Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Mushroom Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Pumpkin Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Sapling Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Beetroot Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Carrot Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Potato Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Wheat Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: NetherWart Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Vine Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Cocoa Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Bamboo Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: SweetBerry Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Kelp Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: TwistingVines Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: WeepingVines Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: CaveVines Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Entity Activation Range: An 32 / Mo 32 / Ra 48 / Mi 16 / Tiv true / Isa false
[13:22:15 INFO] [Minecraft]: Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Di 128 / Other 64
[13:22:15 INFO] [Minecraft]: Custom Map Seeds:  Village: 10387312 Desert: 14357617 Igloo: 14357618 Jungle: 14357619 Swamp: 14357620 Monument: 10387313 Ocean: 14357621 Shipwreck: 165745295 End City: 10387313 Slime: 987234911 Nether: 30084232 Mansion: 10387319 Fossil: 14357921 Portal: 34222645
[13:22:15 INFO] [Minecraft]: Hopper Transfer: 8 Hopper Check: 1 Hopper Amount: 1 Hopper Can Load Chunks: false
[13:22:15 INFO] [Minecraft]: Max TNT Explosions: 100
[13:22:15 INFO] [Minecraft]: Tile Max Tick Time: 50ms Entity max Tick Time: 50ms
[13:22:15 INFO] [Minecraft]: -------- World Settings For [world12/DIM-1] --------
[13:22:15 INFO] [Minecraft]: Zombie Aggressive Towards Villager: true
[13:22:15 INFO] [Minecraft]: Allow Zombie Pigmen to spawn from portal blocks: true
[13:22:15 INFO] [Minecraft]: Nerfing mobs spawned from spawners: false
[13:22:15 INFO] [Minecraft]: View Distance: 10
[13:22:15 INFO] [Minecraft]: Item Merge Radius: 2.5
[13:22:15 INFO] [Minecraft]: Item Despawn Rate: 6000
[13:22:15 INFO] [Minecraft]: Simulation Distance: 10
[13:22:15 INFO] [Minecraft]: Arrow Despawn Rate: 1200 Trident Respawn Rate:1200
[13:22:15 INFO] [Minecraft]: Experience Merge Radius: 3.0
[13:22:15 INFO] [Minecraft]: Mob Spawn Range: 8
[13:22:15 INFO] [Minecraft]: Cactus Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Cane Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Melon Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Mushroom Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Pumpkin Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Sapling Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Beetroot Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Carrot Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Potato Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Wheat Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: NetherWart Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Vine Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Cocoa Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Bamboo Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: SweetBerry Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Kelp Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: TwistingVines Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: WeepingVines Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: CaveVines Growth Modifier: 100%
[13:22:15 INFO] [Minecraft]: Entity Activation Range: An 32 / Mo 32 / Ra 48 / Mi 16 / Tiv true / Isa false
[13:22:15 INFO] [Minecraft]: Entity Tracking Range: Pl 48 / An 48 / Mo 48 / Mi 32 / Di 128 / Other 64
[13:22:15 INFO] [Minecraft]: Custom Map Seeds:  Village: 10387312 Desert: 14357617 Igloo: 14357618 Jungle: 14357619 Swamp: 14357620 Monument: 10387313 Ocean: 14357621 Shipwreck: 165745295 End City: 10387313 Slime: 987234911 Nether: 30084232 Mansion: 10387319 Fossil: 14357921 Portal: 34222645
[13:22:15 INFO] [Minecraft]: Hopper Transfer: 8 Hopper Check: 1 Hopper Amount: 1 Hopper Can Load Chunks: false
[13:22:15 INFO] [Minecraft]: Max TNT Explosions: 100
[13:22:15 INFO] [Minecraft]: Tile Max Tick Time: 50ms Entity max Tick Time: 50ms
[13:22:15 INFO] [Minecraft]: Server permissions file permissions.yml is empty, ignoring it
[13:22:15 INFO]: Preparing start region for dimension minecraft:overworld
[13:22:16 INFO]: Preparing spawn area: 0%
[13:22:16 INFO]: Preparing spawn area: 0%
[13:22:17 INFO]: Preparing spawn area: 0%
[13:22:17 INFO]: Preparing spawn area: 0%
[13:22:18 INFO]: Preparing spawn area: 0%
[13:22:18 INFO]: Preparing spawn area: 0%
[13:22:18 INFO]: Preparing spawn area: 1%
[13:22:19 INFO]: Preparing spawn area: 3%
[13:22:19 INFO]: Preparing spawn area: 4%
[13:22:20 INFO]: Preparing spawn area: 6%
[13:22:20 ERROR]: Failed to fetch mob spawner entity at (67, -12, -2)
[13:22:20 INFO]: Preparing spawn area: 8%
[13:22:21 INFO]: Preparing spawn area: 9%
[13:22:21 INFO]: Preparing spawn area: 12%
[13:22:22 INFO]: Preparing spawn area: 13%
[13:22:22 INFO]: Preparing spawn area: 16%
[13:22:23 INFO]: Preparing spawn area: 18%
[13:22:23 INFO]: Preparing spawn area: 21%
[13:22:24 INFO]: Preparing spawn area: 22%
[13:22:24 INFO]: Preparing spawn area: 27%
[13:22:25 INFO]: Preparing spawn area: 30%
[13:22:25 INFO]: Preparing spawn area: 33%
[13:22:26 INFO]: Preparing spawn area: 35%
[13:22:26 INFO]: Preparing spawn area: 38%
[13:22:27 INFO]: Preparing spawn area: 42%
[13:22:27 INFO]: Preparing spawn area: 44%
[13:22:28 INFO]: Preparing spawn area: 48%
[13:22:28 INFO]: Preparing spawn area: 51%
[13:22:29 INFO]: Preparing spawn area: 55%
[13:22:29 INFO]: Preparing spawn area: 57%
[13:22:30 INFO]: Preparing spawn area: 62%
[13:22:30 INFO]: Preparing spawn area: 65%
[13:22:31 INFO]: Preparing spawn area: 68%
[13:22:31 INFO]: Preparing spawn area: 71%
[13:22:32 INFO]: Preparing spawn area: 75%
[13:22:32 INFO]: Preparing spawn area: 78%
[13:22:33 INFO]: Preparing spawn area: 82%
[13:22:33 INFO]: Preparing spawn area: 85%
[13:22:34 INFO]: Preparing spawn area: 87%
[13:22:34 INFO]: Preparing spawn area: 91%
[13:22:35 INFO]: Preparing spawn area: 94%
[13:22:35 INFO]: Preparing spawn area: 97%
[13:22:36 INFO]: Time elapsed: 20178 ms
[13:22:36 INFO]: Done (27.915s)! For help, type "help"
[13:22:36 INFO]: Starting remote control listener
[13:22:36 INFO]: Thread RCON Listener started
[13:22:36 INFO]: RCON running on 0.0.0.0:25575
[13:22:36 INFO]: Successfully initialized permission handler forge:default_handler
[13:22:36 INFO] [Arclight]: Forwarding forge permission[forge:default_handler] to bukkit
[13:26:10 INFO]: UUID of player Fallen_Breath is 85dbd009-69ed-3cc4-b6b6-ac1e6d07202e
[13:26:10 INFO]: Fallen_Breath[/127.0.0.1:1106] logged in with entity id 577 at (-2.5, 103.0, 4.5)
[13:26:10 INFO]: Fallen_Breath joined the game
[13:26:18 INFO]: [Not Secure] <Fallen_Breath> hello
[13:26:23 INFO]: [Not Secure] <Fallen_Breath> !!MCDR
[13:26:28 INFO]: Fallen_Breath lost connection: Disconnected
[13:26:28 INFO]: Fallen_Breath left the game
[13:26:41 INFO]: Stopping the server
[13:26:41 INFO]: Stopping server
[13:26:41 INFO]: Saving players
[13:26:41 INFO]: Saving worlds
[13:26:42 INFO]: Saving chunks for level 'ServerLevel[world12]'/minecraft:overworld
[13:26:43 INFO]: Saving chunks for level 'ServerLevel[world12/DIM1]'/minecraft:the_end
[13:26:43 INFO]: Saving chunks for level 'ServerLevel[world12/DIM-1]'/minecraft:the_nether
[13:26:43 INFO]: Thread RCON Listener stopped
'''.strip()


if __name__ == '__main__':
	unittest.main()
