"""Tests for asyncio's os module."""

import asyncio
import os
import platform
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from os import stat
from os.path import dirname, exists, isdir, join
from pathlib import Path
from unittest.mock import patch

import pytest

import aiofiles.os


async def test_stat():
    """Test the stat call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")

    stat_res = await aiofiles.os.stat(filename)

    assert stat_res.st_size == 10


@pytest.mark.skipif(platform.system() == "Windows", reason="No statvfs on Windows")
async def test_statvfs():
    """Test the statvfs call."""

    statvfs_res = await aiofiles.os.statvfs("/")

    assert statvfs_res.f_bsize == os.statvfs("/").f_bsize


async def test_remove():
    """Test the remove call."""
    filename = join(dirname(__file__), "resources", "test_file2.txt")
    with open(filename, "w") as f:
        f.write("Test file for remove call")

    assert exists(filename)
    await aiofiles.os.remove(filename)
    assert exists(filename) is False


async def test_unlink():
    """Test the unlink call."""
    filename = join(dirname(__file__), "resources", "test_file2.txt")
    with open(filename, "w") as f:
        f.write("Test file for unlink call")

    assert exists(filename)
    await aiofiles.os.unlink(filename)
    assert exists(filename) is False


async def test_mkdir_and_rmdir():
    """Test the mkdir and rmdir call."""
    directory = join(dirname(__file__), "resources", "test_dir")
    await aiofiles.os.mkdir(directory)
    assert isdir(directory)
    await aiofiles.os.rmdir(directory)
    assert exists(directory) is False


async def test_rename():
    """Test the rename call."""
    old_filename = join(dirname(__file__), "resources", "test_file1.txt")
    new_filename = join(dirname(__file__), "resources", "test_file2.txt")
    await aiofiles.os.rename(old_filename, new_filename)
    assert exists(old_filename) is False and exists(new_filename)
    await aiofiles.os.rename(new_filename, old_filename)
    assert exists(old_filename) and exists(new_filename) is False


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
        exists(old_filename)
        and exists(new_filename) is False
        and exists(dirname(new_filename)) is False
    )


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
    platform.system() in ("Darwin", "Windows"),
    reason="sendfile() doesn't work on mac and Win",
)
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


@pytest.mark.skipif(
    platform.system() in ("Windows"), reason="sendfile() doesn't work on Win"
)
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


async def test_exists():
    """Test path.exists call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.exists(filename)
    assert result


async def test_isfile():
    """Test path.isfile call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.isfile(filename)
    assert result


async def test_isdir():
    """Test path.isdir call."""
    filename = join(dirname(__file__), "resources")
    result = await aiofiles.os.path.isdir(filename)
    assert result


async def test_islink():
    """Test the path.islink call."""
    src_filename = join(dirname(__file__), "resources", "test_file1.txt")
    dst_filename = join(dirname(__file__), "resources", "test_file2.txt")
    await aiofiles.os.symlink(src_filename, dst_filename)
    assert await aiofiles.os.path.islink(dst_filename)
    await aiofiles.os.remove(dst_filename)


async def test_ismount():
    """Test the path.ismount call."""
    filename = join(dirname(__file__), "resources")
    assert not await aiofiles.os.path.ismount(filename)
    assert await aiofiles.os.path.ismount("/")


async def test_getsize():
    """Test path.getsize call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.getsize(filename)
    assert result == 10


async def test_samefile():
    """Test path.samefile call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.samefile(filename, filename)
    assert result


async def test_sameopenfile():
    """Test path.samefile call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.samefile(filename, filename)
    assert result


async def test_getmtime():
    """Test path.getmtime call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.getmtime(filename)
    assert result


async def test_getatime():
    """Test path.getatime call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.getatime(filename)
    assert result


