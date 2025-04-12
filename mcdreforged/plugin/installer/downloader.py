import contextlib
import enum
import hashlib
import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional

from typing_extensions import TypedDict
from wcwidth import wcswidth

from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RText, RTextBase, RTextList
from mcdreforged.plugin.installer.meta_holder import ReleaseData
from mcdreforged.utils import request_utils
from mcdreforged.utils.replier import Replier


def width_limited(s: str, n: int) -> RTextBase:
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
		repos_owner: Optional[str]
		repos_name: Optional[str]

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
		response = request_utils.get_direct(download_url, 'ReleaseDownloader', timeout=self.download_timeout, stream=True)
		response.raise_for_status()

		content_length = response.headers.get('content-length')
		if content_length is None:
			raise ValueError('content-length header is missing')
		try:
			length = int(content_length)
		except ValueError:
			raise ValueError(f'content-length header {content_length!r} is invalid')
		if length != self.release.file_size:
			raise ValueError('content-length mismatched, expected {}, found {}'.format(length, self.release.file_size))
		if length >= 100 * 1024 * 1024:  # 100MiB
			raise ValueError('File too large ({}MiB), please download manually'.format(round(length / 1024 / 1024, 1)))
		if self.logger is not None:
			self.logger.debug('Response content length: {}'.format(length))

		self.__check_abort()

		def report():
			nonlocal has_any_report
			has_any_report = True

			file_name = width_limited(self.release.file_name, 50)
			percent_str = f'{100.0 * downloaded / length:.1f}%'
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
				bar = '=' * (bar_len * downloaded // length)
				bar += ' ' * (bar_len - len(bar))
				self.replier.reply(RTextList(file_name, f' [{bar}] {percent_str}'))
			else:
				self.replier.reply(simple_msg)

		downloaded = 0
		has_any_report = False
		if show_progress == self.ShowProgressPolicy.full:
			report()

		try:
			with open(self.target_path, 'wb') as f:
				hasher = hashlib.sha256()
				last_report_time = time.time()
				for buf in response.iter_content(chunk_size=4096):
					self.__check_abort()

					downloaded += len(buf)
					if downloaded > length:
						raise ValueError('read too much data, read {}, length {}'.format(downloaded, length))
					hasher.update(buf)
					f.write(buf)

					t = time.time()
					if t - last_report_time > self.__REPORT_INTERVAL_SEC or downloaded == length:
						if (
								show_progress == self.ShowProgressPolicy.full or
								(show_progress == self.ShowProgressPolicy.if_costly and (has_any_report or downloaded < length))
						):
							report()
						last_report_time = t

				if (h := hasher.hexdigest()) != self.release.file_sha256:
					raise ValueError('SHA256 mismatched, expected {}, actual {}, length {}'.format(self.release.file_sha256, h, length))
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
