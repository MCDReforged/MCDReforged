import os

from setuptools import find_packages, setup

from mcdreforged.constants import core_constant

# === cheatsheet ===
# rm -rf build/ dist/ mcdreforged.egg-info/
# python setup.py sdist bdist_wheel
# python -m twine upload --repository testpypi dist/*
# python -m twine upload dist/*

# -------------------------------- Basics --------------------------------

NAME = core_constant.PACKAGE_NAME
VERSION = core_constant.VERSION_PYPI
DESCRIPTION = 'A rewritten version of MCDaemon, a python tool to control your Minecraft server'
PROJECT_URLS = {
	'Homepage': core_constant.GITHUB_URL,
	'Documentation': core_constant.DOCUMENTATION_URL,
}
AUTHOR = 'Fallen_Breath'
REQUIRES_PYTHON = '>=3.9'

CLASSIFIERS = [
	# https://pypi.org/classifiers/
	'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
	'Operating System :: OS Independent',
	'Programming Language :: Python',
	'Programming Language :: Python :: 3',
	'Programming Language :: Python :: 3.9',
	'Programming Language :: Python :: 3.10',
	'Programming Language :: Python :: 3.11',
	'Programming Language :: Python :: 3.12',
	'Programming Language :: Python :: 3.13',
]

ENTRY_POINTS = {
	'console_scripts': [
		'{} = {}.mcdr_entrypoint:entrypoint'.format(core_constant.CLI_COMMAND, core_constant.PACKAGE_NAME)
	]
}
print('ENTRY_POINTS = {}'.format(ENTRY_POINTS))

# -------------------------------- Files --------------------------------

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'requirements.txt')) as f:
	REQUIRED = list(filter(None, map(str.strip, f)))
	print('REQUIRED = {}'.format(REQUIRED))

with open(os.path.join(here, 'README.md'), encoding='utf8') as f:
	LONG_DESCRIPTION = f.read()


# -------------------------------- Setup --------------------------------

setup(
	name=NAME,
	version=VERSION,
	description=DESCRIPTION,
	long_description=LONG_DESCRIPTION,
	long_description_content_type='text/markdown',
	author=AUTHOR,
	python_requires=REQUIRES_PYTHON,
	project_urls=PROJECT_URLS,
	packages=find_packages(exclude=['tests', '*.tests', '*.tests.*', 'tests.*']),
	include_package_data=True,
	install_requires=REQUIRED,
	classifiers=CLASSIFIERS,
	entry_points=ENTRY_POINTS,
)
