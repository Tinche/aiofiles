import asyncio
import time
from collections.abc import AsyncIterable, Iterable, Sequence
from typing import Any, Union

import pytest

from aiofiles.base import to_agen, wrap


class TestToAsyncGeneratorWrapper:
    """Test suite for the `to_agen` decorator."""

    def _doiter(
        self,
        data: Iterable,
        *,
        with_timeout: float = 0.001,
        raise_if_exception: bool = False,
    ):
        for datum in data:
            if raise_if_exception and isinstance(datum, Exception):
                raise datum
            time.sleep(with_timeout)
            yield datum
        return 42

    @pytest.mark.parametrize(
        "seq",
        [
            "",
            "A",
            "AB",
            "ABC",
            [1, 2, [3, 4]],
            [None, None, None],
            [Exception(), ValueError(), TypeError(), BaseException()],
            [object(), object()],
            [
                1,
                [2],
                None,
                {3},
                Exception(),
                {"a": "b"},
                "str",
                object(),
                None,
                BaseException(),
                object(),
                None,
                object(),
            ],
        ],
    )
    async def test_basic_iterations(self, seq: Sequence) -> None:
        adoiter = to_agen(self._doiter)
        assert [i async for i in adoiter(seq)] == list(seq)

    async def _do_aiter(
        self, ait: AsyncIterable, *, global_acc: list, lock: asyncio.Lock
    ) -> list:
        items: list = []
        async for item in ait:
            async with lock:
                items.append(item)
                global_acc.append(item)
            # `async for` does not responsible for coroutine switching
            # so we need to yield control back to the event loop
            await asyncio.sleep(0)
        return items

    async def test_non_sequential_execution(self) -> None:
        lock = asyncio.Lock()
        collections: list[Sequence] = ["Aiofiles", tuple("Rocks"), [42, 21]]
        accumulator: list[str] = []
        tasks: list[asyncio.Task] = []

        for collection in collections:
            task = asyncio.create_task(
                self._do_aiter(
                    to_agen(self._doiter)(collection),
                    global_acc=accumulator,
                    lock=lock,
                )
            )
            tasks.append(task)
        results = await asyncio.gather(*tasks)

        for idx, collection in enumerate(collections):
            lc = list(collection)
            assert lc == results[idx]
            assert lc not in accumulator

    async def test_aiter_exhaustion(self) -> None:
        adoiter = to_agen(self._doiter)
        seq = [None, object(), Exception()]
        agen = adoiter(seq)
        assert [i async for i in agen] == seq
        assert [i async for i in agen] == []

    async def test_same_aiter_multiple_calls(self) -> None:
        adoiter = to_agen(self._doiter)
        seq = [None, object(), Exception()]
        for _ in range(2):
            assert [i async for i in adoiter(seq)] == seq

    async def test_exception_raised(self) -> None:
        adoiter = to_agen(self._doiter)
        seq = [3, 2, 1, ZeroDivisionError("zero"), -1]
        res: Union[None, list] = None
        with pytest.raises(ZeroDivisionError):
            res = [i async for i in adoiter(seq, raise_if_exception=True)]
        assert res is None


class TestToCoroutineWrapper:
    """Test suite for the wrap decorator."""

    def _do_io(self, *, with_timeout: float = 0.001, with_result: Any = 42) -> Any:
        time.sleep(with_timeout)
        return with_result

    async def test_wrap(self) -> None:
        tasks: list[asyncio.Task] = []
        seconds = list(range(1, 11))
        time_coef = 0.001

        start = time.time()
        for second in seconds:
            task = asyncio.create_task(
                wrap(self._do_io)(with_timeout=time_coef * second, with_result=second)
            )
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        assert seconds[0] * time_coef < elapsed < seconds[0]
        assert all(result == answer for result, answer in zip(results, seconds))
