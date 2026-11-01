import signal
from typing import Union


def get_signal_name(sig: int) -> str:
	try:
		return signal.Signals(sig).name
	except ValueError:
		return f'unknown_{sig}'


def resolve_signal(sig: Union[str, int]) -> int:
	if isinstance(sig, int):
		return sig
	try:
		return signal.Signals[sig].value
	except KeyError:
		raise ValueError('signal {!r} is not available on the current platform'.format(sig)) from None
