# -*- coding: utf-8 -*-


class ServerStatus:
	RUNNING = 'server_status.running'
	STOPPING_BY_ITSELF = 'server_status.stopping_by_itself'
	STOPPING_BY_PLUGIN = 'server_status.stopping_by_plugin'
	STOPPED = 'server_status.stopped'


class ExitType:
	EXIT = 'server_status.exit'        # complete exit the program, default value
	RESTART = 'server_status.restart'  # restart MCDR but keep server process running
