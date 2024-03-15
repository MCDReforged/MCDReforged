import urllib.error
import urllib.request
from typing import Optional


def ua(what: Optional[str] = None) -> str:
	from mcdreforged.constants import core_constant
	s = 'MCDReforged/{}'.format(core_constant.VERSION)
	if what:
		s += ' ({})'.format(what)
	return s


def get(url: str, *, timeout: Optional[float] = None, max_size: Optional[int] = None) -> bytes:
	req = urllib.request.Request(url, method='GET', headers={'User-Agent': ua()})
	with urllib.request.urlopen(req, timeout=timeout) as rsp:
		if max_size is not None:
			length = int(rsp.headers.get('content-length'))
			if length > max_size:
				raise ValueError('content-length too large {} {}'.format(length, max_size))
		return rsp.read()
