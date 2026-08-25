"""Tests for aiofiles.pathlib.Path."""

import asyncio
import os
import pathlib
import platform
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from aiofiles.pathlib import Path
from aiofiles.threadpool.binary import AsyncBufferedReader
from aiofiles.threadpool.text import AsyncTextIOWrapper

if sys.version_info >= (3, 14):
    from pathlib.types import PathInfo


class RecordingExecutor(ThreadPoolExecutor):
    """An executor that counts submitted calls."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.submissions = 0

    def submit(self, *args, **kwargs):
        self.submissions += 1
        return super().submit(*args, **kwargs)


@pytest.mark.parametrize(
    "segments",
    [
        pytest.param(("a", "b"), id="segments"),
        pytest.param(("a/b",), id="str"),
        pytest.param((pathlib.Path("a/b"),), id="pathlib"),
        pytest.param((Path("a/b"),), id="aiofiles"),
        pytest.param((), id="empty"),
    ],
)
def test_construction(segments):
    """Construction gives the same path as pathlib for every input kind."""
    assert Path(*segments) == pathlib.Path(*segments)


def test_fspath_str_bytes_repr():
    """A Path is os.PathLike and converts like its pathlib equivalent."""
    path = Path("a", "b")
    assert os.fspath(path) == os.fspath(pathlib.Path("a", "b"))
    assert isinstance(path, os.PathLike)
    assert str(path) == str(pathlib.Path("a", "b"))
    assert bytes(path) == bytes(pathlib.Path("a", "b"))
    assert repr(path) == "Path('a/b')"


def test_equality_and_hash():
    """Equality and hashing agree with pathlib from either side."""
    assert Path("a/b") == Path("a", "b")
    assert Path("a/b") == pathlib.Path("a", "b")
    assert pathlib.Path("a/b") == Path("a", "b")
    assert Path("a") != Path("b")
    assert Path("a") != "a"
    assert hash(Path("a/b")) == hash(pathlib.Path("a/b"))
    assert len({Path("a"), pathlib.Path("a"), Path("a")}) == 1


def test_ordering():
    """Ordering matches pathlib; unorderable operands raise TypeError."""
    assert Path("a") < Path("b") <= Path("b")
    assert Path("b") > pathlib.Path("a")
    assert Path("b") >= pathlib.Path("b")
    assert pathlib.Path("b") >= Path("a")
    assert sorted([Path("b"), Path("a")]) == [Path("a"), Path("b")]
    with pytest.raises(TypeError):
        _ = Path("a") < 1


def test_truediv():
    """The slash operator returns wrapped paths from either operand side."""
    path = Path("a") / "b" / pathlib.Path("c") / Path("d")
    assert isinstance(path, Path)
    assert path == pathlib.Path("a", "b", "c", "d")
    r_path = "a" / Path("b")
    assert isinstance(r_path, Path)
    assert r_path == pathlib.Path("a", "b")
    with pytest.raises(TypeError):
        _ = Path("a") / 1
    with pytest.raises(TypeError):
        _ = 1 / Path("a")


def test_pure_properties():
    """The pure path properties report the same values as pathlib."""
    path = Path("a/b/c.tar.gz")
    pure = pathlib.Path("a/b/c.tar.gz")
    assert path.parts == pure.parts
    assert path.drive == pure.drive
    assert path.root == pure.root
    assert path.anchor == pure.anchor
    assert path.name == pure.name
    assert path.suffix == pure.suffix
    assert path.suffixes == pure.suffixes
    assert path.stem == pure.stem


def test_parent_and_parents():
    """parent and parents return wrapped paths."""
    path = Path("a/b/c")
    assert isinstance(path.parent, Path)
    assert path.parent == pathlib.Path("a/b")
    parents = path.parents
    assert isinstance(parents, tuple)
    assert all(isinstance(p, Path) for p in parents)
    assert list(parents) == list(pathlib.Path("a/b/c").parents)


def test_with_name_stem_suffix():
    """The with_* methods return wrapped paths and reject empty stems."""
    path = Path("a/b.txt")
    assert path.with_name("c.rst") == pathlib.Path("a/c.rst")
    assert path.with_stem("c") == pathlib.Path("a/c.txt")
    assert path.with_suffix(".rst") == pathlib.Path("a/b.rst")
    assert isinstance(path.with_suffix(".rst"), Path)
    with pytest.raises(ValueError):
        path.with_stem("")
    assert Path("a/b").with_stem("c") == pathlib.Path("a/c")


def test_joinpath_and_with_segments():
    """joinpath and with_segments build wrapped paths from segments."""
    path = Path("a").joinpath("b", pathlib.Path("c"))
    assert isinstance(path, Path)
    assert path == pathlib.Path("a/b/c")
    segments = Path("a/b").with_segments("c", "d")
    assert isinstance(segments, Path)
    assert segments == pathlib.Path("c/d")


def test_match():
    """match() reports whether the path matches a glob pattern."""
    assert Path("a/b.py").match("*.py")
    assert not Path("a/b.py").match("*.rst")


@pytest.mark.skipif(sys.version_info < (3, 12), reason="case_sensitive is 3.12+")
def test_match_case_sensitive():
    """match() ignores case when case_sensitive is disabled."""
    assert Path("a/B.py").match("*.PY", case_sensitive=False)


@pytest.mark.skipif(sys.version_info < (3, 13), reason="full_match is 3.13+")
def test_full_match():
    """full_match() matches against the entire path."""
    assert Path("a/b.py").full_match("a/*.py")
    assert not Path("a/b.py").full_match("*.py")


@pytest.mark.parametrize(
    "other",
    [
        pytest.param("/etc", id="str"),
        pytest.param(pathlib.Path("/etc"), id="pathlib"),
        pytest.param(Path("/etc"), id="aiofiles"),
    ],
)
def test_relative_to(other):
    """relative_to() and is_relative_to() accept strings and both path types."""
    path = Path("/etc/passwd")
    relative = path.relative_to(other)
    assert isinstance(relative, Path)
    assert relative == pathlib.Path("passwd")
    assert path.is_relative_to(other)


def test_relative_to_unrelated():
    """An unrelated base is rejected by relative_to() and is_relative_to()."""
    path = Path("/etc/passwd")
    assert not path.is_relative_to("/usr")
    with pytest.raises(ValueError):
        path.relative_to("/usr")


@pytest.mark.skipif(sys.version_info < (3, 12), reason="walk_up is 3.12+")
def test_relative_to_walk_up():
    """walk_up resolves a path relative to a non-ancestor."""
    assert Path("/etc").relative_to("/etc/passwd", walk_up=True) == pathlib.Path("..")


@pytest.mark.skipif(
    sys.version_info >= (3, 12),
    reason="multi-segment relative_to mirrors pathlib before 3.12",
)
def test_relative_to_multiple_segments():
    """The multi-segment form mirrors pathlib before 3.12."""
    assert Path("/a/b/c").relative_to("/a", "b") == pathlib.Path("c")
    assert Path("/a/b/c").is_relative_to("/a", "b")


def test_as_posix_is_absolute():
    """as_posix() uses forward slashes; is_absolute() spots rooted paths."""
    assert Path("a/b").as_posix() == "a/b"
    assert not Path("a").is_absolute()
    assert Path(pathlib.Path.cwd()).is_absolute()


def test_as_uri():
    """as_uri() renders the same URI as pathlib."""
    path = pathlib.Path.cwd() / "a.txt"
    assert Path(path).as_uri() == path.as_uri()


@pytest.mark.skipif(
    sys.version_info >= (3, 15), reason="is_reserved is removed in 3.15"
)
@pytest.mark.filterwarnings("ignore:pathlib.PurePath.is_reserved:DeprecationWarning")
@pytest.mark.parametrize("name", ["a/b", "NUL"])
def test_is_reserved(name):
    """is_reserved() gives pathlib's answer for reserved Windows names."""
    assert Path(name).is_reserved() == pathlib.Path(name).is_reserved()


