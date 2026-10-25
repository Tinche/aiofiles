import asyncio
import io
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from aiofiles.threadpool.binary import AsyncBufferedReader, AsyncIndirectBufferedReader


@pytest.mark.parametrize("indirect", [False, True])
async def test_readinto1_runs_in_executor(indirect):
    loop_thread = threading.get_ident()
    calls = []

    class Reader(io.BufferedReader):
        def readinto1(self, buffer):
            calls.append(threading.get_ident())
            return super().readinto1(buffer)

    with Reader(io.BytesIO(b"abcdef")) as reader, ThreadPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        if indirect:
            wrapped = AsyncIndirectBufferedReader(
                "reader", loop, executor, lambda: reader
            )
        else:
            wrapped = AsyncBufferedReader(reader, loop, executor)
        buffer = bytearray(3)
        assert await wrapped.readinto1(buffer) == 3
        assert buffer == b"abc"
        assert await wrapped.readinto1(buffer) == 3
        assert buffer == b"def"
        assert await wrapped.readinto1(buffer) == 0

    assert len(calls) == 3
    assert all(thread != loop_thread for thread in calls)
