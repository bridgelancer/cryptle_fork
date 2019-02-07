# Cryptle: Algorithmic trading framework
<a href="https://github.com/ambv/black"><img alt="Code style: black"
src="https://img.shields.io/badge/style-black-000000.svg"></a>

Cryptle's web [documentation](http://cryptle-docs.s3-website-ap-southeast-1.amazonaws.com/),
hosted statically on AWS S3.

Cryptle is a Python algorithmic trading framework with batteries included.  It
comes with a number of data sources and API implementations of cryptocurrency
exchanges.


## Installation
Python3.6 is required to run cryptle.

Cryptle is not yet avaliable on [PyPI](https://pypi.org/) and must be installed
from source. Obtain a copy of the source tree and install it with
[pip](https://pip.pypa.io/en/stable):
```bash
git clone https://github.com/pinealan/cryptle
cd cryptle
sudo pip install .
```

### Development setup
[venv](https://docs.python.org/3/library/venv.html) is the recommended method to
create a local development environment and manage dependencies. A make command
is provided as the setup shortcut:
```
make initial-python-setup
```

The following is a quick look at what that command did, and how to use venv with
pip by yourself to set up a virutal environment to develop python projects.

1. Create a virtual environment in a new local directory `.venv`. Using
   `python3.6` ensures the installation symlinks to a python3.6 binary.
   Substitue with your system's python path when approperiate.
2. Sources the virtual environment's activation script. This modify future calls
   to python and pip binaries to use the ones provided by the virtual
   environment.
3. Install the required onto the virutalenv. Flag `-e` makes the installtion
   _editable_. This means the installation directly links to the packages
   source, and any changes is effective immediately. Adding `[dev]` makes pip to
   install development packages from `extra_requires`.

See FAQ for [issues on Debian/Ubuntu/Mint](#install-python-venv-on-debian).


## Contributing

### Testing
Cryptle uses [pytest](https://docs.pytest.org/en/latest/index.html) for testing.

Run unittests with command `make test`. This only run tests in the directory
`test/unit`.

Run all tests, including I/O bound integration tests, with the command `make
testall` (this may take a while).

Build the documentation locally by running the following at the root package
directory:
```bash
make doc
```
The compiled documentation in HTML can be found relative to the project root at
`docs/_build/html/index.html`.

For convenience sake, the provided command `make servedoc` builds the docs,
starts a simple server, and launch the page in your default browser all in one
go.

### Code style
All code must be formatted with [black](https://github.com/ambv/black) before
committed. The CI _will_ reject commits that doesn't pass black's check. The
only black configuration we have is skip string normalisation, i.e. you may use
single quote strings. In fact we prefer single quoted strings. Also note that
black limits to 88 character as line width.

#### Imports
All imports should be done at the top of a python file. The only exception for
this is for resolving between packages for different OS or Python version.

The order of import should be __stdlib__, __external dependencies__, then
__internal modules__. External dependencies meaning packages that are installed
from somewhere outside the project, i.e. ones that came with pip install.
Internal packages meaning code from other parts of the project.

#### Naming convention
The following should cover most cases. If in doubt, consult the [Google Python
Style Guide](https://google.github.io/styleguide/pyguide.html#Comments). When
there's any conflict between Google and the following, this list should take
precedence.

- snake_case for variables and module level functions.
- CamelCase for classes.
- mixedCase for methods.
- Avoid puncations for package names. Excessively long names i.e. 15 character
  long may use underscores. However, if your package name is that long, you
  should consider giving it a better name.


## FAQ

##### ImportError: No module named `_tkinter`
If you're getting the warning `failing to import module 'plotting' from module
'cryptle'`, your will need to install system libraries for python tkinter, which
is the default backend of matplotlib. To fix, install tk with this command:
```
$ sudo apt-get install python3-tk
```
Or use a different backend.
```
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
```

[Source](https://stackoverflow.com/questions/50327906/importerror-no-module-named-tkinter-please-install-the-python3-tk-package).

##### Install python3-venv on Debian
Install the `venv` package through apt
```
$ sudo apt-get install python3-venv
```
Even though venv is now part of Python's standard library, Debian based systems
doesn't have the `ensurepip` Python package in their default python distribution,
which is one of `venv`'s dependencies.

To resolve fix this, simply do as the error says and install the package
`python3-venv`. If you installed other versions of python from apt, such as
python3.6, you would have to install the corresponding package, such as
`python3.6-venv`.

[Source](https://stackoverflow.com/a/47842394/7768732).

##### Why not [pipenv](https://pipenv.readthedocs.io/en/latest/)?
Pipenv's is VERY slow in generating the lockfile. Besides, cryptle has grown
from a monolithic repository for both library and application into a
stand-alone framework package. This removes the need for pipenv's most desired
strength: locking dependencies.
