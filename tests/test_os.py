"""Tests for asyncio's os module."""
import aiofiles.os
import asyncio
import os
from os import stat
from os.path import join, dirname, exists, isdir
import pytest
import platform


@pytest.mark.asyncio
async def test_stat():
    """Test the stat call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")

    stat_res = await aiofiles.os.stat(filename)

    assert stat_res.st_size == 10


@pytest.mark.asyncio
async def test_remove():
    """Test the remove call."""
    filename = join(dirname(__file__), "resources", "test_file2.txt")
    with open(filename, "w") as f:
        f.write("Test file for remove call")

    assert exists(filename)
    await aiofiles.os.remove(filename)
    assert exists(filename) is False


@pytest.mark.asyncio
async def test_unlink():
    """Test the unlink call."""
    filename = join(dirname(__file__), "resources", "test_file2.txt")
    with open(filename, "w") as f:
        f.write("Test file for unlink call")

    assert exists(filename)
    await aiofiles.os.unlink(filename)
    assert exists(filename) is False


@pytest.mark.asyncio
async def test_mkdir_and_rmdir():
    """Test the mkdir and rmdir call."""
    directory = join(dirname(__file__), "resources", "test_dir")
    await aiofiles.os.mkdir(directory)
    assert isdir(directory)
    await aiofiles.os.rmdir(directory)
    assert exists(directory) is False


@pytest.mark.asyncio
async def test_rename():
    """Test the rename call."""
    old_filename = join(dirname(__file__), "resources", "test_file1.txt")
    new_filename = join(dirname(__file__), "resources", "test_file2.txt")
    await aiofiles.os.rename(old_filename, new_filename)
    assert exists(old_filename) is False and exists(new_filename)
    await aiofiles.os.rename(new_filename, old_filename)
    assert exists(old_filename) and exists(new_filename) is False


@pytest.mark.asyncio
async def test_renames():
    """Test the renames call."""
    old_filename = join(dirname(__file__), "resources", "test_file1.txt")
    new_filename = join(
        dirname(__file__), "resources", "subdirectory", "test_file2.txt"
    )
    await aiofiles.os.renames(old_filename, new_filename)
    assert exists(old_filename) is False and exists(new_filename)
    await aiofiles.os.renames(new_filename, old_filename)
    assert (
        exists(old_filename) and
        exists(new_filename) is False and
        exists(dirname(new_filename)) is False
    )


@pytest.mark.asyncio
async def test_replace():
    """Test the replace call."""
    old_filename = join(dirname(__file__), "resources", "test_file1.txt")
    new_filename = join(dirname(__file__), "resources", "test_file2.txt")

    await aiofiles.os.replace(old_filename, new_filename)
    assert exists(old_filename) is False and exists(new_filename)
    await aiofiles.os.replace(new_filename, old_filename)
    assert exists(old_filename) and exists(new_filename) is False

    with open(new_filename, "w") as f:
        f.write("Test file")
    assert exists(old_filename) and exists(new_filename)

    await aiofiles.os.replace(old_filename, new_filename)
    assert exists(old_filename) is False and exists(new_filename)
    await aiofiles.os.replace(new_filename, old_filename)
    assert exists(old_filename) and exists(new_filename) is False


@pytest.mark.skipif(
    "2.4" < platform.release() < "2.6.33",
    reason="sendfile() syscall doesn't allow file->file",
)
@pytest.mark.skipif(
    platform.system() == "Darwin",
    reason="sendfile() doesn't work on mac",
)
@pytest.mark.asyncio
async def test_sendfile_file(tmpdir):
    """Test the sendfile functionality, file-to-file."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    tmp_filename = tmpdir.join("tmp.bin")

    with open(filename) as f:
        contents = f.read()

    input_file = await aiofiles.open(filename)
    output_file = await aiofiles.open(str(tmp_filename), mode="w+")

    size = (await aiofiles.os.stat(filename)).st_size

    input_fd = input_file.fileno()
    output_fd = output_file.fileno()

    await aiofiles.os.sendfile(output_fd, input_fd, 0, size)

    await output_file.seek(0)

    actual_contents = await output_file.read()
    actual_size = (await aiofiles.os.stat(str(tmp_filename))).st_size

    assert contents == actual_contents
    assert size == actual_size


