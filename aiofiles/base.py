"""Various base classes."""
import asyncio

from ._compat import PY_35


class AsyncBase:
    def __init__(self, file, loop, executor):
        self._file = file
        self._loop = loop
        self._executor = executor

    if PY_35:
        @asyncio.coroutine
        def __aiter__(self):
            """We are our own iterator."""
            return self

        @asyncio.coroutine
        def __anext__(self):
            """Simulate normal file iteration."""
            line = yield from self.readline()
            if line:
                return line
            else:
                raise StopAsyncIteration

if PY_35:
    from collections.abc import Coroutine
    base = Coroutine
else:
    base = object


class _ContextManager(base):
    __slots__ = ('_coro', '_obj')

    def __init__(self, coro):
        self._coro = coro
        self._obj = None

    def send(self, value):
        return self._coro.send(value)

    def throw(self, typ, val=None, tb=None):
        if val is None:
            return self._coro.throw(typ)
        elif tb is None:
            return self._coro.throw(typ, val)
        else:
            return self._coro.throw(typ, val, tb)

    def close(self):
        return self._coro.close()

    @property
    def gi_frame(self):
        return self._coro.gi_frame

    @property
    def gi_running(self):
        return self._coro.gi_running

    @property
    def gi_code(self):
        return self._coro.gi_code

    def __next__(self):
        return self.send(None)

    @asyncio.coroutine
    def __iter__(self):
        resp = yield from self._coro
        return resp

    if PY_35:
        def __await__(self):
            resp = yield from self._coro
            return resp

        @asyncio.coroutine
        def __aenter__(self):
            self._obj = yield from self._coro
            return self._obj

        @asyncio.coroutine
        def __aexit__(self, exc_type, exc, tb):
            self._obj.close()
            self._obj = None


class AiofilesContextManager(_ContextManager):
    """An adjusted async context manager for aiofiles."""
    if PY_35:
        @asyncio.coroutine
        def __aexit__(self, exc_type, exc_val, exc_tb):
            yield from self._obj.close()
            self._obj = None