async def test_cwd_and_home():
    """cwd() and home() return wrapped paths for the process directories."""
    cwd = await Path.cwd()
    assert isinstance(cwd, Path)
    assert cwd == pathlib.Path.cwd()
    home = await Path.home()
    assert isinstance(home, Path)
    assert home == pathlib.Path.home()


async def test_exists(tmp_path):
    """exists() reflects file creation."""
    path = Path(tmp_path) / "file"
    assert not await path.exists()
    await path.touch()
    assert await path.exists()


async def test_touch_and_unlink(tmp_path):
    """touch() creates and unlink() removes; missing_ok suppresses the error."""
    path = Path(tmp_path) / "file"
    await path.touch()
    assert await path.is_file()
    await path.unlink()
    assert not await path.exists()
    with pytest.raises(FileNotFoundError):
        await path.unlink()
    await path.unlink(missing_ok=True)


async def test_mkdir_and_rmdir(tmp_path):
    """mkdir() honors parents and exist_ok; rmdir() removes the directory."""
    path = Path(tmp_path) / "a" / "b"
    with pytest.raises(FileNotFoundError):
        await path.mkdir()
    await path.mkdir(parents=True)
    assert await path.is_dir()
    await path.mkdir(exist_ok=True)
    with pytest.raises(FileExistsError):
        await path.mkdir()
    await path.rmdir()
    assert not await path.exists()


