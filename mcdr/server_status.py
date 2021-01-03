class ServerStatus:
	RUNNING = 0
	STOPPED = 1
	PRE_STOPPED = 2
	STOPPING = 3
	__TRANSLATION_MAP = {
		RUNNING: 'mcdr_server_status.running',
		STOPPING: 'mcdr_server_status.stopping',
		PRE_STOPPED: 'mcdr_server_status.pre_stopped',
		STOPPED: 'mcdr_server_status.stopped'
	}

	@classmethod
	def get_translate_key(cls, status):
		return cls.__TRANSLATION_MAP[status]
