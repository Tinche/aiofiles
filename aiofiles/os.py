"""Async executor versions of file functions from the os module."""
import asyncio
from functools import partial, wraps
import os


def wrap(func):
    @asyncio.coroutine
    @wraps(func)
    def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return loop.run_in_executor(executor, pfunc)

    return run


stat = wrap(os.stat)

if hasattr(os, "sendfile"):
    sendfile = wrap(os.sendfile)
