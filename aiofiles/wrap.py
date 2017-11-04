# -*-coding: utf-8 -*-
from io import (FileIO, TextIOBase, BufferedReader, BufferedWriter,
                BufferedRandom)
from .threadpool.binary import AsyncBufferedIOBase, AsyncBufferedReader, AsyncFileIO
from .threadpool.text import AsyncTextIOWrapper
from ._compat import singledispatch


@singledispatch
def wrap(file, *, loop=None, executor=None):
    raise TypeError('Unsupported io type: {}.'.format(file))


@wrap.register(TextIOBase)
def _(file, *, loop=None, executor=None):
    return AsyncTextIOWrapper(file, loop=loop, executor=executor)


@wrap.register(BufferedWriter)
def _(file, *, loop=None, executor=None):
    return AsyncBufferedIOBase(file, loop=loop, executor=executor)


@wrap.register(BufferedReader)
@wrap.register(BufferedRandom)
def _(file, *, loop=None, executor=None):
    return AsyncBufferedReader(file, loop=loop, executor=executor)


@wrap.register(FileIO)
def _(file, *, loop=None, executor=None):
    return AsyncFileIO(file, loop, executor)
