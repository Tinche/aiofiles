from aiofiles.threadpool import wrap

import pytest


@pytest.mark.parametrize("entity", [int, [1, 2, 3], lambda x: x**x])
def test_threadpool_wrapper(entity):
    """Raising TypeError when wrapping unsupported entities."""

    with pytest.raises(TypeError):
        wrap(entity)
