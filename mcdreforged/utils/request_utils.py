import threading
from typing import Optional, Union, Tuple, List, Iterable

import requests

_proxy_dict = {}
_proxy_dict_lock = threading.Lock()


def set_proxies(http_proxy: Optional[str], https_proxy: Optional[str]):
	with _proxy_dict_lock:
		_proxy_dict.clear()
		if http_proxy is not None:
			_proxy_dict['http'] = http_proxy
		if https_proxy is not None:
			_proxy_dict['https'] = https_proxy


def get_proxies() -> dict:
	with _proxy_dict_lock:
		return _proxy_dict.copy()


def ua(what: Optional[str] = None) -> str:
	from mcdreforged.constants import core_constant
	s = 'MCDReforged/{}'.format(core_constant.VERSION)
	if what:
		s += ' ({})'.format(what)
	return s


def ua_header(what: str) -> dict:
	return {'User-Agent': ua(what)}


def get_direct(url: str, what: str, *, timeout: Optional[Union[float, Tuple[float, float]]] = None, stream: Optional[bool] = None) -> requests.Response:
	return requests.get(url, timeout=timeout, headers=ua_header(what), proxies=get_proxies(), stream=stream)


def get_buf(url: str, what: str, *, timeout: Optional[Union[float, Tuple[float, float]]] = None, max_size: Optional[int] = None) -> bytes:
	response = get_direct(url, what, timeout=timeout, stream=True)

	if max_size is None:
		return response.content
	else:
		buf = bytearray()
		for chunk in response.iter_content(chunk_size=4096):
			buf += chunk
			if len(buf) > max_size:
				raise ValueError('body too large, read {}, max size {}'.format(len(buf), max_size))
		return bytes(buf)


def get_buf_multi(urls: Iterable[str], what: str, *, timeout: Optional[Union[float, Tuple[float, float]]] = None, max_size: Optional[int] = None):
	errors: List[Exception] = []
	for url in urls:
		try:
			return get_buf(url, what, timeout=timeout, max_size=max_size)
		except Exception as e:
			errors.append(e)
	raise Exception('All attempts failed: {}'.format('; '.join(map(str, errors))))
