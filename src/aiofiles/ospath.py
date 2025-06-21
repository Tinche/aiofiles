"""Async executor versions of file functions from the os.path module."""

from os import path

from .base import to_coro

__all__ = [
    "abspath",
    "getatime",
    "getctime",
    "getmtime",
    "getsize",
    "exists",
    "isdir",
    "isfile",
    "islink",
    "ismount",
    "samefile",
    "sameopenfile",
]

abspath = to_coro(path.abspath)

getatime = to_coro(path.getatime)
getctime = to_coro(path.getctime)
getmtime = to_coro(path.getmtime)
getsize = to_coro(path.getsize)

exists = to_coro(path.exists)

isdir = to_coro(path.isdir)
isfile = to_coro(path.isfile)
islink = to_coro(path.islink)
ismount = to_coro(path.ismount)

samefile = to_coro(path.samefile)
sameopenfile = to_coro(path.sameopenfile)
