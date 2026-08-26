"""Asynchronous version of the os module."""

import os

from . import ospath as path
from .base import to_agen, wrap

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
    "walk",
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
walk = to_agen(os.walk)


if hasattr(os, "fwalk"):
    __all__ += ["fwalk"]
    fwalk = to_agen(os.fwalk)
if hasattr(os, "link"):
    __all__ += ["link"]
    link = wrap(os.link)
if hasattr(os, "sendfile"):
    __all__ += ["sendfile"]
    sendfile = wrap(os.sendfile)
if hasattr(os, "statvfs"):
    __all__ += ["statvfs"]
    statvfs = wrap(os.statvfs)
