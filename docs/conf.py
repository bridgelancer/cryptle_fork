# Cryptle documentation build configuration file for sphinx.

import os
import sys
sys.path.append(os.path.abspath('..'))

project = 'Cryptle'
author = 'CryptleFund'
copyright = '2018, CryptleFund'

version = '0.0'
release = '0'

# General --------------------------------------------------------------------

master_doc = 'index'
source_suffix = '.rst'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
]
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autodoc_member_order = 'groupwise'

today_fmt = '%B %d, %Y'
add_module_names = False
pygments_style = 'sphinx'

# HTML -----------------------------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_last_updated_fmt = '%b %d, %Y'

# Output file base name for HTML help builder.
htmlhelp_basename = 'Cryptledoc'


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