async def test_read_write_text(tmp_path):
    """Text written with write_text() is returned by read_text()."""
    path = Path(tmp_path) / "file.txt"
    assert await path.write_text("hello") == 5
    assert await path.read_text() == "hello"
    assert await path.read_text(encoding="utf-8") == "hello"


async def test_write_text_newline(tmp_path):
    """write_text() translates newlines even on 3.9, which pathlib cannot."""
    path = Path(tmp_path) / "file.txt"
    await path.write_text("a\nb", newline="\r\n")
    assert await path.read_bytes() == b"a\r\nb"


async def test_write_text_bad_data(tmp_path):
    """A write_text() type error leaves the file untouched."""
    path = Path(tmp_path) / "file.txt"
    await path.write_text("data")
    with pytest.raises(TypeError):
        await path.write_text(b"bytes")
    assert await path.read_text() == "data"


async def test_read_write_bytes(tmp_path):
    """Bytes written with write_bytes() are returned by read_bytes()."""
    path = Path(tmp_path) / "file.bin"
    assert await path.write_bytes(b"\x00\x01") == 2
    assert await path.read_bytes() == b"\x00\x01"


async def test_open_text(tmp_path):
    """open() yields the same async text file objects as aiofiles.open()."""
    path = Path(tmp_path) / "file.txt"
    await path.write_text("line1\nline2\n")
    async with path.open() as f:
        assert isinstance(f, AsyncTextIOWrapper)
        assert await f.read() == "line1\nline2\n"
    f = await path.open()
    lines = [line async for line in f]
    assert lines == ["line1\n", "line2\n"]
    await f.close()


async def test_open_binary(tmp_path):
    """open() in binary mode yields aiofiles' async binary file objects."""
    path = Path(tmp_path) / "file.bin"
    await path.write_bytes(b"\x00\x01")
    async with path.open("rb") as f:
        assert isinstance(f, AsyncBufferedReader)
        assert await f.read() == b"\x00\x01"


async def test_stat_and_lstat(tmp_path):
    """stat() and lstat() report file metadata."""
    path = Path(tmp_path) / "file"
    await path.write_bytes(b"abc")
    stat = await path.stat()
    assert stat.st_size == 3
    lstat = await path.lstat()
    assert lstat.st_size == 3


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Doesn't work on Win properly"
)
async def test_stat_follow_symlinks(tmp_path):
    """stat(follow_symlinks=False) reports the symlink, not its target."""
    target = Path(tmp_path) / "target"
    await target.write_bytes(b"abc")
    link = Path(tmp_path) / "link"
    await link.symlink_to(target)
    assert (await link.stat()).st_size == 3
    assert (await link.stat(follow_symlinks=False)).st_size != 3


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Unix permissions don't map to Win"
)
async def test_chmod(tmp_path):
    """chmod() changes the file mode."""
    path = Path(tmp_path) / "file"
    await path.touch()
    await path.chmod(0o600)
    assert (await path.stat()).st_mode & 0o777 == 0o600


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Unix permissions don't map to Win"
)
@pytest.mark.skipif(not hasattr(os, "lchmod"), reason="No os.lchmod on this system")
async def test_lchmod(tmp_path):
    """lchmod() changes the symlink's own mode, not its target's."""
    target = Path(tmp_path) / "target"
    await target.touch()
    mode_before = (await target.stat()).st_mode
    link = Path(tmp_path) / "link"
    await link.symlink_to(target)
    await link.lchmod(0o600)
    assert (await link.stat(follow_symlinks=False)).st_mode & 0o777 == 0o600
    assert (await target.stat()).st_mode == mode_before


