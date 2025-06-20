# History

## 25.1.0 (UNRELEASED)

- Use `asyncio.to_thread` in the `wrap` asynchroniser
  [#213](https://github.com/Tinche/aiofiles/pull/213)
- Switch to [uv](https://docs.astral.sh/uv/) + add Python v3.14 support.
  ([#219](https://github.com/Tinche/aiofiles/pull/219))
- Add `ruff` formatter and linter.
  [#216](https://github.com/Tinche/aiofiles/pull/216)
- Drop Python 3.8 support. If you require it, use version 24.1.0.
  [#204](https://github.com/Tinche/aiofiles/pull/204)

## 24.1.0 (2024-06-24)

- Import `os.link` conditionally to fix importing on android.
  [#175](https://github.com/Tinche/aiofiles/issues/175)
- Remove spurious items from `aiofiles.os.__all__` when running on Windows.
- Switch to more modern async idioms: Remove types.coroutine and make AiofilesContextManager an awaitable instead a coroutine.
- Add `aiofiles.os.path.abspath` and `aiofiles.os.getcwd`.
  [#174](https://github.com/Tinche/aiofiles/issues/181)
- _aiofiles_ is now tested on Python 3.13 too.
  [#184](https://github.com/Tinche/aiofiles/pull/184)
- Drop Python 3.7 support. If you require it, use version 23.2.1.

## 23.2.1 (2023-08-09)

- Import `os.statvfs` conditionally to fix importing on non-UNIX systems.
  [#171](https://github.com/Tinche/aiofiles/issues/171) [#172](https://github.com/Tinche/aiofiles/pull/172)
- aiofiles is now also tested on Windows.

## 23.2.0 (2023-08-09)

- aiofiles is now tested on Python 3.12 too.
  [#166](https://github.com/Tinche/aiofiles/issues/166) [#168](https://github.com/Tinche/aiofiles/pull/168)
- On Python 3.12, `aiofiles.tempfile.NamedTemporaryFile` now accepts a `delete_on_close` argument, just like the stdlib version.
- On Python 3.12, `aiofiles.tempfile.NamedTemporaryFile` no longer exposes a `delete` attribute, just like the stdlib version.
- Added `aiofiles.os.statvfs` and `aiofiles.os.path.ismount`.
  [#162](https://github.com/Tinche/aiofiles/pull/162)
- Use [PDM](https://pdm.fming.dev/latest/) instead of Poetry.
  [#169](https://github.com/Tinche/aiofiles/pull/169)

## 23.1.0 (2023-02-09)

- Added `aiofiles.os.access`.
  [#146](https://github.com/Tinche/aiofiles/pull/146)
- Removed `aiofiles.tempfile.temptypes.AsyncSpooledTemporaryFile.softspace`.
  [#151](https://github.com/Tinche/aiofiles/pull/151)
- Added `aiofiles.stdin`, `aiofiles.stdin_bytes`, and other stdio streams.
  [#154](https://github.com/Tinche/aiofiles/pull/154)
- Transition to `asyncio.get_running_loop` (vs `asyncio.get_event_loop`) internally.

## 22.1.0 (2022-09-04)

- Added `aiofiles.os.path.islink`.
  [#126](https://github.com/Tinche/aiofiles/pull/126)
- Added `aiofiles.os.readlink`.
  [#125](https://github.com/Tinche/aiofiles/pull/125)
- Added `aiofiles.os.symlink`.
  [#124](https://github.com/Tinche/aiofiles/pull/124)
- Added `aiofiles.os.unlink`.
  [#123](https://github.com/Tinche/aiofiles/pull/123)
- Added `aiofiles.os.link`.
  [#121](https://github.com/Tinche/aiofiles/pull/121)
- Added `aiofiles.os.renames`.
  [#120](https://github.com/Tinche/aiofiles/pull/120)
- Added `aiofiles.os.{listdir, scandir}`.
  [#143](https://github.com/Tinche/aiofiles/pull/143)
- Switched to CalVer.
- Dropped Python 3.6 support. If you require it, use version 0.8.0.
- aiofiles is now tested on Python 3.11.

## 0.8.0 (2021-11-27)

- aiofiles is now tested on Python 3.10.
- Added `aiofiles.os.replace`.
  [#107](https://github.com/Tinche/aiofiles/pull/107)
- Added `aiofiles.os.{makedirs, removedirs}`.
- Added `aiofiles.os.path.{exists, isfile, isdir, getsize, getatime, getctime, samefile, sameopenfile}`.
  [#63](https://github.com/Tinche/aiofiles/pull/63)
- Added `suffix`, `prefix`, `dir` args to `aiofiles.tempfile.TemporaryDirectory`.
  [#116](https://github.com/Tinche/aiofiles/pull/116)

## 0.7.0 (2021-05-17)

- Added the `aiofiles.tempfile` module for async temporary files.
  [#56](https://github.com/Tinche/aiofiles/pull/56)
- Switched to Poetry and GitHub actions.
- Dropped 3.5 support.

## 0.6.0 (2020-10-27)

- `aiofiles` is now tested on ppc64le.
- Added `name` and `mode` properties to async file objects.
  [#82](https://github.com/Tinche/aiofiles/pull/82)
- Fixed a DeprecationWarning internally.
  [#75](https://github.com/Tinche/aiofiles/pull/75)
- Python 3.9 support and tests.

## 0.5.0 (2020-04-12)

- Python 3.8 support. Code base modernization (using `async/await` instead of `asyncio.coroutine`/`yield from`).
- Added `aiofiles.os.remove`, `aiofiles.os.rename`, `aiofiles.os.mkdir`, `aiofiles.os.rmdir`.
  [#62](https://github.com/Tinche/aiofiles/pull/62)

## 0.4.0 (2018-08-11)

- Python 3.7 support.
- Removed Python 3.3/3.4 support. If you use these versions, stick to aiofiles 0.3.x.

## 0.3.2 (2017-09-23)

- The LICENSE is now included in the sdist.
  [#31](https://github.com/Tinche/aiofiles/pull/31)

## 0.3.1 (2017-03-10)

- Introduced a changelog.
- `aiofiles.os.sendfile` will now work if the standard `os` module contains a `sendfile` function.
