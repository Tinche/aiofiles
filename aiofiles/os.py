"""Async executor versions of file functions from the os module."""
import asyncio
import sys
from functools import partial, wraps
import os


@asyncio.coroutine
@wraps(os.stat)
def stat(path, *, dir_fd=None, follow_symlinks=True, loop=None, executor=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    fun = partial(os.stat, path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
    return loop.run_in_executor(executor, fun)


if hasattr(os, "sendfile"):
    @asyncio.coroutine
    @wraps(os.sendfile)
    def sendfile(out, in_fd, offset, nbytes, *, loop=None, executor=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        fun = partial(os.sendfile, out, in_fd, offset, nbytes)
        return loop.run_in_executor(executor, fun)
