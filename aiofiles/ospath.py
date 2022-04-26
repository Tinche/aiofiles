# -*- coding: utf-8 -*-
"""Async versions of file functions from the os.path module."""

from os import path

from aiofiles.base import asyncify


exists = asyncify(path.exists)
isfile = asyncify(path.isfile)
isdir = asyncify(path.isdir)
islink = asyncify(path.islink)
getsize = asyncify(path.getsize)
getmtime = asyncify(path.getmtime)
getatime = asyncify(path.getatime)
getctime = asyncify(path.getctime)
samefile = asyncify(path.samefile)
sameopenfile = asyncify(path.sameopenfile)
