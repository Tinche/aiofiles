import asyncio
import inspect
import os

from .base import AiofilesContextManager, AsyncBase
from .threadpool import run_threadpool
from .threadpool.binary import AsyncBufferedIOBase
from .threadpool.utils import (
    delegate_to_executor,
    proxy_method_directly,
    proxy_property_directly,
)

import zipfile
from zipfile import (
    BadZipFile,
    BadZipfile,
    error,
    ZIP_STORED,
    ZIP_DEFLATED,
    ZIP_BZIP2,
    ZIP_LZMA,
    is_zipfile,
    ZipInfo,
    ZipFile,
    PyZipFile,
    LargeZipFile,
)

__all__ = zipfile.__all__

sync_is_zipfile = is_zipfile
sync_ZipFile = ZipFile
sync_PyZipFile = PyZipFile


def is_zipfile(filename, loop=None, executor=None):
    return run_threadpool(
        sync_is_zipfile, filename=filename, loop=loop, executor=executor
    )


def ZipFile(
    file, mode="r", compression=ZIP_STORED, allowZip64=True, loop=None, executor=None
):
    return AiofilesContextManager(
        run_threadpool(
            sync_ZipFile,
            file,
            mode,
            compression,
            allowZip64,
            loop=loop,
            executor=executor,
            async_wrap=AsyncZipFile,
        )
    )


def PyZipFile(
    file,
    mode="r",
    compression=ZIP_STORED,
    allowZip64=True,
    optimize=-1,
    loop=None,
    executor=None,
):
    return AiofilesContextManager(
        run_threadpool(
            sync_PyZipFile,
            file=file,
            mode=mode,
            compression=compression,
            allowZip64=allowZip64,
            optimize=optimize,
            loop=loop,
            executor=executor,
            async_wrap=AsyncPyZipFile,
        )
    )


@delegate_to_executor("readline", "peek", "read", "read1", "close")
@proxy_method_directly("__repr__", "readable")
class AsyncZipExtFile(AsyncBufferedIOBase):
    """
    The asyncio executor version of zipfile.ZipExtFile.

    Note that this class should never be instantiated except by ``AsyncZipFile``
    as ``ZipExtFile`` is itself only ever used by ``ZipFile``. 
    """


@delegate_to_executor(
    "testzip", "read", "extract", "extractall", "write", "writestr", "close"
)
@proxy_method_directly(
    "__repr__", "namelist", "infolist", "printdir", "getinfo", "setpassword"
)
@proxy_property_directly("comment")
class AsyncZipFile(AsyncBase):
    """The asyncio executor version of zipfile.ZipFile."""

    def open(self, name, mode="r", pwd=None, *, force_zip64=False):
        cb = self._file.open
        args = {
            'name': name,
            'mode': mode,
            'pwd': pwd,
            'loop': self._loop,
            'executor': self._executor,
            'force_zip64': force_zip64,
            'async_wrap': AsyncZipExtFile,
        }

        try:
            if 'force_zip64' not in inspect.signature(cb).parameters:
                del args['force_zip64']
        except (ValueError, TypeError):
            pass  # just hope that force_zip64 exists

        return AiofilesContextManager(run_threadpool(cb, **args))


@delegate_to_executor("writepy")
class AsyncPyZipFile(AsyncZipFile):
    """The asyncio executor version of zipfile.PyZipFile."""
