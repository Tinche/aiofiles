"""Async executor versions of file functions from the os module."""
import asyncio
from functools import partial, wraps
import os

import anyio


def wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        pfunc = partial(func, *args, **kwargs)
        if loop is not None or executor is not None:
            if loop is None:
                loop = asyncio.get_event_loop()
            return await loop.run_in_executor(executor, pfunc)
        else:
            return await anyio.run_sync_in_worker_thread(pfunc)

    return run


stat = wrap(os.stat)
rename = wrap(os.rename)
remove = wrap(os.remove)
mkdir = wrap(os.mkdir)
rmdir = wrap(os.rmdir)

if hasattr(os, "sendfile"):
    sendfile = wrap(os.sendfile)
