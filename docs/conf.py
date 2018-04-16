# Cryptle documentation build configuration file for sphinx.
#
# Most builtin configurable values are listed, those that are commented out
# shows the default.

import os
import sys
sys.path.append(os.path.abspath('..'))

project = 'Cryptle'
author = 'CryptleFund'
copyright = '2018, CryptleFund'

version = '0.0'
release = '0'


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
]

# Extension configurations
autodoc_member_order = 'groupwise'

# Add any paths that contain templates here, reative to this directory
# templates_path = []

# The suffix(es) of source filenames.
source_suffix = '.rst'

# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# primary_domain = 'py'

# default_role = None

today_fmt = '%B %d, %Y'

# highlight_language = 'python3'

# highlight_options = {}

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all unit descriptions
add_module_names = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output -------------------------------------------------

html_theme = 'classic'

# Theme-specific options that customize the look and feel of a theme.
# html_theme_options = {}

# html_theme_path = ['_theme']

# html_style = None
# html_title = None
# html_short_title = None
# html_context = None

# Filename of an image file to place at the top of the sidebar.
# html_logo = None

# Filename of an image file to use as favicon of the docs.
# html_favicon = None

# Add any paths that contain custom static files (such as style sheets).
html_static_path = ['_static']

html_last_updated_fmt = '%b %d, %Y'

# html_index = ''
# html_sidebars = {}
# html_additional_pages = {}
# html_domain_index = True
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, links to the reST sources are added to the pages.
# html_show_sourcelink = True

# html_show_sphinx = True
# html_show_copyright = True
# html_use_opensearch = ''
# html_file_suffix = None


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'Cryptledoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'Cryptle.tex', 'Cryptle Documentation',
     'CryptleFund', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'cryptle', 'Cryptle Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'Cryptle', 'Cryptle Documentation',
     author, 'Cryptle', 'One line description of project.',
     'Miscellaneous'),
]
