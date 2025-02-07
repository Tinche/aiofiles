from io import FileIO

import pytest

from aiofiles.threadpool import wrap


@pytest.mark.parametrize("entity", [int, [1, 2, 3], lambda x: x**x, FileIO])
def test_threadpool_wrapper_negative(entity):
    """Raising TypeError when wrapping unsupported entities."""

    with pytest.raises(TypeError):
        wrap(entity)
