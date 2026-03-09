"""Async executor versions of file functions from the os module."""

import os
from asyncio import get_running_loop
from functools import partial

from . import ospath as path
from .base import wrap

__all__ = [
    "path",
    "stat",
    "rename",
    "renames",
    "replace",
    "remove",
    "unlink",
    "mkdir",
    "makedirs",
    "rmdir",
    "removedirs",
    "symlink",
    "readlink",
    "listdir",
    "scandir",
    "access",
    "wrap",
    "getcwd",
]

access = wrap(os.access)

getcwd = wrap(os.getcwd)

listdir = wrap(os.listdir)

makedirs = wrap(os.makedirs)
mkdir = wrap(os.mkdir)

readlink = wrap(os.readlink)
remove = wrap(os.remove)
removedirs = wrap(os.removedirs)
rename = wrap(os.rename)
renames = wrap(os.renames)
replace = wrap(os.replace)
rmdir = wrap(os.rmdir)

_END = object()


class AsyncScandirIterator:
    """An asynchronous iterator and context manager for os.scandir."""

    __slots__ = ("_iterator", "_loop", "_executor")

    def __init__(self, iterator, loop, executor):
        self._iterator = iterator
        self._loop = loop
        self._executor = executor

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self._loop.run_in_executor(
            self._executor, next, self._iterator, _END
        )
        if item is _END:
            raise StopAsyncIteration
        return item

    async def __aenter__(self):
        await self._loop.run_in_executor(self._executor, self._iterator.__enter__)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._loop.run_in_executor(
            self._executor, self._iterator.__exit__, exc_type, exc_val, exc_tb
        )

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iterator)

    def __enter__(self):
        self._iterator.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._iterator.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        return self._iterator.close()


def _wrap_scandir():
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = get_running_loop()
        iterator = await loop.run_in_executor(
            executor, partial(os.scandir, *args, **kwargs)
        )
        return AsyncScandirIterator(iterator, loop, executor)

    return run


scandir = _wrap_scandir()
stat = wrap(os.stat)
symlink = wrap(os.symlink)

unlink = wrap(os.unlink)


if hasattr(os, "link"):
    __all__ += ["link"]
    link = wrap(os.link)
if hasattr(os, "sendfile"):
    __all__ += ["sendfile"]
    sendfile = wrap(os.sendfile)
if hasattr(os, "statvfs"):
    __all__ += ["statvfs"]
    statvfs = wrap(os.statvfs)
