"""Async executor versions of file functions from the os.path module."""

from os import path

from aiofiles.base import wrap


abspath = wrap(path.abspath)

exists = wrap(path.exists)

getsize = wrap(path.getsize)
getmtime = wrap(path.getmtime)
getatime = wrap(path.getatime)
getctime = wrap(path.getctime)

isfile = wrap(path.isfile)
isdir = wrap(path.isdir)
islink = wrap(path.islink)
ismount = wrap(path.ismount)

samefile = wrap(path.samefile)
sameopenfile = wrap(path.sameopenfile)
