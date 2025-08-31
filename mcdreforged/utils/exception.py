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


class IllegalPluginStructure(Exception):
	pass


# When the metadata of a plugin is invalid
class BrokenMetadata(Exception):
	pass


# If the metadata of a AbstractPlugin has not been set yet
class MetadataNotSet(Exception):
	pass


# infinity join
class SelfJoinError(RuntimeError):
	pass
