import socket
import urllib.error
import urllib.request
from typing import Iterable


def get_with_retry(urls: Iterable[str]) -> bytes:
	errors = {}
	for url in urls:
		try:
			req = urllib.request.Request(url, method='GET')
			with urllib.request.urlopen(req, timeout=3) as response:
				return response.read()
		except (urllib.error.URLError, socket.error) as e:
			if isinstance(e, urllib.error.HTTPError):
				raise
			errors[url] = e
	else:
		raise urllib.error.URLError('All attempts failed: {}'.format(errors))