async def test_getctime():
    """Test path. call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.getctime(filename)
    assert result


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


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Doesn't work on Win properly"
)
async def test_readlink():
    """Test the readlink call."""
    src_filename = join(dirname(__file__), "resources", "test_file1.txt")
    dst_filename = join(dirname(__file__), "resources", "test_file2.txt")
    await aiofiles.os.symlink(src_filename, dst_filename)
    symlinked_path = await aiofiles.os.readlink(dst_filename)
    assert src_filename == symlinked_path
    await aiofiles.os.remove(dst_filename)


async def test_listdir_empty_dir():
    """Test the listdir call when the dir is empty."""
    directory = join(dirname(__file__), "resources", "empty_dir")
    await aiofiles.os.mkdir(directory)
    dir_list = await aiofiles.os.listdir(directory)
    assert dir_list == []
    await aiofiles.os.rmdir(directory)


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


async def test_listdir_non_existing_dir():
    """Test the listdir call when the dir doesn't exist."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    with pytest.raises(FileNotFoundError):
        await aiofiles.os.listdir(some_dir)


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


async def test_scandir_non_existing_dir():
    """Test the scandir call when the dir doesn't exist."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    with pytest.raises(FileNotFoundError):
        await aiofiles.os.scandir(some_dir)


async def test_scandir_async_for_dir_with_multiple_files():
    """Test the scandir call using async for."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    some_file1 = join(some_dir, "some_file1.txt")
    some_file2 = join(some_dir, "some_file2.txt")
    await aiofiles.os.mkdir(some_dir)
    with open(some_file1, "w") as f1, open(some_file2, "w") as f2:
        f1.write("Test file")
        f2.write("Test file")

    dir_iterator = await aiofiles.os.scandir(some_dir)
    names = []
    async for entry in dir_iterator:
        names.append(entry.name)

    assert set(names) == {"some_file1.txt", "some_file2.txt"}
    await aiofiles.os.remove(some_file1)
    await aiofiles.os.remove(some_file2)
    await aiofiles.os.rmdir(some_dir)


async def test_scandir_async_with():
    """Test the scandir call using async with."""
    some_dir = join(dirname(__file__), "resources", "some_dir")
    some_file1 = join(some_dir, "some_file1.txt")
    await aiofiles.os.mkdir(some_dir)
    with open(some_file1, "w") as f1:
        f1.write("Test file")

    names = []
    async with await aiofiles.os.scandir(some_dir) as dir_iterator:
        async for entry in dir_iterator:
            names.append(entry.name)

    assert names == ["some_file1.txt"]
    await aiofiles.os.remove(some_file1)
    await aiofiles.os.rmdir(some_dir)


async def test_scandir_sync_with_delegates_cleanup_on_exit(monkeypatch):
    """Test sync ``with`` cleans up via ``__exit__`` without calling ``__enter__``.

    ``os.scandir``'s ``__enter__`` is a no-op, so the wrapper skips it; the
    handle is released through ``__exit__``.
    """
    state = {"entered": 0, "exited": 0}

    class StubScandirIterator:
        def __init__(self):
            self._items = iter(["entry"])

        def __iter__(self):
            return self

        def __next__(self):
            return next(self._items)

        def __enter__(self):
            state["entered"] += 1
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            state["exited"] += 1
            return False

        def close(self):
            return None

    monkeypatch.setattr(
        aiofiles.os.os, "scandir", lambda *_args, **_kwargs: StubScandirIterator()
    )

    entries = []
    with await aiofiles.os.scandir("ignored") as dir_iterator:
        for entry in dir_iterator:
            entries.append(entry)

    assert entries == ["entry"]
    assert state == {"entered": 0, "exited": 1}


async def test_scandir_async_with_delegates_cleanup_on_exit(monkeypatch):
    """Test async ``with`` cleans up via ``__exit__`` without calling ``__enter__``."""
    state = {"entered": 0, "exited": 0}

    class StubScandirIterator:
        def __init__(self):
            self._items = iter(["entry"])

        def __iter__(self):
            return self

        def __next__(self):
            return next(self._items)

        def __enter__(self):
            state["entered"] += 1
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            state["exited"] += 1
            return False

        def close(self):
            return None

    monkeypatch.setattr(
        aiofiles.os.os, "scandir", lambda *_args, **_kwargs: StubScandirIterator()
    )

    entries = []
    async with await aiofiles.os.scandir("ignored") as dir_iterator:
        async for entry in dir_iterator:
            entries.append(entry)

    assert entries == ["entry"]
    assert state == {"entered": 0, "exited": 1}


