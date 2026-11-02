"""Handle files using a thread pool executor."""

import asyncio
import sys
import threading
from functools import partial, singledispatch
from io import (
    BufferedIOBase,
    BufferedRandom,
    BufferedReader,
    BufferedWriter,
    FileIO,
    TextIOBase,
)

from ..base import AiofilesContextManager
from .binary import (
    AsyncBufferedIOBase,
    AsyncBufferedReader,
    AsyncFileIO,
    AsyncIndirectBufferedIOBase,
)
from .text import AsyncTextIndirectIOWrapper, AsyncTextIOWrapper

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
    executor=None,
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


async def _open(
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
    executor=None,
):
    """Open an asyncio file."""
    if loop is None:
        loop = asyncio.get_running_loop()
    open_file = partial(
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
    # `state` is shared with the worker thread. Once the call is cancelled,
    # a worker that has not started yet must not open (and possibly create
    # or truncate) the file. A worker that has already started will finish,
    # and the file it returns is closed instead of being left to the GC.
    lock = threading.Lock()
    state = {"started": False, "cancelled": False}

    def cb():
        with lock:
            if state["cancelled"]:
                return None
            state["started"] = True
        return open_file()

    fut = loop.run_in_executor(executor, cb)
    try:
        f = await asyncio.shield(fut)
    except asyncio.CancelledError:
        with lock:
            state["cancelled"] = True
            started = state["started"]
        if started:
            fut.add_done_callback(partial(_close_abandoned, loop, executor))
        else:
            fut.cancel()
        raise

    return wrap(f, loop=loop, executor=executor)


def _close_abandoned(loop, executor, fut):
    """Close a file whose open() call was cancelled after it started."""
    if fut.cancelled() or fut.exception() is not None:
        return
    f = fut.result()
    try:
        loop.run_in_executor(executor, f.close)
    except RuntimeError:
        # The executor (or the loop) is already shut down.
        f.close()


@singledispatch
def wrap(file, *, loop=None, executor=None):
    msg = f"Unsupported io type: {file}."
    raise TypeError(msg)


@wrap.register(TextIOBase)
def _(file, *, loop=None, executor=None):
    return AsyncTextIOWrapper(file, loop=loop, executor=executor)


@wrap.register(BufferedWriter)
@wrap.register(BufferedIOBase)
def _(file, *, loop=None, executor=None):
    return AsyncBufferedIOBase(file, loop=loop, executor=executor)


@wrap.register(BufferedReader)
@wrap.register(BufferedRandom)
def _(file, *, loop=None, executor=None):
    return AsyncBufferedReader(file, loop=loop, executor=executor)


@wrap.register(FileIO)
def _(file, *, loop=None, executor=None):
    return AsyncFileIO(file, loop=loop, executor=executor)


stdin = AsyncTextIndirectIOWrapper("sys.stdin", None, None, indirect=lambda: sys.stdin)
stdout = AsyncTextIndirectIOWrapper(
    "sys.stdout", None, None, indirect=lambda: sys.stdout
)
stderr = AsyncTextIndirectIOWrapper(
    "sys.stderr", None, None, indirect=lambda: sys.stderr
)
stdin_bytes = AsyncIndirectBufferedIOBase(
    "sys.stdin.buffer", None, None, indirect=lambda: sys.stdin.buffer
)
stdout_bytes = AsyncIndirectBufferedIOBase(
    "sys.stdout.buffer", None, None, indirect=lambda: sys.stdout.buffer
)
stderr_bytes = AsyncIndirectBufferedIOBase(
    "sys.stderr.buffer", None, None, indirect=lambda: sys.stderr.buffer
)
