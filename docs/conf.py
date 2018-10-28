# Cryptle documentation build configuration file for sphinx.

import os
import sys
sys.path.append(os.path.abspath('..'))

project = 'Cryptle'
author = 'CryptleFund'
copyright = '2018, CryptleFund'

import cryptle
import metric
version = '.'.join((str(n) for n in cryptle.__version__))


# General --------------------------------------------------------------------

add_module_names = False
master_doc = 'index'
pygments_style = 'sphinx'
source_suffix = '.rst'
today_fmt = '%B %d, %Y'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
]

autodoc_member_order = 'groupwise'


# HTML -----------------------------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_last_updated_fmt = '%b %d, %Y'
htmlhelp_basename = 'Cryptledoc'
html_theme_options = {
    'collapse_navigation': False,
    'titles_only': False
}


# LaTeX ----------------------------------------------------------------------

latex_documents = [
    (master_doc, 'Cryptle.tex', 'Cryptle Documentation',
     'CryptleFund', 'manual'),
]


# Manpage --------------------------------------------------------------------

man_pages = [
    (master_doc, 'cryptle', 'Cryptle Documentation',
     [author], 1)
]


# Texinfo --------------------------------------------------------------------

texinfo_documents = [
    (master_doc, 'Cryptle', 'Cryptle Documentation',
     author, 'Cryptle', 'One line description of project.',
     'Miscellaneous'),
]