async def test_scandir_close_calls_underlying_close(monkeypatch):
    """Test close delegates to the underlying scandir iterator."""
    state = {"closed": 0}

    class StubScandirIterator:
        def __iter__(self):
            return self

        def __next__(self):
            msg = "no entries"
            raise StopIteration(msg)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def close(self):
            state["closed"] += 1
            return "closed"

    monkeypatch.setattr(
        aiofiles.os.os, "scandir", lambda *_args, **_kwargs: StubScandirIterator()
    )

    dir_iterator = await aiofiles.os.scandir("ignored")
    assert dir_iterator.close() == "closed"
    assert state == {"closed": 1}


async def test_scandir_aclose_calls_underlying_close(monkeypatch):
    """Test aclose delegates to the underlying scandir iterator close."""
    state = {"closed": 0}

    class StubScandirIterator:
        def __iter__(self):
            return self

        def __next__(self):
            msg = "no entries"
            raise StopIteration(msg)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def close(self):
            state["closed"] += 1
            return "closed"

    monkeypatch.setattr(
        aiofiles.os.os, "scandir", lambda *_args, **_kwargs: StubScandirIterator()
    )

    dir_iterator = await aiofiles.os.scandir("ignored")
    await dir_iterator.aclose()
    assert state == {"closed": 1}


async def test_scandir_async_for_does_not_block_event_loop(monkeypatch):
    """Test scandir async iteration keeps the event loop responsive."""

    class SlowScandirIterator:
        def __init__(self):
            self._items = iter(["a", "b", "c"])

        def __iter__(self):
            return self

        def __next__(self):
            time.sleep(0.05)
            return next(self._items)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def close(self):
            return None

    monkeypatch.setattr(
        aiofiles.os.os, "scandir", lambda *_args, **_kwargs: SlowScandirIterator()
    )

    ticks = 0
    should_run = True

    async def ticker():
        nonlocal ticks
        while should_run:
            ticks += 1
            await asyncio.sleep(0.005)

    tick_task = asyncio.create_task(ticker())
    try:
        entries = []
        async for entry in await aiofiles.os.scandir("ignored"):
            entries.append(entry)
    finally:
        should_run = False
        await tick_task

    assert entries == ["a", "b", "c"]
    assert ticks > 2


async def test_scandir_many_entries_remains_non_blocking(monkeypatch):
    """Test non-blocking behavior holds across a larger async iteration."""

    class SlowScandirIterator:
        def __init__(self):
            self._items = iter([f"entry-{i}" for i in range(200)])

        def __iter__(self):
            return self

        def __next__(self):
            time.sleep(0.001)
            return next(self._items)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def close(self):
            return None

    monkeypatch.setattr(
        aiofiles.os.os, "scandir", lambda *_args, **_kwargs: SlowScandirIterator()
    )

    ticks = 0
    should_run = True

    async def ticker():
        nonlocal ticks
        while should_run:
            ticks += 1
            await asyncio.sleep(0.0005)

    tick_task = asyncio.create_task(ticker())
    try:
        count = 0
        async for _entry in await aiofiles.os.scandir("ignored"):
            count += 1
    finally:
        should_run = False
        await tick_task

    assert count == 200
    assert ticks > 10


# ``GatedScandir`` stands in for the ``os.scandir`` iterator: it holds its first
# ``__next__`` open and records any call that starts while another one is still
# running. A cancelled ``await`` does not stop the executor thread running
# ``next()``, so every other call into the iterator must wait for it.

SCANDIR_TIMEOUT = 5  # upper bound for waits that succeed on a correct implementation
SCANDIR_HOLD = 0.2  # how long the first next() stays open for an overlapping call


