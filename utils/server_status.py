# -*- coding: utf-8 -*-


class ServerStatus:
	RUNNING = 0
	STOPPED = 1
	STOPPING = 2
	__TRANSLATION_MAP = {
		RUNNING: 'server_status.running',
		STOPPING: 'server_status.stopping',
		STOPPED: 'server_status.stopped'
	}

	@classmethod
	def translate_key(cls, status):
		return cls.__TRANSLATION_MAP[status]
