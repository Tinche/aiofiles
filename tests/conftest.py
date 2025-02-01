import pytest
from blockbuster import blockbuster_ctx


@pytest.fixture(autouse=True)
def blockbuster():
    with blockbuster_ctx("aiofiles"):
        yield
