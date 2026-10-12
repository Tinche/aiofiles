"""Async wrappers for spooled temp files and temp directory objects"""

from functools import partial

from ..base import AsyncBase
from ..threadpool.utils import (
    cond_delegate_to_executor,
    delegate_to_executor,
    proxy_property_directly,
)


@delegate_to_executor("fileno", "rollover")
@cond_delegate_to_executor(
    "close",
    "flush",
    "isatty",
    "read",
    "readline",
    "readlines",
    "seek",
    "tell",
    "truncate",
)
@proxy_property_directly("closed", "encoding", "mode", "name", "newlines")
class AsyncSpooledTemporaryFile(AsyncBase):
    """Async wrapper for SpooledTemporaryFile class"""

    def readable(self):
        """Return whether the underlying stream supports reading."""
        return self._file._file.readable()

    async def seekable(self):
        """Return whether the underlying stream supports seeking."""
        return await self._capability("seekable")

    async def writable(self):
        """Return whether the underlying stream supports writing."""
        return await self._capability("writable")

    async def _capability(self, name):
        # SpooledTemporaryFile itself has these methods only on Python 3.11+.
        method = getattr(self._file._file, name)
        if self._file._rolled:
            return await self._loop.run_in_executor(self._executor, method)
        return method()

    async def _check(self):
        if self._file._rolled:
            return
        max_size = self._file._max_size
        if max_size and self._file.tell() > max_size:
            await self.rollover()

    async def write(self, s):
        """Implementation to anticipate rollover"""
        if self._file._rolled:
            cb = partial(self._file.write, s)
            return await self._loop.run_in_executor(self._executor, cb)

        file = self._file._file  # reference underlying base IO object
        rv = file.write(s)
        await self._check()
        return rv

    async def writelines(self, iterable):
        """Implementation to anticipate rollover"""
        if self._file._rolled:
            cb = partial(self._file.writelines, iterable)
            return await self._loop.run_in_executor(self._executor, cb)

        file = self._file._file  # reference underlying base IO object
        rv = file.writelines(iterable)
        await self._check()
        return rv


@delegate_to_executor("cleanup")
@proxy_property_directly("name")
class AsyncTemporaryDirectory:
    """Async wrapper for TemporaryDirectory class"""

    def __init__(self, file, loop, executor):
        self._file = file
        self._loop = loop
        self._executor = executor

    async def close(self):
        await self.cleanup()
