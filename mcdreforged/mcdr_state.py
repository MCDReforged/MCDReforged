from enum import Enum, unique, Flag, auto
from typing import Iterable


@unique
class MCDReforgedFlag(Flag):
	NONE = auto()
	INTERRUPT = auto()			# ctrl-c flag
	SERVER_STARTUP = auto()		# set to True after server startup
	SERVER_RCON_READY = auto() 	# set to True after server started its rcon. used to start the rcon server
	EXIT_NATURALLY = auto()		# if MCDR exit after server stop. can be modified by plugins


class EnumStateBase(Enum):
	def in_state(self, states):
		if type(states) is type(self):
			return self is states
		elif not isinstance(states, Iterable):
			states = (states,)
		return self in states


@unique
class MCDReforgedState(EnumStateBase):
	INITIALIZING	= 'mcdr_state.initializing' 	# Just entered construction method
	INITIALIZED		= 'mcdr_state.initialized'		# Construction finished
	RUNNING			= 'mcdr_state.running'			# MCDR started and is running
	PRE_STOPPED		= 'mcdr_state.pre_stopped'		# MCDR is stopping and making some cleaning things
	STOPPED			= 'mcdr_state.stopped'			# MCDR is stopped


@unique
class ServerState(EnumStateBase):
	STOPPED		= 'server_state.stopped'		# Server is stopped
	STOPPING	= 'server_state.stopping'		# Server is being stopped by MCDR
	RUNNING		= 'server_state.running'		# Server is running
	# PRE_STOPPED	= 'server_state.pre_stopped' 	# Server is stopped, and it's going to dispatch_event SERVER_STOP

	def is_server_stopped(self):
		return self.in_state({self.STOPPED})
