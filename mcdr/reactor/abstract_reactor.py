class AbstractReactor:
	def __init__(self, mcdr_server):
		from mcdr.mcdr_server import MCDReforgedServer
		self.mcdr_server = mcdr_server  # type: MCDReforgedServer

	def react(self, info):
		raise NotImplementedError()