class GatedScandir:
    """Stands in for the ``os.scandir`` iterator."""

    def __init__(self, items=("a", "b", "c"), fail_first=False):
        self._items = iter(items)
        self._fail_first = fail_first
        self._calls = 0
        self._active = 0
        self._guard = threading.Lock()
        self.entered = threading.Event()  # the first __next__ is running
        self.release = threading.Event()  # lets the first __next__ finish
        self.overlap = threading.Event()  # a call started while another ran
        self.closes = 0

    def _enter(self):
        with self._guard:
            self._active += 1
            self._calls += 1
            if self._active > 1:
                self.overlap.set()
            return self._calls

    def _leave(self):
        with self._guard:
            self._active -= 1

    def release_after_hold(self):
        """Run in a helper thread: free the first ``__next__`` after SCANDIR_HOLD.

        Returns early if another call overlaps, so the race shows at once.
        """
        self.overlap.wait(SCANDIR_HOLD)
        self.release.set()

    def __iter__(self):
        return self

    def __next__(self):
        call = self._enter()
        try:
            if self._fail_first and call == 1:
                msg = "readdir failed"
                raise OSError(msg)
            if call == 1:
                self.entered.set()
                if not self.release.wait(SCANDIR_TIMEOUT):
                    msg = "first next() was never released"
                    raise TimeoutError(msg)
            return next(self._items)
        finally:
            self._leave()

    def close(self):
        self._enter()
        try:
            self.closes += 1
        finally:
            self._leave()

    def __exit__(self, *exc_info):
        self.close()  # returns None, like the os.scandir iterator


async def open_gated(fake, executor):
    with patch.object(aiofiles.os.os, "scandir", return_value=fake):
        return await aiofiles.os.scandir("unused", executor=executor)


def start_releaser(fake):
    releaser = threading.Thread(target=fake.release_after_hold, daemon=True)
    releaser.start()
    return releaser


@pytest.mark.parametrize("cleanup", ["aclose", "async-with", "close", "with"])
async def test_scandir_cleanup_waits_for_cancelled_anext(cleanup):
    """Closing after a cancelled ``__anext__`` must not overlap its ``next()``."""
    fake = GatedScandir()
    with ThreadPoolExecutor(max_workers=2) as executor:
        dir_iterator = await open_gated(fake, executor)

        async def consume():
            if cleanup == "aclose":
                try:
                    await dir_iterator.__anext__()
                finally:
                    await dir_iterator.aclose()
            elif cleanup == "async-with":
                async with dir_iterator:
                    await dir_iterator.__anext__()
            elif cleanup == "close":
                try:
                    await dir_iterator.__anext__()
                finally:
                    dir_iterator.close()
            else:
                with dir_iterator:
                    await dir_iterator.__anext__()

        task = asyncio.create_task(consume())
        assert await asyncio.to_thread(fake.entered.wait, SCANDIR_TIMEOUT)
        releaser = start_releaser(fake)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        releaser.join(SCANDIR_TIMEOUT)

    assert not fake.overlap.is_set(), "closed the iterator while next() was running"
    assert fake.closes == 1


@pytest.mark.parametrize("second", ["async", "sync"])
async def test_scandir_concurrent_consumers_do_not_overlap(second):
    """Two consumers never run the underlying ``next()`` at the same time."""
    fake = GatedScandir()
    with ThreadPoolExecutor(max_workers=2) as executor:
        dir_iterator = await open_gated(fake, executor)
        first = asyncio.create_task(dir_iterator.__anext__())
        assert await asyncio.to_thread(fake.entered.wait, SCANDIR_TIMEOUT)
        releaser = start_releaser(fake)
        if second == "async":
            second_entry = await dir_iterator.__anext__()
        else:
            second_entry = next(dir_iterator)
        first_entry = await first
        releaser.join(SCANDIR_TIMEOUT)

    assert not fake.overlap.is_set(), "two next() calls ran at once"
    assert (first_entry, second_entry) == ("a", "b")


