aiofiles: file support for asyncio
==================================

.. image:: https://img.shields.io/pypi/v/aiofiles.svg
    :target: https://pypi.python.org/pypi/aiofiles

aiofiles is an Apache2 licensed library, written in Python, for handling local
disk files in asyncio applications.

Ordinary local file IO is blocking, and cannot easily and portably made
asynchronous. This means doing file IO may interfere with asyncio applications,
which shouldn't block the executing thread. aiofiles helps with this by
introducing asynchronous versions of files that support delegating operations to
a separate thread pool.

.. code-block:: python

    f = yield from aiofiles.open('filename', mode='r')
    try:
        contents = yield from f.read()
    finally:
        yield from f.close()
    print(contents)
    'My file contents'

Features
--------

- a file API very similar to Python's standard, blocking API
- support for buffered and unbuffered binary files, and buffered text files


Installation
------------

To install aiofiles, simply:

.. code-block:: bash

    $ pip install aiofiles

Usage
-----

Files are opened using the ``aiofiles.open()`` coroutine, which in addition to
mirroring the builtin ``open`` accepts optional ``loop`` and ``executor``
arguments. If ``loop`` is absent, the default loop will be used, as per the
set asyncio policy. If ``executor`` is not specified, the default event loop
executor will be used.

In case of success, an asynchronous file object is returned with an
API identical to an ordinary file, except the following methods are coroutines
and delegate to an executor:

* ``close``
* ``flush``
* ``isatty``
* ``read``
* ``readall``
* ``read1``
* ``readinto``
* ``readline``
* ``readlines``
* ``seek``
* ``seekable``
* ``tell``
* ``truncate``
* ``writable``
* ``write``
* ``writelines``

In case of failure, one of the usual exceptions will be raised.

The ``aiofiles.os`` module contains executor-enabled coroutine versions of
several useful ``os`` functions that deal with files:

* ``stat``
* ``sendfile``

Limitations and Differences from the Builtin File API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The closing of a file may block, and yielding from a coroutine while exiting
from a context manager isn't possible, so aiofiles file objects can't be used
as context managers. Use the ``try/finally`` construct from the introductory
section to ensure files are closed.

Iteration is also unsupported. To iterate over a file, call ``readline``
repeatedly until an empty result is returned. Keep in mind ``readline`` doesn't
strip newline characters.

.. code-block:: python

    f = yield from aiofiles.open('filename')
    try:
        while True:
            line = f.readline()
            if not line:
                break
            line = line.strip()
            ...
    finally:
        yield from f.close()

Contributing
~~~~~~~~~~~~
Contributions are very welcome. Tests can be run with ``tox``, please ensure
the coverage at least stays the same before you submit a pull request.