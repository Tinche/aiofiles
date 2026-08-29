# aiofiles: file support for asyncio

[![PyPI](https://img.shields.io/pypi/v/aiofiles.svg)](https://pypi.python.org/pypi/aiofiles)
[![Build](https://github.com/Tinche/aiofiles/workflows/CI/badge.svg)](https://github.com/Tinche/aiofiles/actions)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Tinche/882f02e3df32136c847ba90d2688f06e/raw/covbadge.json)](https://github.com/Tinche/aiofiles/actions/workflows/main.yml)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/aiofiles.svg)](https://github.com/Tinche/aiofiles)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**aiofiles** is an Apache2 licensed library, written in Python, for handling local
disk files in asyncio applications.

Ordinary local file IO is blocking, and cannot easily and portably be made
asynchronous. This means doing file IO may interfere with asyncio applications,
which shouldn't block the executing thread. aiofiles helps with this by
introducing asynchronous versions of files that support delegating operations to
a separate thread pool.

```python
async with aiofiles.open('filename', mode='r') as f:
    contents = await f.read()
print(contents)
'My file contents'
```

Asynchronous iteration is also supported.

```python
async with aiofiles.open('filename') as f:
    async for line in f:
        ...
```

Asynchronous interface to tempfile module.

```python
async with aiofiles.tempfile.TemporaryFile('wb') as f:
    await f.write(b'Hello, World!')
```

Asynchronous interface to pathlib.

```python
from aiofiles.pathlib import Path

data = await Path('filename').read_text()
async for path in Path('directory').glob('*.txt'):
    ...
```

## Features

- a file API very similar to Python's standard, blocking API
- support for buffered and unbuffered binary files, and buffered text files
- support for `async`/`await` ([PEP 492](https://peps.python.org/pep-0492/)) constructs
- async interface to tempfile module
- async version of `pathlib.Path`

## Installation

To install aiofiles, simply:

```shell
pip install aiofiles
```

## Usage

Files are opened using the `aiofiles.open()` coroutine, which in addition to
mirroring the builtin `open` accepts optional `loop` and `executor`
arguments. If `loop` is absent, the default loop will be used, as per the
set asyncio policy. If `executor` is not specified, the default event loop
executor will be used.

In case of success, an asynchronous file object is returned with an
API identical to an ordinary file, except the following methods are coroutines
and delegate to an executor:

- `close`
- `flush`
- `isatty`
- `read`
- `readall`
- `read1`
- `readinto`
- `readline`
- `readlines`
- `seek`
- `seekable`
- `tell`
- `truncate`
- `writable`
- `write`
- `writelines`

In case of failure, one of the usual exceptions will be raised.

`aiofiles.stdin`, `aiofiles.stdout`, `aiofiles.stderr`,
`aiofiles.stdin_bytes`, `aiofiles.stdout_bytes`, and
`aiofiles.stderr_bytes` provide async access to `sys.stdin`,
`sys.stdout`, `sys.stderr`, and their corresponding `.buffer` properties.

The `aiofiles.os` module contains executor-enabled coroutine versions of
several useful `os` functions that deal with files:

- `stat`
- `statvfs`
- `sendfile`
- `rename`
- `renames`
- `replace`
- `remove`
- `unlink`
- `mkdir`
- `makedirs`
- `rmdir`
- `removedirs`
- `link`
- `symlink`
- `readlink`
- `listdir`
- `scandir`
- `access`
- `getcwd`
- `path.abspath`
- `path.exists`
- `path.isfile`
- `path.isdir`
- `path.islink`
- `path.ismount`
- `path.getsize`
- `path.getatime`
- `path.getctime`
- `path.samefile`
- `path.sameopenfile`

### Tempfile

**aiofiles.tempfile** implements the following interfaces:

- TemporaryFile
- NamedTemporaryFile
- SpooledTemporaryFile
- TemporaryDirectory

Results return wrapped with a context manager allowing use with async with and async for.

```python
async with aiofiles.tempfile.NamedTemporaryFile('wb+') as f:
    await f.write(b'Line1\n Line2')
    await f.seek(0)
    async for line in f:
        print(line)

async with aiofiles.tempfile.TemporaryDirectory() as d:
    filename = os.path.join(d, "file.ext")
```

### Pathlib

`aiofiles.pathlib.Path` is an asynchronous version of `pathlib.Path`. Pure path
operations (`name`, `parent`, `joinpath`, the `/` operator, and so on) do no IO
and stay synchronous. Methods that touch the filesystem are coroutines;
`iterdir`, `glob`, `rglob`, and `walk` return async iterators, and `open()`
returns the same asynchronous file objects as `aiofiles.open()`.

```python
from aiofiles.pathlib import Path

path = Path('directory') / 'file.txt'
if await path.exists():
    contents = await path.read_text()

async with path.open('rb') as f:
    header = await f.read(16)

async for python_file in Path('directory').rglob('*.py'):
    print(python_file, (await python_file.stat()).st_size)
```

The class implements the `os.PathLike` interface, so it is accepted anywhere a
path is, but it cannot substitute for `pathlib.Path` or `pathlib.PurePath`.

The constructor accepts optional `loop` and `executor` keyword arguments, used
for every blocking call and inherited by paths derived from the instance, such
as the results of `parent`, the `/` operator, and `glob`.

On Python 3.14+, `path.info` returns an async version of the path's
`pathlib.types.PathInfo`: its query methods are coroutines, and their answers
are cached like the standard library's. The wrapped synchronous object is
available as `path.info.wrapped`.

### Writing tests for aiofiles

Real file IO can be mocked by patching `aiofiles.threadpool.sync_open`
as desired. The return type also needs to be registered with the
`aiofiles.threadpool.wrap` dispatcher:

```python
aiofiles.threadpool.wrap.register(mock.MagicMock)(
    lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(*args, **kwargs)
)

async def test_stuff():
    write_data = 'data'
    read_file_chunks = [
        b'file chunks 1',
        b'file chunks 2',
        b'file chunks 3',
        b'',
    ]
    file_chunks_iter = iter(read_file_chunks)

    mock_file_stream = mock.MagicMock(
        read=lambda *args, **kwargs: next(file_chunks_iter)
    )

    with mock.patch('aiofiles.threadpool.sync_open', return_value=mock_file_stream) as mock_open:
        async with aiofiles.open('filename', 'w') as f:
            await f.write(write_data)
            assert await f.read() == b'file chunks 1'

        mock_file_stream.write.assert_called_once_with(write_data)
```

### Contributing

Contributions are very welcome. Tests can be run with `tox`, please ensure
the coverage at least stays the same before you submit a pull request.