async def test_iterdir(tmp_path):
    """iterdir() yields every child as a wrapped path."""
    for name in ("a", "b", "c"):
        (tmp_path / name).touch()
    entries = [entry async for entry in Path(tmp_path).iterdir()]
    assert all(isinstance(entry, Path) for entry in entries)
    assert sorted(entries) == sorted(Path(p) for p in tmp_path.iterdir())


async def test_glob(tmp_path):
    """glob() yields the matching children as wrapped paths."""
    for name in ("a.py", "b.py", "c.txt"):
        (tmp_path / name).touch()
    matches = [match async for match in Path(tmp_path).glob("*.py")]
    assert all(isinstance(match, Path) for match in matches)
    assert sorted(matches) == [Path(tmp_path, "a.py"), Path(tmp_path, "b.py")]


async def test_rglob(tmp_path):
    """rglob() matches recursively."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.py").touch()
    (tmp_path / "sub" / "b.py").touch()
    matches = [match async for match in Path(tmp_path).rglob("*.py")]
    assert sorted(matches) == [
        Path(tmp_path, "a.py"),
        Path(tmp_path, "sub", "b.py"),
    ]


@pytest.mark.skipif(sys.version_info < (3, 12), reason="walk is 3.12+")
async def test_walk(tmp_path):
    """walk() yields each directory with its subdirectories and files."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "file").touch()
    seen = {}
    async for root, dirs, files in Path(tmp_path).walk():
        assert isinstance(root, Path)
        seen[root] = (sorted(dirs), sorted(files))
    assert seen[Path(tmp_path)] == (["a", "b"], [])
    assert seen[Path(tmp_path, "a")] == ([], ["file"])


@pytest.mark.skipif(sys.version_info < (3, 12), reason="walk is 3.12+")
async def test_walk_prunes_dirs(tmp_path):
    """Editing the dirs list prunes the walk."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    roots = []
    async for root, dirs, _files in Path(tmp_path).walk():
        roots.append(root)
        dirs[:] = [d for d in dirs if d != "b"]
    assert Path(tmp_path, "a") in roots
    assert Path(tmp_path, "b") not in roots


async def test_rename_and_replace(tmp_path):
    """rename() and replace() move the file and return wrapped paths."""
    src = Path(tmp_path) / "src"
    await src.write_text("data")
    renamed = await src.rename(Path(tmp_path) / "renamed")
    assert isinstance(renamed, Path)
    assert await renamed.read_text() == "data"
    assert not await src.exists()
    replaced = await renamed.replace(str(tmp_path / "replaced"))
    assert isinstance(replaced, Path)
    assert await replaced.read_text() == "data"


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Doesn't work on Win properly"
)
async def test_symlink_and_readlink(tmp_path):
    """symlink_to() creates links that readlink() and is_symlink() report."""
    target = Path(tmp_path) / "target"
    await target.touch()
    link = Path(tmp_path) / "link"
    await link.symlink_to(target)
    assert await link.is_symlink()
    assert not await target.is_symlink()
    resolved = await link.readlink()
    assert isinstance(resolved, Path)
    assert resolved == target


async def test_hardlink_to(tmp_path):
    """hardlink_to() creates a second directory entry for the file."""
    target = Path(tmp_path) / "target"
    await target.write_text("data")
    link = Path(tmp_path) / "link"
    await link.hardlink_to(target)
    assert await link.read_text() == "data"
    assert (await link.stat()).st_nlink == 2


async def test_samefile(tmp_path):
    """samefile() identifies paths that name the same file."""
    path = Path(tmp_path) / "file"
    await path.touch()
    assert await path.samefile(path)
    assert await path.samefile(str(path))
    other = Path(tmp_path) / "other"
    await other.touch()
    assert not await path.samefile(other)


async def test_is_dir_and_is_file(tmp_path):
    """is_dir() and is_file() distinguish directories from files."""
    path = Path(tmp_path)
    assert await path.is_dir()
    assert not await path.is_file()
    file = path / "file"
    await file.touch()
    assert await file.is_file()
    assert not await file.is_dir()


async def test_file_type_checks(tmp_path):
    """A regular file is no mount, device, FIFO, or socket."""
    path = Path(tmp_path) / "file"
    await path.touch()
    assert not await path.is_mount()
    assert not await path.is_block_device()
    assert not await path.is_char_device()
    assert not await path.is_fifo()
    assert not await path.is_socket()


@pytest.mark.skipif(sys.version_info < (3, 12), reason="is_junction is 3.12+")
async def test_is_junction(tmp_path):
    """A regular file is not a junction."""
    path = Path(tmp_path) / "file"
    await path.touch()
    assert not await path.is_junction()


@pytest.mark.skipif(platform.system() == "Windows", reason="No owner/group on Win")
async def test_owner_and_group(tmp_path):
    """owner() and group() name the file's owner and group."""
    path = Path(tmp_path) / "file"
    await path.touch()
    assert isinstance(await path.owner(), str)
    assert isinstance(await path.group(), str)


