# -*- coding: utf-8 -*-


class ServerStatus:
	RUNNING = 0  # server running
	STOPPING = 1  # server stops by itself
	STOPPED = 2  # server and MCDR have stopped
	RESTARTING = 3  # plugin calls a restart