async def test_scandir_anext_after_cancelled_anext_resumes_in_order():
    """A retry after a cancelled ``__anext__`` waits for the in-flight call.

    The entry that call read is dropped (as with ``aiofiles`` file iteration);
    iteration resumes with the next one.
    """
    fake = GatedScandir()
    with ThreadPoolExecutor(max_workers=2) as executor:
        dir_iterator = await open_gated(fake, executor)
        first = asyncio.create_task(dir_iterator.__anext__())
        assert await asyncio.to_thread(fake.entered.wait, SCANDIR_TIMEOUT)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        releaser = start_releaser(fake)
        rest = [entry async for entry in dir_iterator]
        releaser.join(SCANDIR_TIMEOUT)

    assert not fake.overlap.is_set(), "the retry ran next() alongside the old call"
    assert rest == ["b", "c"]


async def test_scandir_next_error_propagates_and_releases_lock():
    """An error from the underlying ``next()`` reaches the caller.

    The lock is released, so a later call does not hang.
    """
    fake = GatedScandir(items=("a",), fail_first=True)
    with ThreadPoolExecutor(max_workers=1) as executor:
        dir_iterator = await open_gated(fake, executor)
        with pytest.raises(OSError, match="readdir failed"):
            await dir_iterator.__anext__()

    entries = []
    # A daemon thread, so a lock left held fails the test instead of hanging it.
    probe = threading.Thread(
        target=lambda: entries.append(next(dir_iterator)), daemon=True
    )
    probe.start()
    probe.join(SCANDIR_TIMEOUT)
    assert entries == ["a"]


async def test_scandir_reentrant_close_does_not_deadlock():
    """A ``close()`` from the thread already inside ``next()`` does not hang.

    A signal handler or finalizer can do this; the lock must be re-entrant.
    """

    class ClosesItself:
        def __init__(self):
            self.wrapper = None
            self.closes = 0

        def __iter__(self):
            return self

        def __next__(self):
            self.wrapper.close()  # re-enters the wrapper on the same thread
            raise StopIteration

        def close(self):
            self.closes += 1

        def __exit__(self, *exc_info):
            self.close()

    fake = ClosesItself()
    fake.wrapper = await open_gated(fake, None)
    results = []
    # A daemon thread, so a deadlock fails the test instead of hanging it.
    probe = threading.Thread(
        target=lambda: results.append(next(fake.wrapper, "end")), daemon=True
    )
    probe.start()
    probe.join(SCANDIR_TIMEOUT)
    assert results == ["end"]
    assert fake.closes == 1


async def test_scandir_keeps_the_wrapped_function_metadata():
    """``aiofiles.os.scandir`` keeps the name and signature of ``os.scandir``."""
    assert aiofiles.os.scandir.__name__ == "scandir"
    assert aiofiles.os.scandir.__wrapped__ is os.scandir


async def test_scandir_async_iteration_yields_every_entry(tmp_path):
    """Mixed sync and async iteration over a real directory sees each entry once."""
    expected = {f"file{i}" for i in range(25)}
    for name in expected:
        (tmp_path / name).write_text("x")
    (tmp_path / "subdir").mkdir()
    expected.add("subdir")

    async with await aiofiles.os.scandir(tmp_path) as dir_iterator:
        names = [next(dir_iterator).name]
        names += [entry.name async for entry in dir_iterator]

    assert len(names) == len(expected)
    assert set(names) == expected


@pytest.mark.parametrize("cleanup", ["aclose", "async-with", "close", "with"])
async def test_scandir_cleanup_closes_real_directory(tmp_path, cleanup):
    """Every cleanup path closes the handle.

    The context managers do not swallow exceptions.
    """
    for name in ("a", "b", "c"):
        (tmp_path / name).write_text("x")
    dir_iterator = await aiofiles.os.scandir(tmp_path)

    if cleanup == "aclose":
        await dir_iterator.__anext__()
        await dir_iterator.aclose()
    elif cleanup == "close":
        await dir_iterator.__anext__()
        dir_iterator.close()
    elif cleanup == "async-with":
        with pytest.raises(ValueError):
            async with dir_iterator:
                await dir_iterator.__anext__()
                raise ValueError
    else:
        with pytest.raises(ValueError):
            with dir_iterator:
                next(dir_iterator)
                raise ValueError

    with pytest.raises(StopIteration):  # entries were left, but it is closed
        next(dir_iterator)


