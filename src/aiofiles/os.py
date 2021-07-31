"""Async executor versions of file functions from the os module."""
import asyncio
from functools import partial, wraps
import os
from typing import Union
from pathlib import Path, _ignore_error as pathlib_ignore_error


def wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


stat = wrap(os.stat)
rename = wrap(os.rename)
remove = wrap(os.remove)
mkdir = wrap(os.mkdir)
rmdir = wrap(os.rmdir)

class path:
    @staticmethod
    async def exists(path: Union[Path, str]) -> bool:
        try:
            await stat(str(path))
        except OSError as e:
            if not pathlib_ignore_error(e):
                raise
            return False
        except ValueError:
            # Non-encodable path
            return False
        return True

if hasattr(os, "sendfile"):
    sendfile = wrap(os.sendfile)
