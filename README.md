# Cryptle: Algorithmic trading framework
Cryptle's web [documentation](http://cryptle-docs.s3-website-ap-southeast-1.amazonaws.com/),
hosted statically on AWS S3.

Cryptle is a Python algorithmic trading framework with batteries included.  It
comes with a number of data sources and API implementations of cryptocurrency
exchanges.


## Installation
Python3.5 is required to run cryptle.

Cryptle is not yet avaliable on [PyPI](https://pypi.org/) and must be installed 
from source. Obtain a copy of the source tree and install it with
[pip](https://pip.pypa.io/en/stable):
```bash
git clone https://github.com/pinealan/cryptle
cd cryptle
sudo pip install .
```

#### Development setup
[venv](https://docs.python.org/3/library/venv.html) is the recommended
method to create a local development environment and manage dependencies. The
following is a quick look at how to use venv with pip to set up a virutal
environment to use/develop cryptle.

Python3.6 is required to setup dev environemnt. (Blame
[black](https://github.com/ambv/black) for that)

```
python3.6 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```
1. Create a virtual environment in a new local directory `.venv`. Using
   `pythone3.6` ensures the installation symlinks to a python3.6 binary.
   Substitue with your system's python path when approperiate.
2. Sources the virtual environment's activation script. This modify future calls
   to python and pip binaries to use the ones provided by the virtual
   environment.
3. Install the required onto the virutalenv. Flag `-e` makes the installtion
   _editable_. This means the installation directly links to the packages
   source, and any changes is effective immediately. Adding `[dev]` makes pip to
   install development packages from `extra_requires`.


## Dev tools
Cryptle uses [pytest](https://docs.pytest.org/en/latest/index.html) for testing.
Run unittests with following command:
```bash
make test
```

Run all tests, including integration tests that are I/O bound, with either
commands(this may take a while):
```bash
make testall
```

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


## FAQ

##### ImportError: No module named '\_tkinter'
If you're getting the warning _failing to import module 'plotting' from module
'cryptle'_, your will need to install system libraries for python tkinter, which
is the default backend of matplotlib.
[Solution](https://stackoverflow.com/questions/50327906/importerror-no-module-named-tkinter-please-install-the-python3-tk-package)

##### Why not [pipenv](https://pipenv.readthedocs.io/en/latest/)?

Pipenv's is VERY slow in generating the lockfile. Besides, cryptle has grown
from a monolithic repository for both library and application into a
stand-alone framework package. This removes the need for pipenv's most desired
strength: locking dependencies.
