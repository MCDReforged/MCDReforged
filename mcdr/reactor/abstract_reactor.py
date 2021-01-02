class AbstractReactor:
	def __init__(self, server):
		self.server = server

	def react(self, info):
		raise NotImplementedError()