@pytest.mark.asyncio
async def test_sendfile_socket(unused_tcp_port):
    """Test the sendfile functionality, file-to-socket."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")

    with open(filename, mode="rb") as f:
        contents = f.read()

    async def serve_file(_, writer):
        out_fd = writer.transport.get_extra_info("socket").fileno()
        size = (await aiofiles.os.stat(filename)).st_size
        in_file = await aiofiles.open(filename)
        try:
            in_fd = in_file.fileno()
            await aiofiles.os.sendfile(out_fd, in_fd, 0, size)
        finally:
            await in_file.close()
            await writer.drain()
            writer.close()

    server = await asyncio.start_server(serve_file, port=unused_tcp_port)

    reader, writer = await asyncio.open_connection("127.0.0.1", unused_tcp_port)
    actual_contents = await reader.read()
    writer.close()

    assert contents == actual_contents
    server.close()

    await server.wait_closed()


@pytest.mark.asyncio
async def test_exists():
    """Test path.exists call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.exists(filename)
    assert result


@pytest.mark.asyncio
async def test_isfile():
    """Test path.isfile call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.isfile(filename)
    assert result


@pytest.mark.asyncio
async def test_isdir():
    """Test path.isdir call."""
    filename = join(dirname(__file__), "resources")
    result = await aiofiles.os.path.isdir(filename)
    assert result


@pytest.mark.asyncio
async def test_islink():
    """Test the path.islink call."""
    src_filename = join(dirname(__file__), "resources", "test_file1.txt")
    dst_filename = join(dirname(__file__), "resources", "test_file2.txt")
    await aiofiles.os.symlink(src_filename, dst_filename)
    assert await aiofiles.os.path.islink(dst_filename)
    await aiofiles.os.remove(dst_filename)


@pytest.mark.asyncio
async def test_getsize():
    """Test path.getsize call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.getsize(filename)
    assert result == 10


@pytest.mark.asyncio
async def test_samefile():
    """Test path.samefile call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.samefile(filename, filename)
    assert result


@pytest.mark.asyncio
async def test_sameopenfile():
    """Test path.samefile call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.samefile(filename, filename)
    assert result


@pytest.mark.asyncio
async def test_getmtime():
    """Test path.getmtime call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.getmtime(filename)
    assert result


@pytest.mark.asyncio
async def test_getatime():
    """Test path.getatime call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.getatime(filename)
    assert result


@pytest.mark.asyncio
async def test_getctime():
    """Test path. call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.getctime(filename)
    assert result


@pytest.mark.asyncio
async def test_link():
    """Test the link call."""
    src_filename = join(dirname(__file__), "resources", "test_file1.txt")
    dst_filename = join(dirname(__file__), "resources", "test_file2.txt")
    initial_src_nlink = stat(src_filename).st_nlink
    await aiofiles.os.link(src_filename, dst_filename)
    assert (
        exists(src_filename)
        and exists(dst_filename)
        and (stat(src_filename).st_ino == stat(dst_filename).st_ino)
        and (stat(src_filename).st_nlink == initial_src_nlink + 1)
        and (stat(dst_filename).st_nlink == 2)
    )
    await aiofiles.os.remove(dst_filename)
    assert (
        exists(src_filename)
        and exists(dst_filename) is False
        and (stat(src_filename).st_nlink == initial_src_nlink)
    )


@pytest.mark.asyncio
async def test_symlink():
    """Test the symlink call."""
    src_filename = join(dirname(__file__), "resources", "test_file1.txt")
    dst_filename = join(dirname(__file__), "resources", "test_file2.txt")
    await aiofiles.os.symlink(src_filename, dst_filename)
    assert (
        exists(src_filename)
        and exists(dst_filename)
        and stat(src_filename).st_ino == stat(dst_filename).st_ino
    )
    await aiofiles.os.remove(dst_filename)
    assert exists(src_filename) and exists(dst_filename) is False


@pytest.mark.asyncio
async def test_readlink():
    """Test the readlink call."""
    src_filename = join(dirname(__file__), "resources", "test_file1.txt")
    dst_filename = join(dirname(__file__), "resources", "test_file2.txt")
    await aiofiles.os.symlink(src_filename, dst_filename)
    symlinked_path = await aiofiles.os.readlink(dst_filename)
    assert src_filename == symlinked_path
    await aiofiles.os.remove(dst_filename)


@pytest.mark.asyncio
async def test_listdir_empty_dir():
    """Test the listdir call when the dir is empty."""
    directory = join(dirname(__file__), "resources", "empty_dir")
    await aiofiles.os.mkdir(directory)
    dir_list = await aiofiles.os.listdir(directory)
    assert dir_list == []
    await aiofiles.os.rmdir(directory)


@pytest.mark.asyncio
async def test_listdir_dir_with_only_one_file():
    """Test the listdir call when the dir has one file."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    some_file = join(some_dir, "some_file.txt")
    await aiofiles.os.mkdir(some_dir)
    with open(some_file, "w") as f:
        f.write("Test file")
    dir_list = await aiofiles.os.listdir(some_dir)
    assert "some_file.txt" in dir_list
    await aiofiles.os.remove(some_file)
    await aiofiles.os.rmdir(some_dir)

