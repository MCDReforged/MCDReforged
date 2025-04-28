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


def get_direct(
		url: str, what: str, *,
		timeout: Optional[Union[float, Tuple[float, float]]] = None,
		stream: Optional[bool] = None,
		allow_redirects: bool = True,  # GET requests are usually ok to allow redirects
) -> requests.Response:
	return requests.get(url, timeout=timeout, headers=ua_header(what), proxies=get_proxies(), stream=stream, allow_redirects=allow_redirects)


def __get_response_buf_with_size_limited(response: requests.Response, max_size: Optional[int] = None) -> bytes:
	if max_size is None:
		return response.content

	buf_list: List[bytes] = []
	len_sum = 0
	for chunk in response.iter_content(chunk_size=4096):
		buf_list.append(chunk)
		len_sum += len(chunk)
		if len_sum > max_size:
			raise ValueError('body too large, read {}, max size {}'.format(len_sum, max_size))
	return b''.join(buf_list)


def get_buf(url: str, what: str, *, timeout: Optional[Union[float, Tuple[float, float]]] = None, max_size: Optional[int] = None) -> Tuple[requests.Response, bytes]:
	response = get_direct(url, what, timeout=timeout, stream=True)
	return response, __get_response_buf_with_size_limited(response, max_size=max_size)


def get_buf_multi(urls: Iterable[str], what: str, *, timeout: Optional[Union[float, Tuple[float, float]]] = None, max_size: Optional[int] = None) -> Tuple[requests.Response, bytes]:
	errors: List[Exception] = []
	for url in urls:
		try:
			return get_buf(url, what, timeout=timeout, max_size=max_size)
		except Exception as e:
			errors.append(e)
	raise Exception('All attempts failed: {}'.format('; '.join(map(str, errors))))


def post_json(url: str, what: str, payload: dict, *, timeout: Optional[Union[float, Tuple[float, float]]] = None, max_size: Optional[int] = None) -> Tuple[requests.Response, bytes]:
	response = requests.post(url, timeout=timeout, headers=ua_header(what), proxies=get_proxies(), json=payload, stream=True)
	return response, __get_response_buf_with_size_limited(response, max_size=max_size)
