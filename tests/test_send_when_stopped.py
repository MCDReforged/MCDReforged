import unittest
from typing import Optional
from unittest.mock import Mock

from mcdreforged.mcdr_server import MCDReforgedServer
from mcdreforged.process.server_process_manager import ProcessNotRunning


def _make_server(*, running: bool, write_error: Optional[BaseException] = None) -> MCDReforgedServer:
	"""
	An MCDReforgedServer carrying only what send() touches.

	send() reads the configured encoding, asks whether the server is running,
	writes through the process manager and logs through the translator. Building
	a real server needs a config file and a working directory, none of which this
	behaviour depends on.
	"""
	server = object.__new__(MCDReforgedServer)
	server._MCDReforgedServer__encoding_method = 'utf8'
	server.logger = Mock()
	server._MCDReforgedServer__tr = lambda key, *args: f'{key}{args if args else ""}'
	server.is_server_running = Mock(return_value=running)
	server.process_manager = Mock()
	if write_error is not None:
		server.process_manager.write.side_effect = write_error
	return server


class SendWhenServerStopsTest(unittest.TestCase):
	def test_send_writes_while_running(self):
		server = _make_server(running=True)
		server.send('say hello')
		server.process_manager.write.assert_called_once_with(b'say hello\n')
		server.logger.warning.assert_not_called()

	def test_send_warns_when_already_stopped(self):
		server = _make_server(running=False)
		server.send('say hello')
		server.process_manager.write.assert_not_called()
		self.assertEqual(2, server.logger.warning.call_count)

	def test_a_reset_connection_during_the_write_is_reported_not_raised(self):
		# The server can close its stdin between the state check and the write,
		# which surfaces as a ConnectionResetError from the write itself.
		server = _make_server(running=True, write_error=ConnectionResetError(104, 'Connection reset by peer'))
		server.send('say hello')
		server.process_manager.write.assert_called_once()
		self.assertEqual(2, server.logger.warning.call_count)

	def test_a_broken_pipe_during_the_write_is_reported_not_raised(self):
		server = _make_server(running=True, write_error=BrokenPipeError(32, 'Broken pipe'))
		server.send('say hello')
		self.assertEqual(2, server.logger.warning.call_count)

	def test_a_process_that_vanished_during_the_write_is_reported_not_raised(self):
		server = _make_server(running=True, write_error=ProcessNotRunning('process not running'))
		server.send('say hello')
		self.assertEqual(2, server.logger.warning.call_count)

	def test_an_unrelated_write_error_still_raises(self):
		# Only a dead stdin is the reported case; anything else is a real fault
		# and must not be swallowed.
		server = _make_server(running=True, write_error=RuntimeError('boom'))
		with self.assertRaises(RuntimeError):
			server.send('say hello')

	def test_the_warning_names_the_command(self):
		server = _make_server(running=False)
		server.send('tellraw @a "hello"')
		calls = [call.args[0] for call in server.logger.warning.call_args_list]
		self.assertIn('send.send_when_stopped', calls)
		self.assertIn("send.send_when_stopped.text", calls[1])
		self.assertIn('tellraw @a "hello"', calls[1])


if __name__ == '__main__':
	unittest.main()
