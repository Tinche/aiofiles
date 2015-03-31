"""Handle files using a thread pool executor."""
import asyncio
from .binary import AsyncBufferedIOBase, AsyncBufferedReader, AsyncFileIO
from .text import AsyncTextIOWrapper
from io import (FileIO, TextIOBase, BufferedReader, BufferedWriter,
                BufferedRandom)
import functools

_sync_open = open


__all__ = ('open', 'wrap')

@asyncio.coroutine
def open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None,
         closefd=True, opener=None, loop=None, executor=None):
    """Open an asyncio file."""
    if loop is None:
        loop = asyncio.get_event_loop()
    cb = functools.partial(_sync_open, file, mode=mode, buffering=buffering,
                           encoding=encoding, errors=errors, newline=newline,
                           closefd=closefd, opener=opener)
    f = yield from loop.run_in_executor(executor, cb)

    return wrap(f, loop, executor)


@functools.singledispatch
def wrap(file, loop=None, executor=None):
    raise TypeError('Unsupported io type: {}.'.format(file))


@wrap.register(TextIOBase)
def _(file, loop=None, executor=None):
    return AsyncTextIOWrapper(file, loop, executor)


@wrap.register(BufferedWriter)
def _(file, loop=None, executor=None):
    return AsyncBufferedIOBase(file, loop, executor)


@wrap.register(BufferedReader)
@wrap.register(BufferedRandom)
def _(file, loop=None, executor=None):
    return AsyncBufferedReader(file, loop, executor)


@wrap.register(FileIO)
def _(file, loop=None, executor=None):
    return AsyncFileIO(file, loop, executor)