@pytest.mark.skipif(platform.system() == "Windows", reason="No owner/group on Win")
@pytest.mark.skipif(sys.version_info < (3, 13), reason="follow_symlinks is 3.13+")
async def test_owner_and_group_follow_symlinks(tmp_path):
    """follow_symlinks=False reports the link's own owner and group."""
    path = Path(tmp_path) / "file"
    await path.touch()
    link = Path(tmp_path) / "link"
    await link.symlink_to(path)
    assert await link.owner(follow_symlinks=False) == await path.owner()
    assert await link.group(follow_symlinks=False) == await path.group()


async def test_resolve_absolute_expanduser(tmp_path):
    """resolve(), absolute(), and expanduser() return wrapped absolute paths."""
    path = Path("a")
    for result in (await path.resolve(), await path.absolute()):
        assert isinstance(result, Path)
        assert result.is_absolute()
    expanded = await Path("~").expanduser()
    assert isinstance(expanded, Path)
    assert expanded == pathlib.Path("~").expanduser()


@pytest.mark.skipif(sys.version_info < (3, 13), reason="from_uri is 3.13+")
def test_from_uri():
    """from_uri() reconstructs a path from its URI."""
    path = pathlib.Path.cwd() / "a.txt"
    from_uri = Path.from_uri(path.as_uri())
    assert isinstance(from_uri, Path)
    assert from_uri == path


@pytest.mark.skipif(sys.version_info < (3, 14), reason="info is 3.14+")
async def test_info(tmp_path):
    """The info queries are awaitable and cache their answers like pathlib's."""
    path = Path(tmp_path) / "file"
    await path.write_text("data")
    info = path.info
    assert await info.exists()
    assert await info.is_file()
    assert await info.is_file(follow_symlinks=False)
    assert not await info.is_dir()
    assert not await info.is_symlink()
    await path.unlink()
    assert await info.exists()  # answers are cached, like pathlib's
    assert not await Path(tmp_path, "file").info.exists()


@pytest.mark.skipif(sys.version_info < (3, 14), reason="info is 3.14+")
async def test_info_wrapped(tmp_path):
    """info.wrapped exposes the underlying cached PathInfo."""
    path = Path(tmp_path)
    assert isinstance(path.info.wrapped, PathInfo)
    assert path.info.wrapped is path.info.wrapped
    assert Path(path).info.wrapped is path.info.wrapped
    assert repr(path.info.wrapped) in repr(path.info)


@pytest.mark.skipif(sys.version_info < (3, 14), reason="info is 3.14+")
async def test_info_iterdir_prefetch(tmp_path):
    """iterdir entries keep the stat info prefetched by scandir."""
    (tmp_path / "file").touch()
    entries = [entry async for entry in Path(tmp_path).iterdir()]
    (tmp_path / "file").unlink()
    assert await entries[0].info.is_file()
    assert not await Path(tmp_path, "file").info.exists()


@pytest.mark.skipif(sys.version_info < (3, 14), reason="copy/move are 3.14+")
async def test_copy_and_move(tmp_path):
    """The copy and move family transfers files and returns wrapped paths."""
    src = Path(tmp_path) / "src"
    await src.write_text("data")
    copied = await src.copy(Path(tmp_path) / "copied")
    assert isinstance(copied, Path)
    assert await copied.read_text() == "data"
    directory = Path(tmp_path) / "dir"
    await directory.mkdir()
    copied_into = await src.copy_into(directory)
    assert copied_into == directory / "src"
    assert await copied_into.read_text() == "data"
    moved = await copied.move(Path(tmp_path) / "moved")
    assert isinstance(moved, Path)
    assert await moved.read_text() == "data"
    assert not await copied.exists()
    moved_into = await moved.move_into(directory)
    assert moved_into == directory / "moved"
    assert not await moved.exists()


