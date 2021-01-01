"""
Some custom exceptions
"""


# Fail to start the server
class ServerStartError(RuntimeError):
	pass


# The function call is illegal due to some reasons
class IllegalCall(RuntimeError):
	pass


class IllegalStateError(RuntimeError):
	pass


# The server has stopped, operation is illegal
class ServerStopped(IllegalCall):
	pass
