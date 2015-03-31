"""Various base classes."""


class AsyncBase:
    def __init__(self, file, loop, executor):
        self._file = file
        self._loop = loop
        self._executor = executor
