"""Async executor versions of file functions from the os module."""

import asyncio
import os
from functools import partial
from queue import Queue, Empty

from .base import wrap
from . import ospath as path


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

scandir = wrap(os.scandir)
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


async def walk(top, topdown=True, onerror=None, followlinks=False):
    """Asynchronous directory tree generator.

    Wraps the `os.walk` function.
    """

    def _walk(q: Queue):
        nonlocal is_over
        try:
            for row in os.walk(
                top, topdown=topdown, onerror=onerror, followlinks=followlinks
            ):
                q.put_nowait(row)
        finally:
            is_over = True

    loop = asyncio.get_running_loop()
    queue = Queue()

    is_over = False

    walker = partial(_walk, q=queue)
    loop.run_in_executor(None, walker)
    while True:
        if is_over and queue.empty():
            break
        try:
            entry = queue.get_nowait()
            queue.task_done()
            yield entry
        except Empty:
            pass
    queue.join()