@pytest.mark.asyncio
async def test_listdir_dir_with_only_one_dir():
    """Test the listdir call when the dir has one dir."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    other_dir = join(some_dir, "other_dir")
    await aiofiles.os.mkdir(some_dir)
    await aiofiles.os.mkdir(other_dir)
    dir_list = await aiofiles.os.listdir(some_dir)
    assert "other_dir" in dir_list
    await aiofiles.os.rmdir(other_dir)
    await aiofiles.os.rmdir(some_dir)

@pytest.mark.asyncio
async def test_listdir_dir_with_multiple_files():
    """Test the listdir call when the dir has multiple files."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    some_file = join(some_dir, "some_file.txt")
    other_file = join(some_dir, "other_file.txt")
    await aiofiles.os.mkdir(some_dir)
    with open(some_file, "w") as f:
        f.write("Test file")
    with open(other_file, "w") as f:
        f.write("Test file")
    dir_list = await aiofiles.os.listdir(some_dir)
    assert "some_file.txt" in dir_list
    assert "other_file.txt" in dir_list
    await aiofiles.os.remove(some_file)
    await aiofiles.os.remove(other_file)
    await aiofiles.os.rmdir(some_dir)

@pytest.mark.asyncio
async def test_listdir_dir_with_a_file_and_a_dir():
    """Test the listdir call when the dir has files and other dirs."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    other_dir = join(some_dir, "other_dir")
    some_file = join(some_dir, "some_file.txt")
    await aiofiles.os.mkdir(some_dir)
    await aiofiles.os.mkdir(other_dir)
    with open(some_file, "w") as f:
        f.write("Test file")
    dir_list = await aiofiles.os.listdir(some_dir)
    assert "some_file.txt" in dir_list
    assert "other_dir" in dir_list
    await aiofiles.os.remove(some_file)
    await aiofiles.os.rmdir(other_dir)
    await aiofiles.os.rmdir(some_dir)


@pytest.mark.asyncio
async def test_listdir_non_existing_dir():
    """Test the listdir call when the dir doesn't exist."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    with pytest.raises(FileNotFoundError) as excinfo:
        await aiofiles.os.listdir(some_dir)


@pytest.mark.asyncio
async def test_scantdir_empty_dir():
    """Test the scandir call when the dir is empty."""
    empty_dir = join(dirname(__file__), "resources", "empty_dir")
    await aiofiles.os.mkdir(empty_dir)
    dir_iterator = await aiofiles.os.scandir(empty_dir)
    dir_list = []
    for dir_entity in dir_iterator:
        dir_list.append(dir_entity)
    assert dir_list == []
    await aiofiles.os.rmdir(empty_dir)


@pytest.mark.asyncio
async def test_scandir_dir_with_only_one_file():
    """Test the scandir call when the dir has one file."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    some_file = join(some_dir, "some_file.txt")
    await aiofiles.os.mkdir(some_dir)
    with open(some_file, "w") as f:
        f.write("Test file")
    dir_iterator = await aiofiles.os.scandir(some_dir)
    some_file_entity = next(dir_iterator)
    assert some_file_entity.name == "some_file.txt"
    await aiofiles.os.remove(some_file)
    await aiofiles.os.rmdir(some_dir)

@pytest.mark.asyncio
async def test_scandir_dir_with_only_one_dir():
    """Test the scandir call when the dir has one dir."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    other_dir = join(some_dir, "other_dir")
    await aiofiles.os.mkdir(some_dir)
    await aiofiles.os.mkdir(other_dir)
    dir_iterator = await aiofiles.os.scandir(some_dir)
    other_dir_entity = next(dir_iterator)
    assert other_dir_entity.name == "other_dir"
    await aiofiles.os.rmdir(other_dir)
    await aiofiles.os.rmdir(some_dir)


@pytest.mark.asyncio
async def test_scandir_non_existing_dir():
    """Test the scandir call when the dir doesn't exist."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    with pytest.raises(FileNotFoundError) as excinfo:
        await aiofiles.os.scandir(some_dir)


@pytest.mark.asyncio
async def test_access_all_is_ok():
    some_file = join(dirname(__file__), "resources", "test_file1.txt")
    assert await aiofiles.os.access(some_file, os.R_OK)
    assert not await aiofiles.os.access(some_file, os.X_OK)
