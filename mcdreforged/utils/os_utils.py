import signal


def get_signal_name(sig: int) -> str:
	try:
		return signal.Signals(sig).name
	except ValueError:
		return f'unknown_{sig}'
