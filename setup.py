import os
import re

from setuptools import find_packages, setup

from mcdreforged import constant

# python setup.py sdist bdist_wheel
# python -m twine upload --repository testpypi dist/*
# python -m twine upload dist/*


NAME = constant.PACKAGE_NAME
VERSION = constant.VERSION_PYPI
DESCRIPTION = 'A rewritten version of MCDaemon, a python script to control your Minecraft server'
URL = 'https://github.com/Fallen-Breath/MCDReforged'
AUTHOR = 'Fallen_Breath'
REQUIRES_PYTHON = '>=3.6.0'

CLASSIFIERS = [
	# https://pypi.org/classifiers/
	'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
	'Development Status :: 3 - Alpha',
	'Programming Language :: Python',
	'Programming Language :: Python :: 3',
	'Programming Language :: Python :: 3.6',
	'Programming Language :: Python :: 3.7',
	'Programming Language :: Python :: 3.8',
	'Programming Language :: Python :: 3.9',
	'Operating System :: OS Independent'
]

if os.getenv('CI', None) is not None:
	build_num = os.getenv('GITHUB_RUN_NUMBER', None)
	is_release = os.getenv('GITHUB_REF', '').startswith('refs/tags/v')
	if build_num is not None and not is_release:
		VERSION += '.dev{}'.format(build_num)

# ----------------------------------------------------------------

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'requirements.txt')) as f:
	REQUIRED = [re.match(r'^[A-Za-z.]+', line).group() for line in f.readlines() if not len(line.strip()) == 0]

print('REQUIRED = {}'.format(REQUIRED))

with open(os.path.join(here, 'README.md'), encoding='utf8') as f:
	LONG_DESCRIPTION = f.read()


setup(
	name=NAME,
	version=VERSION,
	description=DESCRIPTION,
	long_description=LONG_DESCRIPTION,
	long_description_content_type='text/markdown',
	author=AUTHOR,
	python_requires=REQUIRES_PYTHON,
	url=URL,
	packages=find_packages(exclude=['tests', '*.tests', '*.tests.*', 'tests.*']),
	install_requires=REQUIRED,
	include_package_data=True,
	license='GPL-3.0',
	classifiers=CLASSIFIERS,
)
