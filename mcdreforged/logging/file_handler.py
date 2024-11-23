import datetime
import itertools
import logging
import time
import zipfile
from pathlib import Path
from typing import Optional

from typing_extensions import override


class ZippingDayRotatingFileHandler(logging.FileHandler):
	def __init__(self, file_path: str, rotate_day_count: int):
		self.rotate_day_count = rotate_day_count
		self.file_path = Path(file_path)
		self.dir_path = self.file_path.parent

		self.last_rover_date: Optional[datetime.date] = None
		self.last_record_date: Optional[datetime.date] = None
		self.try_rotate()

		super().__init__(file_path, encoding='utf8')

	@override
	def emit(self, record: logging.LogRecord) -> None:
		try:
			self.try_rotate()
			super().emit(record)
		except Exception:
			self.handleError(record)

	def try_rotate(self):
		current = datetime.datetime.now().date()

		if self.last_rover_date is None or (current - self.last_rover_date).days >= self.rotate_day_count:
			self.do_rotate(self.last_record_date and self.last_record_date.strftime('%Y-%m-%d'))
			self.last_rover_date = current

		self.last_record_date = current

	def do_rotate(self, base_name: Optional[str] = None):
		if not self.file_path.is_file():
			return

		inited = hasattr(self, 'stream')
		if inited:
			self.stream.close()
		try:
			if base_name is None:
				try:
					log_time = time.localtime(self.file_path.stat().st_mtime)
				except (OSError, OverflowError, ValueError):
					log_time = time.localtime()
				base_name = time.strftime('%Y-%m-%d', log_time)
			for counter in itertools.count(start=1):
				zip_path = self.dir_path / '{}-{}.zip'.format(base_name, counter)
				if not zip_path.is_file():
					break
			else:
				raise RuntimeError('should already able to get a valid zip path')
			with zipfile.ZipFile(zip_path, 'w') as zipf:
				zipf.write(self.file_path, arcname=self.file_path.name, compress_type=zipfile.ZIP_DEFLATED)

			try:
				self.file_path.unlink()
			except OSError:
				# failed to delete the old log file, might due to another MCDR instance being running
				# delete the rotated zip file to avoid duplication
				try:
					zip_path.unlink()
				except OSError:
					pass
				raise
		finally:
			if inited:
				self.stream = self._open()
