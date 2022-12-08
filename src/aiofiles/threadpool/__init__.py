"""Handle files using a thread pool executor."""
import asyncio
import sys
from types import coroutine

from io import (
    FileIO,
    TextIOBase,
    BufferedReader,
    BufferedWriter,
    BufferedRandom,
    BufferedIOBase,
)
from functools import partial, singledispatch

from .binary import (
    AsyncBufferedIOBase,
    AsyncBufferedReader,
    AsyncFileIO,
    AsyncIndirectBufferedIOBase,
    AsyncIndirectBufferedReader,
    AsyncIndirectFileIO,
)
from .text import AsyncTextIOWrapper, AsyncTextIndirectIOWrapper
from ..base import AiofilesContextManager

sync_open = open

__all__ = (
    "open",
    "stdin",
    "stdout",
    "stderr",
    "stdin_bytes",
    "stdout_bytes",
    "stderr_bytes",
)


def open(
    file,
    mode="r",
    buffering=-1,
    encoding=None,
    errors=None,
    newline=None,
    closefd=True,
    opener=None,
    *,
    loop=None,
    executor=None
):
    return AiofilesContextManager(
        _open(
            file,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=opener,
            loop=loop,
            executor=executor,
        )
    )


@coroutine
def _open(
    file,
    mode="r",
    buffering=-1,
    encoding=None,
    errors=None,
    newline=None,
    closefd=True,
    opener=None,
    *,
    loop=None,
    executor=None
):
    """Open an asyncio file."""
    if loop is None:
        loop = asyncio.get_event_loop()
    cb = partial(
        sync_open,
        file,
        mode=mode,
        buffering=buffering,
        encoding=encoding,
        errors=errors,
        newline=newline,
        closefd=closefd,
        opener=opener,
    )
    f = yield from loop.run_in_executor(executor, cb)

    return wrap(f, loop=loop, executor=executor)


@singledispatch
def wrap(file, *, loop=None, executor=None, indirect=None):
    raise TypeError("Unsupported io type: {}.".format(file))


@wrap.register(TextIOBase)
def _(file, *, loop=None, executor=None, indirect=None):
    if indirect is None:
        return AsyncTextIOWrapper(file, loop=loop, executor=executor)
    else:
        return AsyncTextIndirectIOWrapper(
            file, loop=loop, executor=executor, indirect=indirect
        )


@wrap.register(BufferedWriter)
@wrap.register(BufferedIOBase)
def _(file, *, loop=None, executor=None, indirect=None):
    if indirect is None:
        return AsyncBufferedIOBase(file, loop=loop, executor=executor)
    else:
        return AsyncIndirectBufferedIOBase(
            file, loop=loop, executor=executor, indirect=indirect
        )


@wrap.register(BufferedReader)
@wrap.register(BufferedRandom)
def _(file, *, loop=None, executor=None, indirect=None):
    if indirect is None:
        return AsyncBufferedReader(file, loop=loop, executor=executor)
    else:
        return AsyncIndirectBufferedReader(
            file, loop=loop, executor=executor, indirect=indirect
        )


@wrap.register(FileIO)
def _(file, *, loop=None, executor=None, indirect=None):
    if indirect is None:
        return AsyncFileIO(file, loop, executor)
    else:
        return AsyncIndirectFileIO(file, loop, executor, indirect=indirect)


try:
    stdin = wrap(sys.stdin, indirect=lambda: sys.stdin)
except TypeError:
    stdin = None
try:
    stdout = wrap(sys.stdout, indirect=lambda: sys.stdout)
except TypeError:
    stdout = None
try:
    stderr = wrap(sys.stderr, indirect=lambda: sys.stderr)
except TypeError:
    stdout = None
try:
    stdin_bytes = wrap(sys.stdin.buffer, indirect=lambda: sys.stdin.buffer)
except TypeError:
    stdin_bytes = None
try:
    stdout_bytes = wrap(sys.stdout.buffer, indirect=lambda: sys.stdout.buffer)
except TypeError:
    stdout_bytes = None
try:
    stderr_bytes = wrap(sys.stderr.buffer, indirect=lambda: sys.stderr.buffer)
except TypeError:
    stderr_bytes = None
