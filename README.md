# Cryptle: Algorithmic trading framework
Cryptle [documentation](http://cryptle-docs.s3-website-ap-southeast-1.amazonaws.com/).

Cryptle is a Python algorithmic trading framework with batteries included.  It
comes with a number of data sources and API implementations of cryptocurrency
exchanges.


## Installation
The Cryptle source distribution is required for it's installation. Obtain a copy
of the source tree and install using [pip](https://pip.pypa.io/en/stable):
```bash
git clone https://github.com/pinealan/cryptle.git
cd cryptle
pip install .
```

Install the dev dependencies as well with the following command:
```bash
pip install .[dev]
```

If you want to install only Cryptle without letting pip resolve the dependency:
```bash
python setup.py install
```


## Testing
Cryptle uses [pytest](https://docs.pytest.org/en/latest/index.html) for testing.
Run unittests with following command:
```bash
make test
```

Run all tests, including integration tests that are I/O bound, with either
commands(this may take a while):
```bash
make test-all
pytest
```

Build the documentation locally by running the following at the root package
directory:
```bash
make doc
```
The compiled documentation in HTML can be found at 'docs/\_build/html/index.html'.
