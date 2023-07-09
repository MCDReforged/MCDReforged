import unittest

from mcdreforged.mcdr_state import ServerState, MCDReforgedState


class MyTestCase(unittest.TestCase):
	def test_0_in_state(self):
		self.assertEqual(True, ServerState.STOPPED.in_state(ServerState.STOPPED))
		self.assertEqual(True, MCDReforgedState.INITIALIZING.in_state(MCDReforgedState.INITIALIZING, MCDReforgedState.RUNNING))
		self.assertEqual(False, MCDReforgedState.STOPPED.in_state(MCDReforgedState.INITIALIZING, MCDReforgedState.RUNNING))
		self.assertEqual(False, ServerState.STOPPED.in_state(MCDReforgedState.STOPPED))


if __name__ == '__main__':
	unittest.main()
