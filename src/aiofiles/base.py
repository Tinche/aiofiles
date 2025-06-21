from asyncio import get_running_loop, to_thread
from collections.abc import AsyncIterator, Awaitable, Callable, Coroutine
from contextlib import AbstractAsyncContextManager
from functools import partial, wraps
from queue import Empty, Queue
from warnings import warn


def to_agen(func: Callable) -> AsyncIterator:
    """Converts the routine `func` into an async generator function.

    Args:
        func: A generator function.

    Returns:
        An asynchronous generator function.
    """

    @wraps(func)
    async def _wrapper(*args, **kwargs) -> AsyncIterator:
        def _generate(q: Queue):
            nonlocal is_over
            try:
                for row in func(*args, **kwargs):
                    q.put_nowait(row)
            finally:
                is_over = True

        loop = get_running_loop()
        queue: Queue = Queue()

        is_over = False

        gen = partial(_generate, q=queue)
        loop.run_in_executor(None, gen)
        while True:
            if is_over and queue.empty():
                break
            try:
                item = queue.get_nowait()
                queue.task_done()
                yield item
            except Empty:
                pass
        queue.join()

    return _wrapper


def to_coro(func: Callable) -> Callable:
    """Converts the routine `func` into a coroutine.

    The returned coroutine function runs the decorated function
    in a separate thread.

    Args:
        func: A routine (regular function).

    Returns:
        A coroutine function.
    """

    @wraps(func)
    async def _wrapper(*args, **kwargs) -> Coroutine:
        return await to_thread(func, *args, **kwargs)

    return _wrapper


def wrap(func: Callable) -> Callable:
    warn(
        "scheduled to removal, consider using to_coro", DeprecationWarning, stacklevel=1
    )
    return to_coro(func)


class AsyncBase:
    def __init__(self, file, loop, executor):
        self._file = file
        self._executor = executor
        self._ref_loop = loop

    @property
    def _loop(self):
        return self._ref_loop or get_running_loop()

    def __aiter__(self):
        return self

    def __repr__(self):
        return super().__repr__() + " wrapping " + repr(self._file)

    async def __anext__(self):
        """Simulate normal file iteration."""

        if line := await self.readline():
            return line
        raise StopAsyncIteration


class AsyncIndirectBase(AsyncBase):
    def __init__(self, name, loop, executor, indirect):
        self._indirect = indirect
        self._name = name
        super().__init__(None, loop, executor)

    @property
    def _file(self):
        return self._indirect()

    @_file.setter
    def _file(self, v):
        pass  # discard writes


class AiofilesContextManager(Awaitable, AbstractAsyncContextManager):
    """An adjusted async context manager for aiofiles."""

    __slots__ = ("_coro", "_obj")

    def __init__(self, coro):
        self._coro = coro
        self._obj = None

    def __await__(self):
        if self._obj is None:
            self._obj = yield from self._coro.__await__()
        return self._obj

    async def __aenter__(self):
        return await self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await get_running_loop().run_in_executor(
            None, self._obj._file.__exit__, exc_type, exc_val, exc_tb
        )
        self._obj = None
