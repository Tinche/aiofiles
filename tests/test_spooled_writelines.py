import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import get_ident

import pytest

from aiofiles import tempfile


@pytest.mark.parametrize("mode", ["wb+", "w+"])
@pytest.mark.parametrize("custom_executor", [False, True])
async def test_rollover_during_writelines(mode, custom_executor):
    chunk = b"abcd" if "b" in mode else "abcd"
    caller_thread = get_ident()
    observations = []

    with ThreadPoolExecutor(max_workers=1) as pool:
        executor = pool if custom_executor else None
        worker_thread = await asyncio.get_running_loop().run_in_executor(
            pool, get_ident
        )
        async with tempfile.SpooledTemporaryFile(
            max_size=len(chunk), mode=mode, executor=executor
        ) as f:

            def chunks():
                yield chunk
                observations.append((f._file._rolled, get_ident()))
                yield chunk
                observations.append((f._file._rolled, get_ident()))
                yield chunk

            assert await f.writelines(chunks()) is None
            assert observations[0] == (False, caller_thread)
            assert observations[1][0] is True
            assert observations[1][1] != caller_thread
            if custom_executor:
                assert observations[1][1] == worker_thread
            await f.seek(0)
            assert await f.read() == chunk * 3


@pytest.mark.parametrize("mode", ["wb+", "w+"])
@pytest.mark.parametrize("producer_error", [False, True])
async def test_writelines_error_after_rollover(mode, producer_error):
    chunk = b"abcdef" if "b" in mode else "abcdef"

    async with tempfile.SpooledTemporaryFile(max_size=4, mode=mode) as f:

        def chunks():
            yield chunk
            if producer_error:
                msg = "producer failed"
                raise RuntimeError(msg)
            yield None

        with pytest.raises(RuntimeError if producer_error else TypeError):
            await f.writelines(chunks())
        assert f._file._rolled
        await f.seek(0)
        assert await f.read() == chunk


@pytest.mark.parametrize("mode", ["wb+", "w+"])
@pytest.mark.parametrize("max_size", [0, 4, 8, 9])
@pytest.mark.parametrize("already_rolled", [False, True])
async def test_writelines_spool_limits(mode, max_size, already_rolled):
    chunk = b"abcd" if "b" in mode else "abcd"

    async with tempfile.SpooledTemporaryFile(max_size=max_size, mode=mode) as f:
        if already_rolled:
            await f.rollover()
        assert await f.writelines(iter([chunk, chunk])) is None
        assert f._file._rolled == (already_rolled or max_size == 4)
        await f.seek(0)
        assert await f.read() == chunk * 2


@pytest.mark.parametrize("mode", ["wb+", "w+"])
async def test_empty_writelines_does_not_rollover(mode):
    async with tempfile.SpooledTemporaryFile(max_size=4, mode=mode) as f:
        assert await f.writelines(iter([])) is None
        assert not f._file._rolled
        await f.seek(0)
        assert await f.read() == (b"" if "b" in mode else "")
