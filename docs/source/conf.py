# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join('..', '..')))


# -- Project information -----------------------------------------------------
import os

project = 'MCDReforged'
copyright = '2022, Fallen_Breath'
author = 'Fallen_Breath'

# The full version, including alpha/beta/rc tags
release = '2.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your customize
# ones.
extensions = [
	'sphinx.ext.autodoc',
	'sphinx.ext.napoleon',
	'sphinx.ext.viewcode',
	'sphinx_copybutton',
	'sphinx-prompt',
]

source_suffix = ['.rst']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['build', 'Thumbs.db', '.DS_Store']


def setup(app):
	autodoc_setup(app)


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'


# Show a deeper toctree in the sidebar
# https://stackoverflow.com/questions/27669376/show-entire-toctree-in-read-the-docs-sidebar
html_theme_options = {
	'navigation_depth': 6,
}


# -- Options for sphinx-intl -------------------------------------------------

# https://docs.readthedocs.io/en/stable/builds.html#build-environment
# available languages: en_US, zh_CN
language = os.environ.get('READTHEDOCS_LANGUAGE', 'en_US')

# po files will be created in this directory
# path is example but recommended.
locale_dirs = ['_locale']
gettext_compact = False  # optional


# -- Options for sphinx.ext.autodoc -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
autodoc_member_order = 'bysource'


def autodoc_setup(app):
	# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#event-autodoc-skip-member
	def autodoc_skip_member_handler(app_, what, name, obj, skip, options):
		return skip
	app.connect('autodoc-skip-member', autodoc_skip_member_handler)


# -- save the table width ----------------------------------------------------
# https://rackerlabs.github.io/docs-rackspace/tools/rtd-tables.html

html_static_path = ['../static']

html_css_files = [
	'css/theme_overrides.css',  # override wide tables in RTD theme
]
