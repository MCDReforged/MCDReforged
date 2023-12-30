import os.path
import shlex
import subprocess
import sys
import tempfile
from typing import Optional, List
from zipfile import ZipFile

from mcdreforged.constants import plugin_constant


def pip_install_from_plugins(plugin_paths: List[str], extra_args: Optional[str] = None, *, quiet: bool = False):
	if len(plugin_paths) == 0:
		if not quiet:
			print('Error: No plugin file has been provided')
		sys.exit(1)

	writeln = print if not quiet else lambda *args_, **kwargs_: None

	# read requirements.txt
	requirement_lines: List[bytes] = []
	for plugin_path in plugin_paths:
		req_file_name = plugin_constant.PLUGIN_REQUIREMENTS_FILE
		try:
			with ZipFile(plugin_path) as zip_file:
				if req_file_name not in zip_file.namelist():
					writeln('Plugin {} does not contain a {}'.format(plugin_path, req_file_name))
					continue
				requirement_lines.extend(zip_file.read(req_file_name).splitlines())
		except Exception as e:
			writeln('Failed to read plugin {}: {}'.format(plugin_path, e))

	writeln('Installing requirements from {}'.format(', '.join(plugin_paths)))
	subprocess.call([sys.executable, '-m', 'pip', '-V'])

	temp_file = None
	try:
		# cannot set delete=True, or pip cannot access it
		with tempfile.NamedTemporaryFile(delete=False) as temp_file:
			temp_file.write(b'\n'.join(requirement_lines))
			temp_file.flush()

		args = [sys.executable, '-m', 'pip', 'install', '-r', temp_file.name]
		if extra_args is not None:
			args.extend(shlex.split(extra_args))
		if quiet:
			args.append('-q')

		ret = subprocess.call(args)
		if ret == 0:
			writeln('Pip install succeeded')
		else:
			writeln('Pip process failed with return code {}'.format(ret))
	finally:
		if temp_file is not None:
			try:
				os.unlink(temp_file.name)
			except OSError:
				pass
