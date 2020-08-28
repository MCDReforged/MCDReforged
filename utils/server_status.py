# -*- coding: utf-8 -*-


class ServerStatus:
	RUNNING = 0
	STOPPED = 1
	PRE_STOPPED = 2
	STOPPING = 3
	__TRANSLATION_MAP = {
		RUNNING: 'server_status.running',
		STOPPING: 'server_status.stopping',
		PRE_STOPPED: 'server_status.pre_stopped',
		STOPPED: 'server_status.stopped'
	}

	@classmethod
	def translate_key(cls, status):
		return cls.__TRANSLATION_MAP[status]
