from aiofiles.threadpool import wrap

import pytest


def test_unsupported_wrap():
    """Raising TypeError when wrapping unsupported entities."""

    with pytest.raises(TypeError):
        wrap(int)
