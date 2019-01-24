"""Handle files using a thread pool executor."""
import asyncio

from io import (FileIO, TextIOBase, BufferedReader, BufferedWriter,
                BufferedRandom)
from functools import partial, singledispatch

from .binary import AsyncBufferedIOBase, AsyncBufferedReader, AsyncFileIO
from .text import AsyncTextIOWrapper
from ..base import AiofilesContextManager

sync_open = open

__all__ = ('open', )


def open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None,
         closefd=True, opener=None, *, loop=None, executor=None):
    return AiofilesContextManager(_open(file, mode=mode, buffering=buffering,
                                        encoding=encoding, errors=errors,
                                        newline=newline, closefd=closefd,
                                        opener=opener, loop=loop,
                                        executor=executor))


@asyncio.coroutine
def _open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None,
          closefd=True, opener=None, *, loop=None, executor=None):
    """Open an asyncio file."""
    if loop is None:
        loop = asyncio.get_event_loop()
    cb = partial(sync_open, file, mode=mode, buffering=buffering,
                 encoding=encoding, errors=errors, newline=newline,
                 closefd=closefd, opener=opener)
    f = yield from loop.run_in_executor(executor, cb)

    return wrap(f, loop=loop, executor=executor)


@singledispatch
def wrap(file, *, loop=None, executor=None):
    raise TypeError('Unsupported io type: {}.'.format(file))


@wrap.register(TextIOBase)
def _(file, *, loop=None, executor=None):
    return AsyncTextIOWrapper(file, loop=loop, executor=executor)


@wrap.register(BufferedWriter)
def _(file, *, loop=None, executor=None):
    return AsyncBufferedIOBase(file, loop=loop, executor=executor)


@wrap.register(BufferedReader)
@wrap.register(BufferedRandom)
def _(file, *, loop=None, executor=None):
    return AsyncBufferedReader(file, loop=loop, executor=executor)


@wrap.register(FileIO)
def _(file, *, loop=None, executor=None):
    return AsyncFileIO(file, loop, executor)


@asyncio.coroutine
def print(*objects, sep=None, end=None, file, flush=False):
    end = '\n' if end is None else end
    sep = ' ' if sep is None else sep

    if not isinstance(sep, str):
        raise TypeError("sep must be None or a string, not %.200s", type(sep).__name__)


    if not isinstance(end, str):
        raise TypeError("end must be None or a string, not %.200s", type(end).__name__)

    for i, v in enumerate(objects):
        if i > 0:
            yield from file.write(sep)
        yield from file.write(str(v))

    yield from file.write(end)

    if flush:
        yield from file.flush()
