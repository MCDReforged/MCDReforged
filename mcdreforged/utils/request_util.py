import urllib.error
import urllib.request
from typing import Optional


def ua(what: Optional[str] = None) -> str:
	from mcdreforged.constants import core_constant
	s = 'MCDReforged/{}'.format(core_constant.VERSION)
	if what:
		s += ' ({})'.format(what)
	return s


def get(url: str, what: str, *, timeout: Optional[float] = None, max_size: Optional[int] = None) -> bytes:
	req = urllib.request.Request(url, method='GET', headers={'User-Agent': ua(what)})
	with urllib.request.urlopen(req, timeout=timeout) as rsp:
		if max_size is None:
			buf = rsp.read()
		else:
			buf = rsp.read(max_size + 1)
			if len(buf) > max_size:
				raise ValueError('content-length too large (more than {})'.format(max_size))
		return buf
