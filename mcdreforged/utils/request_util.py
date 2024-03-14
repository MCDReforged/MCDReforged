import socket
import urllib.error
import urllib.request
from typing import Iterable, Optional


def get(url: str, *, timeout: Optional[float] = None, max_size: Optional[int] = None) -> bytes:
	req = urllib.request.Request(url, method='GET', headers={'User-Agent': 'MCDReforged'})
	with urllib.request.urlopen(req, timeout=timeout) as rsp:
		if max_size is not None:
			length = int(rsp.headers.get('content-length'))
			if length > max_size:
				raise ValueError('content-length too large {} {}'.format(length, max_size))
		return rsp.read()


def get_with_retry(urls: Iterable[str]) -> bytes:
	errors = {}
	for url in urls:
		try:
			return get(url, timeout=3)
		except (urllib.error.URLError, socket.error) as e:
			if isinstance(e, urllib.error.HTTPError):
				raise
			errors[url] = e
	else:
		raise urllib.error.URLError('All attempts failed: {}'.format(errors))
