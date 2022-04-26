# -*- coding: utf-8 -*-
"""Unit-test module for isasync function."""

import asyncio
import inspect
from typing import AsyncGenerator, Generator
from warnings import catch_warnings, simplefilter

import pytest

from aiofiles.base import isasync


def foo() -> str:
    """Provides a regular function."""
    return "function"


def test_foo():
    """Test function."""
    assert foo() == 'function'


def gen() -> Generator:
    """Providdes a regular generator."""
    yield "generator"


def test_gen():
    """Test generator."""
    assert next(gen()) == 'generator'


async def afoo() -> str:
    """Provides a coroutine."""
    await asyncio.sleep(1)
    return "async function"


@pytest.mark.asyncio
async def test_afoo():
    """Test async function"""
    assert await afoo() == 'async function'


async def agen() -> AsyncGenerator:
    """Provides an async generator."""
    await asyncio.sleep(1)
    yield "async generator"


@pytest.mark.asyncio
async def test_agen():
    """Test async generator."""
    assert await agen().__anext__() == 'async generator'


with catch_warnings():
    simplefilter("ignore", category=DeprecationWarning)

    @asyncio.coroutine
    def old_style_coroutine() -> Generator:
        """Provides a generator-based coroutine (an outdated way)."""
        yield from asyncio.sleep(1)
        return "an old style generator-based coroutine"


@pytest.mark.asyncio
async def test_old_style_coroutine():
    """Test old-fashioned coroutine."""
    res = await old_style_coroutine()
    assert res == "an old style generator-based coroutine"


class TestIsAsync:
    """Test suite for isasync function."""

    def test_isasync_function_false(self):
        """Returns False if isasync(function)."""
        assert inspect.isfunction(foo) and not isasync(foo)

    def test_isasync_function_return_false(self):
        """Returns False if isasync(function())."""
        assert not isasync(foo())

    def test_isasync_generator_function_false(self):
        """Returns False if isasync(generator_function)."""
        assert inspect.isgeneratorfunction(gen) and not isasync(gen)

    def test_isasync_generator_false(self):
        """Returns False if isasync(generator())."""
        assert inspect.isgenerator(gen()) and not isasync(gen())

    def test_isasync_async_function_true(self):
        """Returns True if isasync(asyncfunction)."""
        assert inspect.iscoroutinefunction(afoo) and isasync(afoo)

    def test_isasync_coroutine_true(self):
        """Returns True if isasync(asyncfunction())."""
        coro = afoo()
        assert inspect.iscoroutine(coro) and isasync(coro)
        coro.close()

    def test_isasync_async_generator_function_true(self):
        """Returns True if isasync(asyncgen)."""
        inspect.isasyncgenfunction(agen) and isasync(agen)

    def test_isasync_async_generator_true(self):
        """Returns True if isasync(asyncgen())."""
        coro = agen()
        inspect.isasyncgen(coro) and isasync(coro)

    def test_isasync_old_coroutine_true(self):
        """Returns True if isasync(old_coroutine())."""
        coro = old_style_coroutine()
        print(f"ISASYNC = {isasync(coro)}")
        assert asyncio.iscoroutine(coro) and isasync(coro)
