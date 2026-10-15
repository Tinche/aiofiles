"""Executor-backed gzip files."""

import asyncio
import gzip
from functools import partial

from .base import AiofilesContextManager
from .threadpool import wrap
from .threadpool.binary import AsyncBufferedReader
from .threadpool.utils import proxy_property_directly

sync_open = gzip.open

__all__ = ("open",)


@proxy_property_directly("mtime")
class AsyncGzipFile(AsyncBufferedReader):
    """The asyncio executor version of gzip.GzipFile."""


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
    """Open a gzip file with the standard gzip.open options."""
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
    if isinstance(file, gzip.GzipFile):
        return AsyncGzipFile(file, loop=loop, executor=executor)
    return wrap(file, loop=loop, executor=executor)
