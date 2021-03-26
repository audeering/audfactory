from datetime import date
import os
from subprocess import check_output
import sys

import audeer


# Project -----------------------------------------------------------------
project = 'audfactory'
copyright = f'2019-{date.today().year} audEERING GmbH'
author = 'Hagen Wierstorf'
# The x.y.z version read from tags
try:
    version = check_output(['git', 'describe', '--tags', '--always'])
    version = version.decode().strip()
except Exception:
    version = '<unknown>'
title = '{} Documentation'.format(project)


# General -----------------------------------------------------------------
master_doc = 'index'
extensions = []
source_suffix = '.rst'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
pygments_style = None
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # support for Google-style docstrings
    'sphinx_autodoc_typehints',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_copybutton',
    'jupyter_sphinx',
]
intersphinx_mapping = {
    'audeer': ('https://audeering.github.io/audeer/', None),
    'python': ('https://docs.python.org/3/', None),
    'pandas': ('https://pandas-docs.github.io/pandas-docs-travis/', None),
}
# Disable Gitlab as we need to sign in
linkcheck_ignore = [
    'https://gitlab.audeering.com',
    'http://sphinx-doc.org/',
]


# HTML --------------------------------------------------------------------
html_theme = 'sphinx_audeering_theme'
html_theme_options = {
    'display_version': True,
    'logo_only': False,
    'footer_links': False,
}
html_context = {
    'display_github': True,
}
html_title = title
