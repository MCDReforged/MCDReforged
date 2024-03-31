import hashlib
import time
from pathlib import Path
from typing import Optional

from mcdreforged.plugin.installer.meta_holder import ReleaseData
from mcdreforged.plugin.installer.replier import Replier
from mcdreforged.utils import request_util


class ReleaseDownloader:
	def __init__(
			self,
			release: ReleaseData, target_path: Path, replier: Replier,
			*,
			mkdir: bool = True,
			download_url_override: Optional[str] = None,
			download_timeout: Optional[float] = 15
	):
		self.release = release
		self.target_path = target_path
		self.replier = replier
		self.mkdir = mkdir
		self.download_url_override = download_url_override
		self.download_timeout = download_timeout

	def __download(self, url: str, show_progress: bool):
		if self.download_url_override is not None:
			download_url = self.download_url_override.format(
				url=url,
				repos_owner='',
				repos_name='',
				tag=self.release.tag_name,
				asset_name=self.release.file_name,
				asset_id=self.release.asset_id,
			)
		else:
			download_url = url
		response = request_util.get_raw(download_url, 'download', timeout=self.download_timeout, stream=True)

		length = int(response.headers.get('content-length'))
		if length != self.release.file_size:
			raise ValueError('content-length mismatched, expected {}, found {}'.format(length, self.release.file_size))
		if length >= 100 * 1024 * 1024:  # 100MiB
			raise ValueError('File too large ({}MiB), please download manually'.format(round(length / 1024 / 1024, 1)))

		def report():
			if show_progress:
				percent = 100 * downloaded / length
				bar = '=' * (50 * downloaded // length)
				bar += ' ' * (50 - len(bar))
				self.replier.reply(f'Downloading [{bar}] {percent:.1f}%')

		downloaded = 0
		report()

		with open(self.target_path, 'wb') as f:
			hasher = hashlib.sha256()
			last_report_time = time.time()
			for buf in response.iter_content(chunk_size=4096):
				downloaded += len(buf)
				if downloaded > length:
					raise ValueError('read too much data, read {}, length {}'.format(downloaded, length))
				hasher.update(buf)
				f.write(buf)

				t = time.time()
				if t - last_report_time > 3 or downloaded == length:
					report()
					last_report_time = t

			if (h := hasher.hexdigest()) != self.release.file_sha256:
				raise ValueError('SHA256 mismatched, expected {}, actual {}, length {}'.format(self.release.file_sha256, h, length))

	def download(self, *, show_progress: bool = False):
		if self.mkdir:
			self.target_path.parent.mkdir(parents=True, exist_ok=True)

		errors = {}
		urls = [
			self.release.file_url,
			self.release.file_url,
			'https://mirror.ghproxy.com/' + self.release.file_url,
		]
		for i, url in enumerate(urls):
			try:
				self.__download(url, show_progress)
			except Exception as e:
				# TODO: LOGGING
				self.replier.reply('Download attempt {} failed, url {!r}, error: {}'.format(i + 1, url, e))
				errors[url] = e
			else:
				return

		raise Exception('All download attempts failed: {}'.format(errors))
