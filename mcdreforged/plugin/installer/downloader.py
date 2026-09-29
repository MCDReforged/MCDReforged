import contextlib
import dataclasses
import enum
import hashlib
import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional, Iterator, TYPE_CHECKING

from typing_extensions import TypedDict, NotRequired
from wcwidth import wcswidth

from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RText, RTextList
from mcdreforged.plugin.installer.meta_holder import ReleaseData
from mcdreforged.utils import request_utils
from mcdreforged.utils.replier import Replier
from mcdreforged.utils.types.message import MessageText

if TYPE_CHECKING:
	import requests


_MAX_DOWNLOAD_SIZE = 100 * 1024 * 1024


@dataclasses.dataclass(frozen=True)
class _DownloadChunk:
	chunk: bytes
	total_downloaded: int


class _StreamDownloadHelper:
	def __init__(self, url: str, timeout: float, max_size: int):
		self.url = url
		self.timeout = timeout
		self.max_size = max_size
		self._response: Optional['requests.Response'] = None
		self._content_length: Optional[int] = None

	def establish(self) -> Optional[int]:
		response = request_utils.get_direct(self.url, 'StreamDownloadHelper', timeout=self.timeout, stream=True)
		response.raise_for_status()
		self._response = response

		content_length = response.headers.get('content-length')
		if content_length is None:
			self._content_length = None
			return None
		try:
			self._content_length = int(content_length)
		except ValueError:
			raise ValueError('content-length header {!r} is invalid'.format(content_length))

		if self._content_length > self.max_size:
			raise ValueError('content-length {} exceeds max size {}'.format(self._content_length, self.max_size))

		return self._content_length

	def download(self) -> Iterator[_DownloadChunk]:
		if self._response is None:
			raise RuntimeError('establish() must be called before download()')

		total_downloaded = 0
		for chunk in self._response.iter_content(chunk_size=8192):
			total_downloaded += len(chunk)
			if self._content_length is not None:
				if total_downloaded > self._content_length:
					raise ValueError('read too much data, read {}, length {}'.format(total_downloaded, self._content_length))
			else:
				if total_downloaded > self.max_size:
					raise ValueError('downloaded size {} exceeds max size {}'.format(total_downloaded, self.max_size))
			yield _DownloadChunk(chunk=chunk, total_downloaded=total_downloaded)

		if self._content_length is not None and total_downloaded != self._content_length:
			raise ValueError('downloaded size {} does not match content-length {}'.format(total_downloaded, self._content_length))


class DirectDownloader:
	def __init__(self, url: str, target_path: Path, timeout: float):
		self.url = url
		self.target_path = target_path
		self.timeout = timeout

	def download(self):
		helper = _StreamDownloadHelper(url=self.url, timeout=self.timeout, max_size=_MAX_DOWNLOAD_SIZE)
		helper.establish()

		self.target_path.parent.mkdir(parents=True, exist_ok=True)
		with open(self.target_path, 'wb') as f:
			for dc in helper.download():
				f.write(dc.chunk)


def width_limited(s: str, n: int) -> MessageText:
	result = ''
	for ch in s:
		if wcswidth(new_s := result + ch) > n:
			return RText(result) + RText('...', color=RColor.gray)
		result = new_s
	return result


