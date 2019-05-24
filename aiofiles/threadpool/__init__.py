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
    return AiofilesContextManager(
        run_threadpool(
            sync_open, file, mode=mode, buffering=buffering,
            encoding=encoding, errors=errors, newline=newline, closefd=closefd,
            opener=opener, loop=loop, executor=executor, async_wrap=wrap,
        )
    )


@asyncio.coroutine
def run_threadpool(sync_cb, *args, loop=None, executor=None, async_wrap=None,
                   **kwargs):
    """
    Wrap a sync function to run in a threadpool.
    
    :param sync_cb: Original, synchronous callable to run (e.g. ``open``).
    :param args: Remaining arguments to be passed on to the sync callable.
    :param loop: Loop to run the sync callable in. The default is the current
        event loop.
    :param executor: Executor to run the sync callable in. The default is
        whatever ``loop.run_in_executor`` defaults to (currently
        ``concurrent.futures.ThreadPoolExecutor``).
    :param async_wrap: Wrapper callable that handles the returned file (most
        likely something from ``aiofiles.base.AsyncBase``). Should be able to
        take the object returned from the original callable, in addition to
        ``loop`` and ``executor`` parameters. If this parameter is missing, then
        the return from the original will be returned as-is.
    :param kwargs: Remaining keyword arguments to be passed on to the sync
        function.
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    cb = partial(sync_cb, *args, **kwargs)
    ret = yield from loop.run_in_executor(executor, cb)

    if async_wrap:
        return async_wrap(ret, loop=loop, executor=executor)
    return ret


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
