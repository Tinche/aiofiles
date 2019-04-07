aiofiles: file support for asyncio
==================================

.. image:: https://img.shields.io/pypi/v/aiofiles.svg
        :target: https://pypi.python.org/pypi/aiofiles

.. image:: https://travis-ci.org/Tinche/aiofiles.svg?branch=master
        :target: https://travis-ci.org/Tinche/aiofiles

.. image:: https://codecov.io/gh/Tinche/aiofiles/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/Tinche/aiofiles

.. image:: https://img.shields.io/pypi/pyversions/aiofiles.svg
        :target: https://github.com/Tinche/aiofiles
        :alt: Supported Python versions

**aiofiles** is an Apache2 licensed library, written in Python, for handling local
disk files in asyncio applications.

Ordinary local file IO is blocking, and cannot easily and portably made
asynchronous. This means doing file IO may interfere with asyncio applications,
which shouldn't block the executing thread. aiofiles helps with this by
introducing asynchronous versions of files that support delegating operations to
a separate thread pool.

.. code-block:: python

    async with aiofiles.open('filename', mode='r') as f:
        contents = await f.read()
    print(contents)
    'My file contents'

Asynchronous iteration is also supported.

.. code-block:: python

    async with aiofiles.open('filename') as f:
        async for line in f:
            ...

Features
--------

- a file API very similar to Python's standard, blocking API
- support for buffered and unbuffered binary files, and buffered text files
- support for ``async``/``await`` (:PEP:`492`) constructs


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
* ``rename``
* ``remove``
* ``mkdir``
* ``rmdir``

Writing tests for aiofiles
~~~~~~~~~~~~~~~~~~~~~~~~~~

Real file IO can be mocked by patching ``aiofiles.threadpool.sync_open``
as desired. The return type also needs to be registered with the
``aiofiles.threadpool.wrap`` dispatcher:

.. code-block:: python

    aiofiles.threadpool.wrap.register(mock.MagicMock)(
        lambda *args, **kwargs: threadpool.AsyncBufferedIOBase(*args, **kwargs))

    async def test_stuff():
        data = 'data'
        mock_file = mock.MagicMock()

        with mock.patch('aiofiles.threadpool.sync_open', return_value=mock_file) as mock_open:
            async with aiofiles.open('filename', 'w') as f:
                await f.write(data)

            mock_file.write.assert_called_once_with(data)

History
~~~~~~~

0.4.0 (2018-08-11)
``````````````````
- Python 3.7 support.
- Removed Python 3.3/3.4 support. If you use these versions, stick to aiofiles 0.3.x.

0.3.2 (2017-09-23)
``````````````````
- The LICENSE is now included in the sdist.
  `#31 <https://github.com/Tinche/aiofiles/pull/31>`_

0.3.1 (2017-03-10)
``````````````````

- Introduced a changelog.
- ``aiofiles.os.sendfile`` will now work if the standard ``os`` module contains a ``sendfile`` function.

Contributing
~~~~~~~~~~~~
Contributions are very welcome. Tests can be run with ``tox``, please ensure
the coverage at least stays the same before you submit a pull request.