async def test_scandir_runs_every_call_in_the_configured_executor():
    """Iteration and cleanup use the executor passed to ``scandir``."""
    threads = []

    class Recording:
        def __init__(self):
            self._items = iter(["a"])

        def __iter__(self):
            return self

        def __next__(self):
            threads.append(threading.current_thread().name)
            return next(self._items)

        def close(self):
            threads.append(threading.current_thread().name)

        def __exit__(self, *exc_info):
            self.close()

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="scandir-test") as ex:
        dir_iterator = await open_gated(Recording(), ex)
        async with dir_iterator:
            assert [entry async for entry in dir_iterator] == ["a"]
        await dir_iterator.aclose()

    assert len(threads) == 4
    assert all(name.startswith("scandir-test") for name in threads), threads


async def test_scandir_iterators_do_not_block_each_other():
    """The lock is per iterator: a slow directory does not stall another one."""
    slow = GatedScandir()
    fast = GatedScandir()
    fast.release.set()
    with ThreadPoolExecutor(max_workers=2) as executor:
        slow_iterator = await open_gated(slow, executor)
        fast_iterator = await open_gated(fast, executor)
        pending = asyncio.create_task(slow_iterator.__anext__())
        assert await asyncio.to_thread(slow.entered.wait, SCANDIR_TIMEOUT)
        try:
            entry = await asyncio.wait_for(fast_iterator.__anext__(), SCANDIR_TIMEOUT)
            assert entry == "a"
        finally:
            slow.release.set()
        assert await pending == "a"


@pytest.mark.skipif(platform.system() == "Windows", reason="Doesn't work on Win")
async def test_access():
    temp_file = Path(__file__).parent.joinpath("resources", "os_access_temp.txt")
    temp_dir = Path(__file__).parent.joinpath("resources", "os_access_temp")

    # prepare
    if temp_file.exists():
        os.remove(temp_file)
    assert not temp_file.exists()
    temp_file.touch()

    if temp_dir.exists():
        os.rmdir(temp_dir)
    assert not temp_dir.exists()
    os.mkdir(temp_dir)

    data = [
        # full access
        [0o777, os.F_OK, True],
        [0o777, os.R_OK, True],
        [0o777, os.W_OK, True],
        [0o777, os.X_OK, True],
        # chmod -x
        [0o666, os.F_OK, True],
        [0o666, os.R_OK, True],
        [0o666, os.W_OK, True],
        [0o666, os.X_OK, False],
        # chmod -w
        [0o444, os.F_OK, True],
        [0o444, os.R_OK, True],
        [0o444, os.W_OK, False],
        [0o444, os.X_OK, False],
        # chmod -r
        [0o000, os.F_OK, True],
        [0o000, os.R_OK, False],
        [0o000, os.W_OK, False],
        [0o000, os.X_OK, False],
    ]
    for ch, mode, access in data:
        print(f"mode:{mode}, access:{access}")
        temp_file.chmod(ch)
        temp_dir.chmod(ch)
        assert await aiofiles.os.access(temp_file, mode) == access
        assert await aiofiles.os.access(temp_dir, mode) == access

    # not exists
    os.remove(temp_file)
    os.rmdir(temp_dir)
    for mode in [os.F_OK, os.R_OK, os.W_OK, os.X_OK]:
        print(f"mode:{mode}")
        assert not await aiofiles.os.access(temp_file, mode)
        assert not await aiofiles.os.access(temp_dir, mode)


async def test_getcwd():
    """Test the getcwd call."""
    cwd = await aiofiles.os.getcwd()
    assert cwd == os.getcwd()


async def test_abspath_given_abspath():
    """Test the abspath call with an absolute path."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    file_abs_path = await aiofiles.os.path.abspath(filename)
    assert file_abs_path == filename


async def test_abspath():
    """Test the abspath call."""
    relative_filename = "./tests/resources/test_file1.txt"
    abs_filename = join(dirname(__file__), "resources", "test_file1.txt")
    result = await aiofiles.os.path.abspath(relative_filename)
    assert result == abs_filename
