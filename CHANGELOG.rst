History
~~~~~~~
0.9.0 (TBC)
``````````````````
* Added ``aiofiles.os.path.islink``.
  `#126 <https://github.com/Tinche/aiofiles/pull/126>`_
* Added ``aiofiles.os.readlink``.
  `#125 <https://github.com/Tinche/aiofiles/pull/125>`_
* Added ``aiofiles.os.symlink``.
  `#124 <https://github.com/Tinche/aiofiles/pull/124>`_
* Added ``aiofiles.os.unlink``.
  `#123 <https://github.com/Tinche/aiofiles/pull/123>`_
* Added ``aiofiles.os.link``.
  `#121 <https://github.com/Tinche/aiofiles/pull/121>`_
* Added ``aiofiles.os.renames``.
  `#120 <https://github.com/Tinche/aiofiles/pull/120>`_

0.8.0 (2021-11-27)
``````````````````
* aiofiles is now tested on Python 3.10.
* Added ``aiofiles.os.replace``.
  `#107 <https://github.com/Tinche/aiofiles/pull/107>`_
* Added ``aiofiles.os.{makedirs, removedirs}``.
* Added ``aiofiles.os.path.{exists, isfile, isdir, getsize, getatime, getctime, samefile, sameopenfile}``.
  `#63 <https://github.com/Tinche/aiofiles/pull/63>`_
* Added `suffix`, `prefix`, `dir` args to ``aiofiles.tempfile.TemporaryDirectory``.
  `#116 <https://github.com/Tinche/aiofiles/pull/116>`_

0.7.0 (2021-05-17)
``````````````````
- Added the ``aiofiles.tempfile`` module for async temporary files.
  `#56 <https://github.com/Tinche/aiofiles/pull/56>`_
- Switched to Poetry and GitHub actions.
- Dropped 3.5 support.

0.6.0 (2020-10-27)
``````````````````
- `aiofiles` is now tested on ppc64le.
- Added `name` and `mode` properties to async file objects.
  `#82 <https://github.com/Tinche/aiofiles/pull/82>`_
- Fixed a DeprecationWarning internally.
  `#75 <https://github.com/Tinche/aiofiles/pull/75>`_
- Python 3.9 support and tests.

0.5.0 (2020-04-12)
``````````````````
- Python 3.8 support. Code base modernization (using ``async/await`` instead of ``asyncio.coroutine``/``yield from``).
- Added ``aiofiles.os.remove``, ``aiofiles.os.rename``, ``aiofiles.os.mkdir``, ``aiofiles.os.rmdir``.
  `#62 <https://github.com/Tinche/aiofiles/pull/62>`_


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