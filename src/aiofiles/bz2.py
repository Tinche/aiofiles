"""Executor-backed bz2 files."""

import asyncio
import bz2
from functools import partial

from .base import AiofilesContextManager
from .threadpool import wrap
from .threadpool.binary import AsyncBufferedReader

sync_open = bz2.open

__all__ = ("open",)


def open(
    filename,
    mode="rb",
    compresslevel=9,
    encoding=None,
    errors=None,
    newline=None,
    *,
    loop=None,
    executor=None,
):
    """Open a bz2 file with the standard bz2.open options."""
    return AiofilesContextManager(
        _open(
            filename,
            mode=mode,
            compresslevel=compresslevel,
            encoding=encoding,
            errors=errors,
            newline=newline,
            loop=loop,
            executor=executor,
        )
    )


async def _open(filename, *, loop, executor, **kwargs):
    if loop is None:
        loop = asyncio.get_running_loop()
    file = await loop.run_in_executor(executor, partial(sync_open, filename, **kwargs))
    if isinstance(file, bz2.BZ2File):
        return AsyncBufferedReader(file, loop=loop, executor=executor)
    return wrap(file, loop=loop, executor=executor)