class ReleaseDownloader:
	class ShowProgressPolicy(enum.Enum):
		never = enum.auto()
		if_costly = enum.auto()
		full = enum.auto()

	class Aborted(Exception):
		pass

	class UrlOverrideArgs(TypedDict):
		repos_owner: NotRequired[str]
		repos_name: NotRequired[str]

	def __init__(
			self,
			release: ReleaseData, target_path: Path, replier: Replier,
			*,
			mkdir: bool = True,
			download_url_override: Optional[str] = None,
			download_url_override_kwargs: Optional[UrlOverrideArgs] = None,
			download_timeout: float = 15,
			logger: Optional[logging.Logger] = None
	):
		self.release = release
		self.target_path = target_path
		self.replier = replier
		self.mkdir = mkdir
		self.download_url_override = download_url_override
		self.download_url_override_kwargs: ReleaseDownloader.UrlOverrideArgs = download_url_override_kwargs or {}
		self.download_timeout: float = download_timeout
		self.logger = logger
		self.__download_abort_event = threading.Event()

	__REPORT_INTERVAL_SEC = 5

	def __download(self, url: str, show_progress: ShowProgressPolicy):
		self.__download_abort_event.clear()

		if self.download_url_override is not None:
			kwargs = dict(
				url=url,
				tag=self.release.tag_name,
				asset_name=self.release.file_name,
				asset_id=self.release.asset_id,
				# for repos_owner, repos_name
				**self.download_url_override_kwargs,
			)
			download_url = self.download_url_override.format(**kwargs)
			if self.logger is not None:
				self.logger.debug('Applied download overwrite with kwargs {}: {!r} -> {!r}'.format(kwargs, url, download_url))
		else:
			download_url = url

		helper = _StreamDownloadHelper(url=download_url, timeout=self.download_timeout, max_size=_MAX_DOWNLOAD_SIZE)
		content_length = helper.establish()

		if content_length is None:
			raise ValueError('content-length header is missing')
		if content_length != self.release.file_size:
			raise ValueError('content-length mismatched, expected {}, found {}'.format(self.release.file_size, content_length))
		if self.logger is not None:
			self.logger.debug('Response content length: {}'.format(content_length))

		self.__check_abort()
		has_any_report = False
		downloaded = 0

		def report():
			assert content_length is not None
			nonlocal has_any_report
			has_any_report = True

			file_name = width_limited(self.release.file_name, 50)
			percent_str = f'{100.0 * downloaded / content_length:.1f}%'
			percent_str_m = percent_str + ' ' * (len('100.0%') - len(percent_str))
			simple_msg = RTextList(file_name, ' ', percent_str)
			simple_msg_m = RTextList(file_name, ' ', percent_str_m)

			if self.replier.is_console():
				try:
					terminal_width, _ = os.get_terminal_size()
				except OSError:
					terminal_width = 0
			else:
				terminal_width = 40

			bar_max_len = terminal_width - self.replier.padding_width - len('[] ') - wcswidth(str(simple_msg_m))
			if bar_max_len >= 10:
				bar_len = min(100, bar_max_len - bar_max_len % 10)
				bar = '=' * (bar_len * downloaded // content_length)
				bar += ' ' * (bar_len - len(bar))
				self.replier.reply(RTextList(file_name, f' [{bar}] {percent_str}'))
			else:
				self.replier.reply(simple_msg)

		if show_progress == self.ShowProgressPolicy.full:
			report()

		try:
			with open(self.target_path, 'wb') as f:
				hasher = hashlib.sha256()
				last_report_time = time.time()
				for dc in helper.download():
					self.__check_abort()

					downloaded = dc.total_downloaded
					hasher.update(dc.chunk)
					f.write(dc.chunk)

					t = time.time()
					if t - last_report_time > self.__REPORT_INTERVAL_SEC or downloaded == content_length:
						if (
								show_progress == self.ShowProgressPolicy.full or
								(show_progress == self.ShowProgressPolicy.if_costly and (has_any_report or downloaded < content_length))
						):
							report()
						last_report_time = t

				if (h := hasher.hexdigest()) != self.release.file_sha256:
					raise ValueError('SHA256 mismatched, expected {}, actual {}, length {}'.format(self.release.file_sha256, h, content_length))
		except self.Aborted:
			with contextlib.suppress(OSError):
				self.target_path.unlink()

	def download(self, *, show_progress: ShowProgressPolicy = ShowProgressPolicy.never, retry_cnt: int = 2):
		if self.mkdir:
			self.target_path.parent.mkdir(parents=True, exist_ok=True)

		errors = []
		url = self.release.file_url
		for i in range(retry_cnt):
			self.__check_abort()
			if self.logger is not None:
				self.logger.debug('Download attempt {} start'.format(i + 1))
			try:
				self.__download(url, show_progress)
			except self.Aborted:
				raise
			except Exception as e:
				self.replier.reply('Download attempt {} failed, url {!r}, error: {}'.format(i + 1, url, e))
				if not self.replier.is_console() and self.logger is not None:
					self.logger.warning('PIM download attempt {} failed, url {!r}, error: {}'.format(i + 1, url, e))
				errors.append(e)
			else:
				return

		raise Exception('All download attempts failed: {}'.format(errors))

	def abort(self):
		self.__download_abort_event.set()

	def __check_abort(self):
		if self.__download_abort_event.is_set():
			raise self.Aborted()
