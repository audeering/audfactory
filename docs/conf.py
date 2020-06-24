import os
from subprocess import check_output
import sys

import audeer


# Project -----------------------------------------------------------------
project = 'audfactory'
copyright = '2019-2020 audEERING GmbH'
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
]
intersphinx_mapping = {
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
}
html_title = title


# Run examples ------------------------------------------------------------
# Execute all Python files stored under docs/examples/
# and store the resulting output under docs/examples/output/
input_dir = os.path.abspath('./examples')
output_dir = os.path.abspath('./examples/output')
audeer.mkdir(output_dir)
examples = audeer.list_file_names(input_dir)
orig_stdout = sys.stdout
for example in examples:
    output_file = os.path.join(
        output_dir,
        audeer.basename_wo_ext(example) + '.txt',
    )
    with open(output_file, 'w') as f:
        sys.stdout = f
        try:
            exec(open(example).read())
        except Exception as e:
            raise(e)
        finally:
            sys.stdout = orig_stdout
