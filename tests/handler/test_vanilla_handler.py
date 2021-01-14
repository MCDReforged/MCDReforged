import unittest

from mcdreforged.handler.impl.vanilla_handler import VanillaHandler


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.handler = VanillaHandler()

	def test_0_general(self):
		self.assertEqual(self.handler.get_name(), 'vanilla_handler')
		info = self.handler.parse_server_stdout('''[09:00:01] [Server thread/WARN]: Can't keep up!''')
		self.assertEqual(9, info.hour)
		self.assertEqual(0, info.min)
		self.assertEqual(1, info.sec)
		self.assertEqual('WARN', info.logging_level)
		self.assertEqual("Can't keep up!", info.content)

		info = self.handler.parse_server_stdout('[19:50:40] [main/INFO]: Loaded 0 recipes')
		self.assertEqual(19, info.hour)
		self.assertEqual(50, info.min)
		self.assertEqual(40, info.sec)
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual('Loaded 0 recipes', info.content)

		self.assertRaises(Exception, self.handler.parse_server_stdout, '[00:11:34 INFO]: Preparing level "world"')  # bukkit thing

	def test_1_player(self):
		info = self.handler.parse_server_stdout('[09:00:00] [Server thread/INFO]: <Steve> Hello')
		self.assertEqual('Steve', info.player)
		self.assertEqual('Hello', info.content)
		self.assertEqual(True, info.is_user)
		self.assertEqual(True, info.is_player)
		self.assertEqual(True, info.is_from_server)
		info = self.handler.parse_server_stdout('[09:00:00] [Server thread/INFO]: <Steve> <Alex> !!ping')
		self.assertEqual('Steve', info.player)
		self.assertEqual('<Alex> !!ping', info.content)

		self.assertEqual(None, self.handler.parse_server_stdout('[09:00:00] [Server thread/INFO]: <Prefix Steve> Hello').player)
		self.assertEqual(None, self.handler.parse_server_stdout('[09:00:00] [Server thread/INFO]: <[Prefix]Steve> Hello').player)

	def test_2_player_events(self):
		info = self.handler.parse_server_stdout('[00:04:13] [Server thread/INFO]: Fallen_Breath[/127.0.0.1:10545] logged in with entity id 573 at (124.37274191311167, 279.4052172954894, 141.89424426399407)')
		self.assertEqual('Fallen_Breath', self.handler.parse_player_joined(info))

		info = self.handler.parse_server_stdout('[23:52:53] [Server thread/INFO]: Steve left the game')
		self.assertEqual('Steve', self.handler.parse_player_left(info))
		info = self.handler.parse_server_stdout('[23:52:53] [Server thread/INFO]: <Steve> Steve left the game')
		self.assertEqual(None, self.handler.parse_player_left(info))

	def test_3_server_events(self):
		info = self.handler.parse_server_stdout('[00:01:46] [Server thread/INFO]: Done (3.276s)! For help, type "help"')
		self.assertEqual(True, self.handler.test_server_startup_done(info))
		info = self.handler.parse_server_stdout('[00:01:46] [RCON Listener #1/INFO]: RCON running on 0.0.0.0:25575')
		self.assertEqual(True, self.handler.test_rcon_started(info))
		info = self.handler.parse_server_stdout('[00:04:34] [Server Shutdown Thread/INFO]: Stopping server')
		self.assertEqual(True, self.handler.test_server_stopping(info))

	def test_4_lifecycle(self):
		for line in TEXT.splitlines():
			info = self.handler.parse_server_stdout(line)
			# no exception
			self.assertEqual(line.split(']: ', 1)[1], info.content)
			self.assertIn(info.logging_level, {'INFO', 'WARN'})


