"""
Some customize exceptions
"""


# Fail to start the server
class ServerStartError(RuntimeError):
	pass


# The function call is illegal due to some reasons
class IllegalCallError(RuntimeError):
	pass


class IllegalStateError(RuntimeError):
	pass


class ServerStopped(RuntimeError):
	pass


class IllegalPluginStructure(Exception):
	pass


# When the metadata of a plugin is invalid
class BrokenMetadata(Exception):
	pass
