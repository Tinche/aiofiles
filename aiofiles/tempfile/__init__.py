""" Async implementation of the tempfile module"""

__version__ = '0.1.0.dev0'

# Imports
import asyncio
from types import coroutine

from tempfile import (TemporaryFile as syncTemporaryFile,
                      NamedTemporaryFile as syncNamedTemporaryFile,
                      SpooledTemporaryFile as syncSpooledTemporaryFile,
                      TemporaryDirectory as syncTemporaryDirectory,
                      _TemporaryFileWrapper as syncTemporaryFileWrapper)
from io import (FileIO, TextIOBase, BufferedReader, BufferedWriter,
                BufferedRandom)
from functools import partial, singledispatch
from ..base import AiofilesContextManager
from ..threadpool.text import AsyncTextIOWrapper
from ..threadpool.binary import (AsyncBufferedIOBase, AsyncBufferedReader,
                                 AsyncFileIO)
from .temptypes import (AsyncSpooledTemporaryFile, AsyncTemporaryDirectory)

__all__ = ['named_temporary_file', 'temporary_file', 'spooled_temporary_file',
           'temporary_directory']

# Temporary file type constants
UNNAMED_TEMPFILE = 0
NAMED_TEMPFILE = 1
SPOOLED_TEMPFILE = 2


# ================================================================
# Public methods for async open and return of temp file/directory
# objects with async interface
# ================================================================
def named_temporary_file(mode='w+b', buffering=-1, encoding=None, newline=None,
                         suffix=None, prefix=None, dir=None, delete=True,
                         loop=None, executor=None):
    """Async open a named temporary file"""
    return AiofilesContextManager(
        _temporary_file(file_type=NAMED_TEMPFILE, mode=mode,
                        buffering=buffering, encoding=encoding,
                        newline=newline, suffix=suffix, prefix=prefix, dir=dir,
                        delete=delete, loop=loop, executor=executor))


def temporary_file(mode='w+b', buffering=-1, encoding=None, newline=None,
                   suffix=None, prefix=None, dir=None, loop=None,
                   executor=None):
    """Async open an unnamed temporary file"""
    return AiofilesContextManager(
        _temporary_file(file_type=UNNAMED_TEMPFILE, mode=mode,
                        buffering=buffering, encoding=encoding,
                        newline=newline, suffix=suffix, prefix=prefix, dir=dir,
                        loop=loop, executor=executor))


def spooled_temporary_file(max_size=0, mode='w+b', buffering=-1, encoding=None,
                           newline=None, suffix=None, prefix=None, dir=None,
                           loop=None, executor=None):
    """Async open a spooled temporary file"""
    return AiofilesContextManager(
        _temporary_file(file_type=SPOOLED_TEMPFILE, max_size=max_size,
                        mode=mode, buffering=buffering, encoding=encoding,
                        newline=newline, suffix=suffix, prefix=prefix, dir=dir,
                        loop=loop, executor=executor))


def temporary_directory(loop=None, executor=None):
    """Async open a temporary directory"""
    return AiofilesContextManager(_temporary_directory(loop=loop,
                                                       executor=executor))


# =========================================================
# Internal coroutines to open new temp files/directories
# =========================================================
@asyncio.coroutine
def _temporary_file(file_type=NAMED_TEMPFILE, mode='w+b', buffering=-1,
                    encoding=None, newline=None, suffix=None, prefix=None,
                    dir=None, delete=True, loop=None, executor=None,
                    max_size=0):
    """Async method to open a temporary file with async interface"""
    if loop is None:
        loop = asyncio.get_event_loop()

    if file_type == UNNAMED_TEMPFILE:
        sync_obj = syncTemporaryFile
    elif file_type == NAMED_TEMPFILE:
        sync_obj = syncNamedTemporaryFile
    elif file_type == SPOOLED_TEMPFILE:
        sync_obj = syncSpooledTemporaryFile
    else:
        raise ValueError('Invalid temporary file type {}'.format(file_type))

    cb = partial(sync_obj, mode=mode, buffering=buffering,
                 encoding=encoding, newline=newline, suffix=suffix,
                 prefix=prefix, dir=dir)

    if file_type == NAMED_TEMPFILE:
        cb = partial(cb, delete=delete)
    elif file_type == SPOOLED_TEMPFILE:
        cb = partial(cb, max_size=max_size)

    f = yield from loop.run_in_executor(executor, cb)

    if file_type in (UNNAMED_TEMPFILE, NAMED_TEMPFILE):
        # Wrap based on type of underlying IO object
        if type(f) is syncTemporaryFileWrapper:
            # _TemporaryFileWrapper was used (named files)
            result = wrap(f.file, f, loop=loop, executor=executor)
            # add name and delete properties
            result.name = f.name
            result.delete = f.delete
            return result
        else:
            # IO object was returned directly without wrapper
            return wrap(f, f, loop=loop, executor=executor)
    elif file_type == SPOOLED_TEMPFILE:
        # Single interface provided by SpooledTemporaryFile for all modes
        return AsyncSpooledTemporaryFile(f, loop=loop, executor=executor)


@coroutine
def _temporary_directory(loop=None, executor=None):
    """Async method to open a temporary directory with async interface"""
    if loop is None:
        loop = asyncio.get_event_loop()
    f = yield from loop.run_in_executor(executor, syncTemporaryDirectory)

    return AsyncTemporaryDirectory(f, loop=loop, executor=executor)


@singledispatch
def wrap(base_io_obj, file, *, loop=None, executor=None):
    """Wrap the object with interface based on type of underlying IO"""
    raise TypeError('Unsupported IO type: {}'.format(base_io_obj))


@wrap.register(TextIOBase)
def _(base_io_obj, file, *, loop=None, executor=None):
    return AsyncTextIOWrapper(file, loop=loop, executor=executor)


@wrap.register(BufferedWriter)
def _(base_io_obj, file, *, loop=None, executor=None):
    return AsyncBufferedIOBase(file, loop=loop, executor=executor)


@wrap.register(BufferedReader)
@wrap.register(BufferedRandom)
def _(base_io_obj, file, *, loop=None, executor=None):
    return AsyncBufferedReader(file, loop=loop, executor=executor)


@wrap.register(FileIO)
def _(base_io_obj, file, *, loop=None, executor=None):
    return AsyncFileIO(file, loop=loop, executor=executor)
