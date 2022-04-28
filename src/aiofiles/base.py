# -*- coding: utf-8 -*-
"""Various base classes."""

from asyncio import get_running_loop
from collections.abc import Coroutine
from contextvars import copy_context
from functools import partial, wraps
from inspect import (
    isasyncgen,
    isasyncgenfunction,
    isawaitable,
    iscoroutine,
    iscoroutinefunction,
)
from types import coroutine


def isasync(obj: object) -> bool:
    """Determine if an object is asynchronous,

    Args:
        obj (object): _description_

    Returns:
        bool: True if an object is asynchronous
    """
    foos = (
        isasyncgen,
        isasyncgenfunction,
        isawaitable,
        iscoroutine,
        iscoroutinefunction,
    )
    return any(f(obj) for f in foos)


def asyncify(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = get_running_loop()
        ctx = copy_context()
        pfunc = partial(ctx.run, func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


class AsyncBase:
    def __init__(self, file, loop, executor):
        self._file = file
        self._loop = loop
        self._executor = executor

    def __aiter__(self):
        """We are our own iterator."""
        return self

    def __repr__(self):
        return super().__repr__() + " wrapping " + repr(self._file)

    async def __anext__(self):
        """Simulate normal file iteration."""
        line = await self.readline()
        if line:
            return line
        else:
            raise StopAsyncIteration


class _ContextManager(Coroutine):
    __slots__ = ("_coro", "_obj")

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

    @coroutine
    def __iter__(self):
        resp = yield from self._coro
        return resp

    def __await__(self):
        resp = yield from self._coro
        return resp

    async def __anext__(self):
        resp = await self._coro
        return resp

    async def __aenter__(self):
        self._obj = await self._coro
        return self._obj

    async def __aexit__(self, exc_type, exc, tb):
        self._obj.close()
        self._obj = None


class AiofilesContextManager(_ContextManager):
    """An adjusted async context manager for aiofiles."""

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._obj.close()
        self._obj = None