TEXT = '''
[19:50:40] [main/WARN]: Ambiguity between arguments [teleport, destination] and [teleport, targets] with inputs: [Player, 0123, @e, dd12be42-52a9-4a91-a8a1-11c01849e498]
[19:50:40] [main/WARN]: Ambiguity between arguments [teleport, location] and [teleport, destination] with inputs: [0.1 -0.5 .9, 0 0 0]
[19:50:40] [main/WARN]: Ambiguity between arguments [teleport, location] and [teleport, targets] with inputs: [0.1 -0.5 .9, 0 0 0]
[19:50:40] [main/WARN]: Ambiguity between arguments [teleport, targets] and [teleport, destination] with inputs: [Player, 0123, dd12be42-52a9-4a91-a8a1-11c01849e498]
[19:50:40] [main/WARN]: Ambiguity between arguments [teleport, targets, location] and [teleport, targets, destination] with inputs: [0.1 -0.5 .9, 0 0 0]
[19:50:40] [main/INFO]: Loaded 0 recipes
[19:50:41] [main/INFO]: Loaded 0 advancements
[19:50:41] [Server thread/INFO]: Starting minecraft server version 1.13.2
[19:50:41] [Server thread/INFO]: Loading properties
[19:50:41] [Server thread/INFO]: Default game type: SURVIVAL
[19:50:41] [Server thread/INFO]: Generating keypair
[19:50:41] [Server thread/INFO]: Starting Minecraft server on *:25565
[19:50:41] [Server thread/INFO]: Using default channel type
[19:50:48] [Server thread/WARN]: **** SERVER IS RUNNING IN OFFLINE/INSECURE MODE!
[19:50:48] [Server thread/WARN]: The server will make no attempt to authenticate usernames. Beware.
[19:50:48] [Server thread/WARN]: While this makes the game possible to play without internet access, it also opens up the ability for hackers to connect with any username they choose.
[19:50:48] [Server thread/WARN]: To change this, set "online-mode" to "true" in the server.properties file.
[19:50:48] [Server thread/INFO]: Preparing level "world"
[19:50:48] [Server thread/INFO]: Reloading ResourceManager: Default
[19:50:50] [Server thread/INFO]: Loaded 524 recipes
[19:50:51] [Server thread/INFO]: Loaded 571 advancements
[19:50:51] [Server thread/INFO]: Preparing start region for dimension minecraft:overworld
[19:50:51] [Server thread/INFO]: Preparing spawn area: 4%
[19:50:51] [Server thread/INFO]: Preparing spawn area: 8%
[19:50:51] [Server thread/WARN]: Keeping entity minecraft:drowned that already exists with UUID b244cf5e-d6ac-4652-800a-af010b167978
[19:50:51] [Server thread/INFO]: Preparing spawn area: 12%
[19:50:51] [Server thread/INFO]: Preparing spawn area: 16%
[19:50:51] [Server thread/INFO]: Preparing spawn area: 20%
[19:50:51] [Server thread/INFO]: Preparing spawn area: 24%
[19:50:51] [Server thread/INFO]: Preparing spawn area: 28%
[19:50:51] [Server thread/INFO]: Preparing spawn area: 32%
[19:50:51] [Server thread/INFO]: Preparing spawn area: 36%
[19:50:51] [Server thread/WARN]: Keeping entity minecraft:cod that already exists with UUID 316e2086-6c81-40f7-b43a-27723470d3ff
[19:50:51] [Server thread/INFO]: Preparing spawn area: 40%
[19:50:51] [Server thread/WARN]: Keeping entity minecraft:creeper that already exists with UUID 0d3b290e-be4a-4c36-be77-0452cfad1b28
[19:50:51] [Server thread/INFO]: Preparing spawn area: 44%
[19:50:51] [Server thread/INFO]: Preparing spawn area: 48%
[19:50:51] [Server thread/WARN]: Keeping entity minecraft:sheep that already exists with UUID 5c6d2f48-fed3-479d-a26b-4b9873f5c91c
[19:50:51] [Server thread/INFO]: Preparing spawn area: 52%
[19:50:52] [Server thread/WARN]: Keeping entity minecraft:skeleton that already exists with UUID c8da66b8-bbb8-4569-87be-edafd9e8de5c
[19:50:52] [Server thread/WARN]: Keeping entity minecraft:bat that already exists with UUID 7b02e0ff-140a-434d-886c-9c0aaaedcf5f
[19:50:52] [Server thread/INFO]: Preparing spawn area: 56%
[19:50:52] [Server thread/WARN]: Keeping entity minecraft:cow that already exists with UUID 470468e2-3e3a-4f91-9867-36e4baf3d9bf
[19:50:52] [Server thread/WARN]: Keeping entity minecraft:horse that already exists with UUID e8dfe5d9-c9e5-4a16-8cb7-19164099b604
[19:50:52] [Server thread/INFO]: Preparing spawn area: 60%
[19:50:52] [Server thread/INFO]: Preparing spawn area: 64%
[19:50:52] [Server thread/WARN]: Keeping entity minecraft:chicken that already exists with UUID 5f784101-b372-43fe-be2a-8d7a813a11c5
[19:50:52] [Server thread/INFO]: Preparing spawn area: 68%
[19:50:52] [Server thread/WARN]: Keeping entity minecraft:cod that already exists with UUID aa3d24ba-402b-4952-ae15-1d7163d137ec
[19:50:52] [Server thread/INFO]: Preparing spawn area: 72%
[19:50:52] [Server thread/WARN]: Keeping entity minecraft:turtle that already exists with UUID a1417383-0264-4b56-957f-887dec27600e
[19:50:52] [Server thread/INFO]: Preparing spawn area: 76%
[19:50:52] [Server thread/INFO]: Preparing spawn area: 80%
[19:50:52] [Server thread/INFO]: Preparing spawn area: 84%
[19:50:52] [Server thread/INFO]: Preparing spawn area: 88%
[19:50:52] [Server thread/INFO]: Preparing spawn area: 92%
[19:50:52] [Server thread/INFO]: Preparing spawn area: 96%
[19:50:52] [Server thread/INFO]: Preparing spawn area: 100%
[19:50:52] [Server thread/INFO]: Time elapsed: 1152 ms
[19:50:52] [Server thread/INFO]: Done (3.355s)! For help, type "help"
[19:50:52] [Server thread/INFO]: Starting remote control listener
[19:50:52] [RCON Listener #1/INFO]: RCON running on 0.0.0.0:25575
[19:51:00] [Server thread/WARN]: Can't keep up! Is the server overloaded? Running 2332ms or 46 ticks behind
[23:52:53] [Server thread/INFO]: Fallen_Breath[/127.0.0.1:9477] logged in with entity id 574 at (97.54280240953143, 283.524569321069, 145.44209988243546)
[23:52:53] [Server thread/INFO]: Fallen_Breath joined the game
[23:54:28] [Server thread/INFO]: [Fallen_Breath: Saved the game]
[23:54:36] [Server thread/INFO]: [Fallen_Breath: Stopping the server]
[23:54:36] [Server thread/INFO]: Stopping server
[23:54:36] [Server thread/INFO]: Saving players
[23:54:36] [Server thread/INFO]: Saving worlds
[23:54:36] [Server thread/INFO]: Saving chunks for level 'world'/minecraft:the_end
[23:54:36] [Server thread/INFO]: Saving chunks for level 'world'/minecraft:overworld
[23:54:36] [Server thread/INFO]: Saving chunks for level 'world'/minecraft:the_nether
[23:54:36] [Server Shutdown Thread/INFO]: Stopping server
'''.strip()


if __name__ == '__main__':
	unittest.main()
