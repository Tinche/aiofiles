"""Async executor versions of file functions from the os module."""

import os

from . import ospath as path
from .base import to_coro

__all__ = [
    "access",
    "getcwd",
    "listdir",
    "makedirs",
    "mkdir",
    "readlink",
    "remove",
    "removedirs",
    "rename",
    "renames",
    "replace",
    "rmdir",
    "path",
    "scandir",
    "stat",
    "symlink",
    "unlink",
]

access = to_coro(os.access)

getcwd = to_coro(os.getcwd)

listdir = to_coro(os.listdir)

makedirs = to_coro(os.makedirs)
mkdir = to_coro(os.mkdir)

readlink = to_coro(os.readlink)
remove = to_coro(os.remove)
removedirs = to_coro(os.removedirs)
rename = to_coro(os.rename)
renames = to_coro(os.renames)
replace = to_coro(os.replace)
rmdir = to_coro(os.rmdir)

scandir = to_coro(os.scandir)
stat = to_coro(os.stat)
symlink = to_coro(os.symlink)

unlink = to_coro(os.unlink)


if hasattr(os, "link"):
    __all__ += ["link"]
    link = to_coro(os.link)
if hasattr(os, "sendfile"):
    __all__ += ["sendfile"]
    sendfile = to_coro(os.sendfile)
if hasattr(os, "statvfs"):
    __all__ += ["statvfs"]
    statvfs = to_coro(os.statvfs)
