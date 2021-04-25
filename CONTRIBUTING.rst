Contributing to and Hacking on Python httptest
==============================================

How to get started working on / with the ``httptest`` codebase.

Development Mode Install
------------------------

The first thing you need to do if you're going to make a change to ``httptest``
is clone the repo and install it in development mode.

.. code-block:: console

    $ git clone https://github.com/pdxjohnny/httptest
    $ cd httptest

It's usually a good idea to create a virtual environment, so that dependencies
for this project are isolated from dependencies for other project.

.. code-block:: console
    :test:

    $ python -m venv .venv
    $ . .venv/bin/activate

You need to make sure that all the pre-requisite dependencies are up to date.
You should upgrade: ``setuptools``, ``wheel``, and ``pip``.

.. code-block:: console
    :test:

    $ python -m pip install -U setuptools wheel pip

Now install the package in development mode (``-e``). We also use ``[dev]`` to
install the development related dependencies (listed in ``extras_require`` in
the ``setup.cfg`` file). These are things like the code auto formatter,
``black``, and ``twine``, the utility used to upload the package to PyPi.

Installing in development mode means that any changes you make to the files
within the repo you checked out will be used. This is different than a
traditional install because in a traditional install, a snapshot of the codebase
at it's current state at time of install is created. Then the snapshot is
installed into a ``site-packages`` directory. Development mode install tells
Python that a snapshot should not be made, instead, whenever the module is
``import``'ed, Python should use the code in the Git repo that's checked out.

.. code-block:: console
    :test:

    $ python -m pip install -e .[dev]

Testing
-------

To run the tests, just invoke the standard ``unittest`` discover command. It
will run tests in any files where the filename starts with ``test_``.

.. code-block:: console
    :test:

    $ python -m unittest discover -v

Style
-----

We use `black <https://github.com/psf/black>`_ to format. Version ``20.8b1``
specifically. Styling changes with versions, so it's important you have the
correct version installed. Installing in development mode with ``[dev]`` will
ensure version ``20.8b1`` is installed.

.. code-block:: console
    :test:

    $ python -m black .
