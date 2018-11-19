:orphan:

Welcome to Cryptle
==================

Welcome to Cryptle's documentation. Cryptle is a Python algorithmic trading
framework. Get started with backtesting at :doc:`quickstart`, or go straight to
:doc:`livetrade`. Once you are familiar with the basic usage of Cryptle, we
recommend you to proceed to the :doc:`Usage guides <guides>`, where there would
be more detailed information about individual components in Cryptle.

Installation
------------
The Cryptle source distribution is required for it's installation. Obtain a copy
of the source tree with git:

.. code-block:: bash

   git clone https://github.com/pinealan/cryptle.git

Several tools is essential to contribute to Cryptle. These include Install these
dev dependencies with the following command:

.. code-block:: bash

   pip install .[dev]

Testing
-------
Cryptle uses `pytest <https://docs.pytest.org/en/latest/index.html>`_ for testing.
Run unittests with following command:

.. code-block:: bash

   make test

Run all tests, including integration tests that are I/O bound, with either
commands:

.. code-block:: bash

   # this may take a while
   make test-all

   # or
   pytest

You can build the documentation locally by running the following at the root
repository directory:

.. code-block:: bash

   make doc

The successfully compiled documentation in HTML can be found at
``docs/\_build/html/index.html``.


User Guides
===========

.. toctree::
   :hidden:

   self

.. toctree::
   :maxdepth: 2

   quickstart
   livetrade
   guides

For Cryptle in detail, the full technical reference can be found in the
:doc:`api` document.

.. toctree::
   :maxdepth: 3

   api
