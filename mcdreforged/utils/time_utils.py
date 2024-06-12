import time
from typing import Optional


def format_time(fmt: str, timestamp: float) -> Optional[str]:
	if not isinstance(fmt, str):
		return None
	try:
		return time.strftime(fmt, time.localtime(timestamp))
	except (OSError, OverflowError, ValueError):
		return None
