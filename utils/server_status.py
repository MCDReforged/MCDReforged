# -*- coding: utf-8 -*-


class ServerStatus:
	RUNNING = 'Running'  # server running
	STOPPING_BY_ITSELF = 'Stopping by itself'  # server stops by itself
	STOPPING_BY_PLUGIN = 'Stopping by plugin'   # server stops by plugin
	STOPPED = 'Stopped'  # server and MCDR have stopped
