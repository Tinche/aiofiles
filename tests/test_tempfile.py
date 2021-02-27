import asyncio
import pytest
from aiofiles import tempfile
import os
import io


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["r+", "w+", "rb+", "wb+"])
async def test_temporary_file(mode):
    """Test temporary file."""
    data = b'Hello World!\n' if 'b' in mode else 'Hello World!\n' 

    async with tempfile.TemporaryFile(mode=mode) as f:
        for i in range(3):
            await f.write(data) 

        await f.flush()
        await f.seek(0)

        async for line in f:
            assert line == data
        

@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["r+", "w+", "rb+", "wb+"])
async def test_named_temporary_file(mode):
    """Test named temporary file."""
    data = b'Hello World!' if 'b' in mode else 'Hello World!' 
    filename = None

    async with tempfile.NamedTemporaryFile(mode=mode) as f:
        await f.write(data)
        await f.flush()
        await f.seek(0)
        assert await f.read() == data

        filename = f.name
        assert os.path.exists(filename)
        assert os.path.isfile(filename)
        assert f.delete

    assert not os.path.exists(filename)

        
@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["r+", "w+", "rb+", "wb+"])
async def test_spooled_temporary_file(mode):
    """Test spooled temporary file."""
    data = b'Hello World!' if 'b' in mode else 'Hello World!' 

    async with tempfile.SpooledTemporaryFile(max_size=len(data)+1, mode=mode) as f:
        await f.write(data)
        await f.flush()
        if 'b' in mode:
            assert type(f._file._file) is io.BytesIO

        await f.write(data)
        await f.flush()
        if 'b' in mode:
            assert type(f._file._file) is not io.BytesIO

        await f.seek(0)
        assert await f.read() == data + data


@pytest.mark.asyncio
async def test_temporary_directory():
    """Test temporary directory."""
    dir_path = None

    async with tempfile.TemporaryDirectory() as d:
        dir_path = d
        assert os.path.exists(dir_path)
        assert os.path.isdir(dir_path)

    assert not os.path.exists(dir_path)
