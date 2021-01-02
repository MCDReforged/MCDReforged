class AbstractReactor:
	def __init__(self, server):
		from mcdr.server import Server
		self.server = server  # type: Server

	def react(self, info):
		raise NotImplementedError()
