# -*- coding: utf-8 -*-
from .base import AiofilesContextManager
from functools import partial
from tempfile import NamedTemporaryFile, TemporaryFile
from .threadpool.binary import AsyncFileIO
import asyncio


def AioTemporaryFile(mode='w+b', buffering=-1, encoding=None,
                      newline=None, suffix=None, prefix=None,
                      dir=None, ):
    return AiofilesContextManager(_wrap(TemporaryFile, loop=None, executor=None, mode=mode,
                 buffering=buffering, encoding=encoding,
                      newline=newline, suffix=suffix, prefix=prefix,
                      dir=dir))


def NamedAioTemporaryFile(mode='w+b', buffering=-1, encoding=None,
                      newline=None, suffix=None, prefix=None,
                      dir=None, delete=True):
    return AiofilesContextManager(_wrap(NamedTemporaryFile, loop=None, executor=None, mode=mode,
                 buffering=buffering, encoding=encoding,
                      newline=newline, suffix=suffix, prefix=prefix,
                      dir=dir,  delete=delete))


def _wrap(callable, loop=None, executor=None, *args, **kargs):
    if loop is None:
        loop = asyncio.get_event_loop()
    cb = partial(callable, *args, **kargs)
    f = yield from loop.run_in_executor(executor, cb)

    return AsyncFileIO(f, loop=loop, executor=executor)