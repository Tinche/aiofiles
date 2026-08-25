"""Async executor version of pathlib.Path."""

from __future__ import annotations

__all__ = ["Path"]

import asyncio
import functools
import os
import pathlib
import sys
from typing import TYPE_CHECKING

from .threadpool import open as _open

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterable
    from concurrent.futures import Executor
    from typing import TypeVar

    from _typeshed import ReadableBuffer, StrOrBytesPath, StrPath
    from typing_extensions import ParamSpec, Self

    from .base import AiofilesContextManager

    if sys.version_info >= (3, 14):
        from pathlib.types import PathInfo

    _T = TypeVar("_T")
    _P = ParamSpec("_P")


if sys.version_info >= (3, 14):
    __all__ += ["AsyncPathInfo"]

    class AsyncPathInfo:
        """An asynchronous version of pathlib.types.PathInfo.

        The query methods are coroutines delegating to an executor, and
        their answers are cached like the standard library's. The
        underlying synchronous PathInfo is available as the wrapped
        attribute.
        """

        __slots__ = ("_executor", "_info", "_ref_loop")

        _info: PathInfo
        _ref_loop: asyncio.AbstractEventLoop | None
        _executor: Executor | None

        def __init__(
            self,
            info: PathInfo,
            loop: asyncio.AbstractEventLoop | None,
            executor: Executor | None,
        ) -> None:
            self._info = info
            self._ref_loop = loop
            self._executor = executor

        @property
        def wrapped(self) -> PathInfo:
            """The wrapped pathlib.types.PathInfo object."""
            return self._info

        def __repr__(self) -> str:
            return f"{type(self).__name__}({self._info!r})"

        async def _run(
            self,
            func: Callable[_P, _T],
            *args: _P.args,
            **kwargs: _P.kwargs,
        ) -> _T:
            loop = self._ref_loop or asyncio.get_running_loop()
            return await loop.run_in_executor(
                self._executor,
                functools.partial(func, *args, **kwargs),
            )

        async def exists(self, *, follow_symlinks: bool = True) -> bool:
            return await self._run(self._info.exists, follow_symlinks=follow_symlinks)

        async def is_dir(self, *, follow_symlinks: bool = True) -> bool:
            return await self._run(self._info.is_dir, follow_symlinks=follow_symlinks)

        async def is_file(self, *, follow_symlinks: bool = True) -> bool:
            return await self._run(self._info.is_file, follow_symlinks=follow_symlinks)

        async def is_symlink(self) -> bool:
            return await self._run(self._info.is_symlink)