async def test_custom_executor_used(tmp_path):
    """Blocking calls run on the executor given to the constructor."""
    with RecordingExecutor() as executor:
        path = Path(tmp_path, "file", executor=executor)
        await path.write_text("data")
        assert executor.submissions > 0
        before = executor.submissions
        assert await path.read_text() == "data"
        assert executor.submissions > before


async def test_custom_executor_inherited(tmp_path):
    """Derived paths inherit and use the constructor's executor."""
    with RecordingExecutor() as executor:
        path = Path(tmp_path, "file", executor=executor)
        await path.touch()

        child = path.parent / "file"
        before = executor.submissions
        assert await child.exists()
        assert executor.submissions > before

        entries = [entry async for entry in path.parent.iterdir()]
        before = executor.submissions
        assert await entries[0].is_file()
        assert executor.submissions > before


async def test_custom_executor_not_shared(tmp_path):
    """A path constructed without an executor never uses another path's."""
    with RecordingExecutor() as executor:
        path = Path(tmp_path, "file", executor=executor)
        await path.touch()
        before = executor.submissions

        assert await Path(tmp_path, "file").exists()
        entries = [entry async for entry in Path(tmp_path).iterdir()]
        assert entries == [Path(tmp_path, "file")]
        assert await entries[0].is_file()
        assert executor.submissions == before


async def test_custom_executor_open(tmp_path):
    """open() carries the executor into the file operations."""
    with RecordingExecutor() as executor:
        path = Path(tmp_path, "file", executor=executor)
        await path.write_text("data")
        before = executor.submissions
        async with path.open() as f:
            opened = executor.submissions
            assert opened > before
            assert await f.read() == "data"
            assert executor.submissions > opened


async def test_iterdir_one_hop_per_item(tmp_path):
    """Directory iteration takes one executor hop per item, never a bulk listing."""
    for name in ("a", "b", "c"):
        (tmp_path / name).touch()
    with RecordingExecutor() as executor:
        path = Path(tmp_path, executor=executor)
        entries = [entry async for entry in path.iterdir()]
        assert len(entries) == 3
        # One submission creates the iterator, then one per next() call:
        # len(entries) items plus the final call signalling exhaustion.
        assert executor.submissions == 1 + len(entries) + 1


async def test_loop_kwarg(tmp_path):
    """An explicitly passed event loop is accepted."""
    path = Path(tmp_path, "file", loop=asyncio.get_running_loop())
    await path.touch()
    assert await (path.parent / "file").exists()


async def test_subclass():
    """Derived paths preserve the subclass."""

    class UserPath(Path):
        __slots__ = ()

    path = UserPath("a/b.txt")
    assert isinstance(path / "c", UserPath)
    assert isinstance(path.parent, UserPath)
    assert isinstance(path.with_suffix(".rst"), UserPath)
    assert isinstance(await UserPath.cwd(), UserPath)


async def test_subclass_with_segments(tmp_path):
    """Derived paths are created through the with_segments hook."""

    class TaggedPath(Path):
        __slots__ = ("tag",)

        def with_segments(self, *pathsegments):
            derived = super().with_segments(*pathsegments)
            derived.tag = getattr(self, "tag", None)
            return derived

    path = TaggedPath(tmp_path)
    path.tag = "tagged"
    assert (path / "child").tag == "tagged"
    assert path.parent.tag == "tagged"
    (tmp_path / "file").touch()
    entries = [entry async for entry in path.iterdir()]
    assert entries[0].tag == "tagged"


async def test_subclass_iteration(tmp_path):
    """Iteration yields subclass instances."""

    class UserPath(Path):
        __slots__ = ()

    (tmp_path / "file").touch()
    entries = [entry async for entry in UserPath(tmp_path).iterdir()]
    assert all(isinstance(entry, UserPath) for entry in entries)


def test_api_parity():
    """Every public pathlib.Path member has a counterpart or documented omission."""
    deliberately_omitted = {
        "link_to",  # deprecated in 3.10, removed in 3.12
    }
    pathlib_members = {name for name in dir(pathlib.Path) if not name.startswith("_")}
    missing = pathlib_members - set(dir(Path)) - deliberately_omitted
    assert not missing
