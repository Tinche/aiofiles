import asyncio
import threading
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from functools import partial, wraps
from queue import Queue
from typing import Any, Union


def to_agen(cb: Callable) -> Callable:
    @wraps(cb)
    async def _wrapper(*args, **kwargs) -> AsyncIterator:
        def _iterate(
            q: Queue, *, next_item_event: threading.Event, eos_item: object
        ) -> None:
            nonlocal exc
            try:
                for row in cb(*args, **kwargs):
                    next_item_event.clear()
                    q.put(row)
                    # Only the consumer can unblock the next iteration
                    next_item_event.wait()
            except Exception as e:  # noqa: BLE001
                exc = e
            finally:
                # The End-Of-Stream entity must be put anyway
                q.put(eos_item)

        loop = asyncio.get_running_loop()
        queue: Queue = Queue()  # thread-safe
        ready_for_item = threading.Event()
        end_of_stream_item = object()  # sentinel value
        gen = partial(
            _iterate,
            q=queue,
            next_item_event=ready_for_item,
            eos_item=end_of_stream_item,
        )
        loop.run_in_executor(None, gen)

        exc: Union[None, Exception] = None
        while True:
            item = queue.get()
            queue.task_done()
            if item is end_of_stream_item:
                break
            ready_for_item.set()
            yield item
        queue.join()
        if exc:
            raise exc

    return _wrapper


def wrap(cb: Callable) -> Callable:
    @wraps(cb)
    async def _wrapper(*args, **kwargs) -> Any:
        return await asyncio.to_thread(cb, *args, **kwargs)

    return _wrapper


class AsyncBase:
    def __init__(self, file, loop, executor):
        self._file = file
        self._executor = executor
        self._ref_loop = loop

    @property
    def _loop(self):
        return self._ref_loop or asyncio.get_running_loop()

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
        await asyncio.get_running_loop().run_in_executor(
            None, self._obj._file.__exit__, exc_type, exc_val, exc_tb
        )
        self._obj = None
