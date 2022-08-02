"""Async versions of file functions from the os module."""
import os

from . import ospath as path  # noqa: F401
from .base import asyncify

stat = asyncify(os.stat)
rename = asyncify(os.rename)
renames = asyncify(os.renames)
replace = asyncify(os.replace)
remove = asyncify(os.remove)
unlink = asyncify(os.unlink)
mkdir = asyncify(os.mkdir)
makedirs = asyncify(os.makedirs)
rmdir = asyncify(os.rmdir)
removedirs = asyncify(os.removedirs)
link = asyncify(os.link)
symlink = asyncify(os.symlink)
readlink = asyncify(os.readlink)

if hasattr(os, "sendfile"):
    sendfile = asyncify(os.sendfile)