class Path:
    """An asynchronous version of pathlib.Path.

    Pure path operations such as name, parent, and joinpath do no I/O
    and stay synchronous. Methods that touch the filesystem are
    coroutines; iterdir, glob, rglob, and walk return async iterators,
    and open() returns the same async file objects as aiofiles.open().

    Path implements the os.PathLike interface, so it is accepted
    anywhere a path is, but it cannot substitute for pathlib.Path or
    pathlib.PurePath. Methods follow the pathlib API of the running
    interpreter, with two differences: info is an AsyncPathInfo whose
    query methods are coroutines, and the deprecated link_to() is not
    provided; use hardlink_to() instead.

    The optional loop and executor constructor arguments are used for
    every blocking call and are inherited by derived paths.
    """

    __slots__ = ("__weakref__", "_executor", "_path", "_ref_loop")

    _path: pathlib.Path
    _ref_loop: asyncio.AbstractEventLoop | None
    _executor: Executor | None

    def __init__(
        self,
        *pathsegments: StrPath,
        loop: asyncio.AbstractEventLoop | None = None,
        executor: Executor | None = None,
    ) -> None:
        if len(pathsegments) == 1:
            segment = pathsegments[0]
            if isinstance(segment, Path):
                segment = segment._path
            # Keep a concrete instance as-is so its cached stat
            # information is not lost, for example when wrapping the
            # scandir-prefetched paths yielded by iterdir().
            if (
                type(segment) is pathlib.PosixPath
                or type(segment) is pathlib.WindowsPath
            ):
                self._path = segment
            else:
                self._path = pathlib.Path(segment)
        else:
            self._path = pathlib.Path(*pathsegments)
        self._ref_loop = loop
        self._executor = executor

    @property
    def _loop(self) -> asyncio.AbstractEventLoop:
        return self._ref_loop or asyncio.get_running_loop()

    async def _run(
        self,
        func: Callable[_P, _T],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _T:
        cb = functools.partial(func, *args, **kwargs)
        return await self._loop.run_in_executor(self._executor, cb)

    async def _iterate(
        self,
        factory: Callable[[], Iterable[pathlib.Path]],
    ) -> AsyncIterator[Self]:
        """Drive a blocking iterator from the executor, one item per hop."""
        iterator = iter(await self._run(factory))

        def step() -> pathlib.Path | None:
            return next(iterator, None)

        while (item := await self._run(step)) is not None:
            yield self.with_segments(item)

    def __fspath__(self) -> str:
        return self._path.__fspath__()

    def __str__(self) -> str:
        return str(self._path)

    def __bytes__(self) -> bytes:
        return self._path.__bytes__()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.as_posix()!r})"

    def __hash__(self) -> int:
        return hash(self._path)

    def __eq__(self, other: object) -> bool:
        target = other._path if isinstance(other, Path) else other
        return self._path.__eq__(target)

    def __lt__(self, other: pathlib.PurePath | Path) -> bool:
        target = other._path if isinstance(other, Path) else other
        return self._path.__lt__(target)

    def __le__(self, other: pathlib.PurePath | Path) -> bool:
        target = other._path if isinstance(other, Path) else other
        return self._path.__le__(target)

    def __gt__(self, other: pathlib.PurePath | Path) -> bool:
        target = other._path if isinstance(other, Path) else other
        return self._path.__gt__(target)

    def __ge__(self, other: pathlib.PurePath | Path) -> bool:
        target = other._path if isinstance(other, Path) else other
        return self._path.__ge__(target)

    def __truediv__(self, key: StrPath) -> Self:
        result = self._path.__truediv__(key)
        if result is NotImplemented:
            return NotImplemented
        return self.with_segments(result)

    def __rtruediv__(self, key: StrPath) -> Self:
        result = self._path.__rtruediv__(key)
        if result is NotImplemented:
            return NotImplemented
        return self.with_segments(result)

    @property
    def parts(self) -> tuple[str, ...]:
        return self._path.parts

    @property
    def drive(self) -> str:
        return self._path.drive

    @property
    def root(self) -> str:
        return self._path.root

    @property
    def anchor(self) -> str:
        return self._path.anchor

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def suffix(self) -> str:
        return self._path.suffix

    @property
    def suffixes(self) -> list[str]:
        return self._path.suffixes

    @property
    def stem(self) -> str:
        return self._path.stem

    @property
    def parent(self) -> Self:
        return self.with_segments(self._path.parent)

    @property
    def parents(self) -> tuple[Self, ...]:
        return tuple(self.with_segments(p) for p in self._path.parents)

    if sys.version_info >= (3, 13):
        parser = pathlib.Path.parser

    async def absolute(self) -> Self:
        return self.with_segments(await self._run(self._path.absolute))

    def as_posix(self) -> str:
        return self._path.as_posix()

    def as_uri(self) -> str:
        return self._path.as_uri()

    async def chmod(self, mode: int, *, follow_symlinks: bool = True) -> None:
        await self._run(os.chmod, self._path, mode, follow_symlinks=follow_symlinks)

    if sys.version_info >= (3, 14):

        async def copy(
            self,
            target: StrPath,
            *,
            follow_symlinks: bool = True,
            preserve_metadata: bool = False,
        ) -> Self:
            target = target._path if isinstance(target, Path) else target
            return self.with_segments(
                await self._run(
                    self._path.copy,
                    target,
                    follow_symlinks=follow_symlinks,
                    preserve_metadata=preserve_metadata,
                )
            )

        async def copy_into(
            self,
            target_dir: StrPath,
            *,
            follow_symlinks: bool = True,
            preserve_metadata: bool = False,
        ) -> Self:
            target_dir = (
                target_dir._path if isinstance(target_dir, Path) else target_dir
            )
            return self.with_segments(
                await self._run(
                    self._path.copy_into,
                    target_dir,
                    follow_symlinks=follow_symlinks,
                    preserve_metadata=preserve_metadata,
                )
            )

        async def move(self, target: StrPath) -> Self:
            target = target._path if isinstance(target, Path) else target
            return self.with_segments(await self._run(self._path.move, target))

        async def move_into(self, target_dir: StrPath) -> Self:
            target_dir = (
                target_dir._path if isinstance(target_dir, Path) else target_dir
            )
            return self.with_segments(await self._run(self._path.move_into, target_dir))

    @classmethod
    async def cwd(
        cls,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        executor: Executor | None = None,
    ) -> Self:
        run_loop = loop or asyncio.get_running_loop()
        path = await run_loop.run_in_executor(executor, pathlib.Path.cwd)
        return cls(path, loop=loop, executor=executor)

    if sys.version_info >= (3, 12):

        async def exists(self, *, follow_symlinks: bool = True) -> bool:
            return await self._run(self._path.exists, follow_symlinks=follow_symlinks)

    else:

        async def exists(self) -> bool:
            return await self._run(self._path.exists)

    async def expanduser(self) -> Self:
        return self.with_segments(await self._run(self._path.expanduser))

    if sys.version_info >= (3, 13):

        @classmethod
        def from_uri(
            cls,
            uri: str,
            *,
            loop: asyncio.AbstractEventLoop | None = None,
            executor: Executor | None = None,
        ) -> Self:
            return cls(pathlib.Path.from_uri(uri), loop=loop, executor=executor)

        def full_match(
            self,
            pattern: StrPath,
            *,
            case_sensitive: bool | None = None,
        ) -> bool:
            return self._path.full_match(pattern, case_sensitive=case_sensitive)

    if sys.version_info >= (3, 13):

        def glob(
            self,
            pattern: str,
            *,
            case_sensitive: bool | None = None,
            recurse_symlinks: bool = False,
        ) -> AsyncIterator[Self]:
            return self._iterate(
                functools.partial(
                    self._path.glob,
                    pattern,
                    case_sensitive=case_sensitive,
                    recurse_symlinks=recurse_symlinks,
                )
            )

    elif sys.version_info >= (3, 12):

        def glob(
            self,
            pattern: str,
            *,
            case_sensitive: bool | None = None,
        ) -> AsyncIterator[Self]:
            return self._iterate(
                functools.partial(
                    self._path.glob, pattern, case_sensitive=case_sensitive
                )
            )

    else:

        def glob(self, pattern: str) -> AsyncIterator[Self]:
            return self._iterate(functools.partial(self._path.glob, pattern))

    if sys.version_info >= (3, 13):

        async def group(self, *, follow_symlinks: bool = True) -> str:
            return await self._run(self._path.group, follow_symlinks=follow_symlinks)

    else:

        async def group(self) -> str:
            return await self._run(self._path.group)

    async def hardlink_to(self, target: StrOrBytesPath) -> None:
        if not hasattr(os, "link"):
            msg = "os.link() not available on this system"
            raise NotImplementedError(msg)
        target = target._path if isinstance(target, Path) else target
        await self._run(os.link, target, self._path)

    @classmethod
    async def home(
        cls,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        executor: Executor | None = None,
    ) -> Self:
        run_loop = loop or asyncio.get_running_loop()
        path = await run_loop.run_in_executor(executor, pathlib.Path.home)
        return cls(path, loop=loop, executor=executor)

    if sys.version_info >= (3, 14):

        @property
        def info(self) -> AsyncPathInfo:
            return AsyncPathInfo(self._path.info, self._ref_loop, self._executor)

    def is_absolute(self) -> bool:
        return self._path.is_absolute()

    async def is_block_device(self) -> bool:
        return await self._run(self._path.is_block_device)

    async def is_char_device(self) -> bool:
        return await self._run(self._path.is_char_device)

    if sys.version_info >= (3, 13):

        async def is_dir(self, *, follow_symlinks: bool = True) -> bool:
            return await self._run(self._path.is_dir, follow_symlinks=follow_symlinks)

        async def is_file(self, *, follow_symlinks: bool = True) -> bool:
            return await self._run(self._path.is_file, follow_symlinks=follow_symlinks)

    else:

        async def is_dir(self) -> bool:
            return await self._run(self._path.is_dir)

        async def is_file(self) -> bool:
            return await self._run(self._path.is_file)

    async def is_fifo(self) -> bool:
        return await self._run(self._path.is_fifo)

    if sys.version_info >= (3, 12):

        async def is_junction(self) -> bool:
            return await self._run(self._path.is_junction)

    async def is_mount(self) -> bool:
        return await self._run(os.path.ismount, self._path)

    if sys.version_info >= (3, 12):

        def is_relative_to(self, other: StrPath) -> bool:
            target = other._path if isinstance(other, Path) else other
            return self._path.is_relative_to(target)

    else:

        def is_relative_to(self, other: StrPath, /, *others: StrPath) -> bool:
            targets = [o._path if isinstance(o, Path) else o for o in (other, *others)]
            return self._path.is_relative_to(*targets)

    if sys.version_info < (3, 15):

        def is_reserved(self) -> bool:
            return self._path.is_reserved()

    async def is_socket(self) -> bool:
        return await self._run(self._path.is_socket)

    async def is_symlink(self) -> bool:
        return await self._run(self._path.is_symlink)

    def iterdir(self) -> AsyncIterator[Self]:
        return self._iterate(self._path.iterdir)

    def joinpath(self, *pathsegments: StrPath) -> Self:
        return self.with_segments(self._path.joinpath(*pathsegments))

    async def lchmod(self, mode: int) -> None:
        await self._run(self._path.lchmod, mode)

    async def lstat(self) -> os.stat_result:
        return await self._run(self._path.lstat)

    if sys.version_info >= (3, 12):

        def match(
            self, path_pattern: str, *, case_sensitive: bool | None = None
        ) -> bool:
            return self._path.match(path_pattern, case_sensitive=case_sensitive)

    else:

        def match(self, path_pattern: str) -> bool:
            return self._path.match(path_pattern)

    async def mkdir(
        self,
        mode: int = 0o777,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        await self._run(self._path.mkdir, mode, parents, exist_ok)

    def open(
        self,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> AiofilesContextManager:
        return _open(
            self._path,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            loop=self._ref_loop,
            executor=self._executor,
        )

    if sys.version_info >= (3, 13):

        async def owner(self, *, follow_symlinks: bool = True) -> str:
            return await self._run(self._path.owner, follow_symlinks=follow_symlinks)

    else:

        async def owner(self) -> str:
            return await self._run(self._path.owner)

    async def read_bytes(self) -> bytes:
        return await self._run(self._path.read_bytes)

    if sys.version_info >= (3, 13):

        async def read_text(
            self,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
        ) -> str:
            return await self._run(self._path.read_text, encoding, errors, newline)

    else:

        async def read_text(
            self,
            encoding: str | None = None,
            errors: str | None = None,
        ) -> str:
            return await self._run(self._path.read_text, encoding, errors)

    async def readlink(self) -> Self:
        return self.with_segments(await self._run(self._path.readlink))

    if sys.version_info >= (3, 12):

        def relative_to(self, other: StrPath, *, walk_up: bool = False) -> Self:
            target = other._path if isinstance(other, Path) else other
            return self.with_segments(self._path.relative_to(target, walk_up=walk_up))

    else:

        def relative_to(self, *other: StrPath) -> Self:
            targets = [o._path if isinstance(o, Path) else o for o in other]
            return self.with_segments(self._path.relative_to(*targets))

    async def rename(self, target: StrPath) -> Self:
        target = target._path if isinstance(target, Path) else pathlib.Path(target)
        return self.with_segments(await self._run(self._path.rename, target))

    async def replace(self, target: StrPath) -> Self:
        target = target._path if isinstance(target, Path) else pathlib.Path(target)
        return self.with_segments(await self._run(self._path.replace, target))

    async def resolve(self, strict: bool = False) -> Self:
        return self.with_segments(await self._run(self._path.resolve, strict=strict))

    if sys.version_info >= (3, 13):

        def rglob(
            self,
            pattern: str,
            *,
            case_sensitive: bool | None = None,
            recurse_symlinks: bool = False,
        ) -> AsyncIterator[Self]:
            return self._iterate(
                functools.partial(
                    self._path.rglob,
                    pattern,
                    case_sensitive=case_sensitive,
                    recurse_symlinks=recurse_symlinks,
                )
            )

    elif sys.version_info >= (3, 12):

        def rglob(
            self,
            pattern: str,
            *,
            case_sensitive: bool | None = None,
        ) -> AsyncIterator[Self]:
            return self._iterate(
                functools.partial(
                    self._path.rglob, pattern, case_sensitive=case_sensitive
                )
            )

    else:

        def rglob(self, pattern: str) -> AsyncIterator[Self]:
            return self._iterate(functools.partial(self._path.rglob, pattern))

    async def rmdir(self) -> None:
        await self._run(self._path.rmdir)

    async def samefile(self, other_path: StrPath) -> bool:
        target = other_path._path if isinstance(other_path, Path) else other_path
        return await self._run(self._path.samefile, target)

    async def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        return await self._run(os.stat, self._path, follow_symlinks=follow_symlinks)

    async def symlink_to(
        self,
        target: StrOrBytesPath,
        target_is_directory: bool = False,
    ) -> None:
        target = target._path if isinstance(target, Path) else target
        await self._run(self._path.symlink_to, target, target_is_directory)

    async def touch(self, mode: int = 0o666, exist_ok: bool = True) -> None:
        await self._run(self._path.touch, mode, exist_ok)

    async def unlink(self, missing_ok: bool = False) -> None:
        await self._run(self._path.unlink, missing_ok)

    if sys.version_info >= (3, 12):

        async def walk(
            self,
            top_down: bool = True,
            on_error: Callable[[OSError], object] | None = None,
            follow_symlinks: bool = False,
        ) -> AsyncIterator[tuple[Self, list[str], list[str]]]:
            gen = await self._run(self._path.walk, top_down, on_error, follow_symlinks)

            def step() -> tuple[pathlib.Path, list[str], list[str]] | None:
                return next(gen, None)

            while (item := await self._run(step)) is not None:
                root, dirs, files = item
                yield self.with_segments(root), dirs, files

    def with_name(self, name: str) -> Self:
        return self.with_segments(self._path.with_name(name))

    def with_segments(self, *pathsegments: StrPath) -> Self:
        return type(self)(*pathsegments, loop=self._ref_loop, executor=self._executor)

    if sys.version_info >= (3, 13):

        def with_stem(self, stem: str) -> Self:
            return self.with_segments(self._path.with_stem(stem))

    else:

        def with_stem(self, stem: str) -> Self:
            # Match Python 3.13+ behavior for empty stems on paths with
            # a non-empty suffix (python/cpython#114610).
            suffix = self._path.suffix
            if not suffix:
                return self.with_name(stem)
            if not stem:
                msg = f"{self!r} has a non-empty suffix"
                raise ValueError(msg)
            return self.with_name(stem + suffix)

    def with_suffix(self, suffix: str) -> Self:
        return self.with_segments(self._path.with_suffix(suffix))

    async def write_bytes(self, data: ReadableBuffer) -> int:
        return await self._run(self._path.write_bytes, data)

    if sys.version_info >= (3, 10):

        async def write_text(
            self,
            data: str,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
        ) -> int:
            return await self._run(
                self._path.write_text, data, encoding, errors, newline
            )

    else:

        async def write_text(
            self,
            data: str,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
        ) -> int:
            # Replicate Path.write_text with the newline parameter,
            # which this <3.10 pathlib lacks.
            def write() -> int:
                if not isinstance(data, str):
                    msg = f"data must be str, not {type(data).__name__}"
                    raise TypeError(msg)
                with self._path.open(
                    mode="w", encoding=encoding, errors=errors, newline=newline
                ) as f:
                    return f.write(data)

            return await self._run(write)


os.PathLike.register(Path)
