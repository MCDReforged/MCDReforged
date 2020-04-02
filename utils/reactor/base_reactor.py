# -*- coding: utf-8 -*-


class BaseReactor:
	def __init__(self, server):
		self.server = server

	def react(self, info):
		pass


def get_reactor(server):
	return BaseReactor(server)
