from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


WriteText = Callable[[Path, str], object]
WriteBytes = Callable[[Path, bytes], object]
WriteSymlink = Callable[[Path, str], object]
WriteDirectory = Callable[[Path], object]


@dataclass(slots=True)
class _Operation:
    path: Path
    kind: str
    value: str | bytes | None
    writer: WriteText | WriteBytes | WriteSymlink | WriteDirectory


class RecoveryError(OSError):
    def __init__(self, path: Path, cause: BaseException) -> None:
        self.path = path
        self.cause = cause
        super().__init__(f"Recovery failed for {path}: {cause}")


class TransactionError(OSError):
    def __init__(self, operation: Path, cause: BaseException, recovery: BaseException | None = None) -> None:
        self.operation = operation
        self.cause = cause
        self.recovery = recovery
        message = f"Transaction write failed for {operation}: {cause}"
        if recovery is not None:
            message += f"; recovery failed for {getattr(recovery, 'path', operation)}: {recovery}"
        super().__init__(message)


class FileTransaction:
    """Stage bounded file writes and restore the exact pre-write bytes on failure."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve(strict=False)
        self._operations: list[_Operation] = []
        self._by_path: dict[Path, _Operation] = {}
        self._snapshots: dict[Path, tuple[bool, bytes | None, int | None]] = {}
        self._created_dirs: list[Path] = []
        self._attempted: list[Path] = []
        self._directory_operations: set[Path] = set()
        self._symlink_operations: set[Path] = set()
        self._current_operation: Path | None = None
        self._committed = False

    @property
    def operations(self) -> tuple[_Operation, ...]:
        return tuple(self._operations)

    def add_text(self, path: Path, text: str, writer: WriteText) -> None:
        self._add(_Operation(path=path, kind="text", value=text, writer=writer))

    def add_bytes(self, path: Path, value: bytes, writer: WriteBytes) -> None:
        self._add(_Operation(path=path, kind="bytes", value=value, writer=writer))

    def add_symlink(self, path: Path, target: str, writer: WriteSymlink) -> None:
        self._add(_Operation(path=path, kind="symlink", value=target, writer=writer))

    def add_directory(self, path: Path, writer: WriteDirectory) -> None:
        self._add(_Operation(path=path, kind="directory", value=None, writer=writer))

    def planned_paths(self) -> list[Path]:
        return [operation.path for operation in self._operations]

    def validate(self) -> None:
        for operation in self._operations:
            self._current_operation = operation.path
            self._validate_path(operation.path)
            path = operation.path
            if operation.kind == "directory":
                if path.is_symlink():
                    raise OSError(f"Refusing to replace symbolic link: {path}")
                if path.exists() and not path.is_dir():
                    raise OSError(f"Transaction directory is not a directory: {path}")
                if path.exists():
                    stat_result = path.stat()
                    self._snapshots[path] = (True, None, stat_result.st_mode)
                else:
                    self._snapshots[path] = (False, None, None)
                continue
            if path.exists() and not path.is_file() and not path.is_symlink():
                raise OSError(f"Transaction target is not a file: {path}")
            if path.is_symlink():
                raise OSError(f"Refusing to replace symbolic link: {path}")
            if path.exists():
                stat_result = path.stat()
                self._snapshots[path] = (True, path.read_bytes(), stat_result.st_mode)
            else:
                self._snapshots[path] = (False, None, None)

    def commit(self) -> None:
        try:
            self.validate()
            for operation in self._operations:
                self._current_operation = operation.path
                self._ensure_parent(operation.path)
                self._validate_path(operation.path)
                if operation.path.is_symlink():
                    raise OSError(f"Refusing to replace symbolic link: {operation.path}")
                self._attempted.append(operation.path)
                if operation.kind == "directory":
                    operation.writer(operation.path)
                else:
                    operation.writer(operation.path, operation.value)
        except BaseException as exc:
            recovery = self.rollback()
            operation = self._current_operation or (self._attempted[-1] if self._attempted else self.root)
            raise TransactionError(operation, exc, recovery) from exc
        finally:
            self._current_operation = None
        self._committed = True

    def rollback(self) -> BaseException | None:
        recovery: BaseException | None = None
        for path in reversed(self._attempted):
            try:
                self._restore(path)
            except BaseException as exc:
                recovery = RecoveryError(path, exc)
                break
        if recovery is None:
            for directory in reversed(self._created_dirs):
                try:
                    self._validate_directory_path(directory)
                    directory.rmdir()
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    recovery = RecoveryError(directory, exc)
                    break
        if recovery is None:
            self._committed = False
        return recovery

    def _add(self, operation: _Operation) -> None:
        path = operation.path.absolute()
        operation.path = path
        self._directory_operations.discard(path)
        self._symlink_operations.discard(path)
        if operation.kind == "directory":
            self._directory_operations.add(path)
        elif operation.kind == "symlink":
            self._symlink_operations.add(path)
        previous = self._by_path.get(path)
        if previous is not None:
            index = self._operations.index(previous)
            self._operations[index] = operation
        else:
            self._operations.append(operation)
        self._by_path[path] = operation

    def _validate_path(self, path: Path) -> None:
        self._validate_parent_chain(path)

    def _validate_parent_chain(self, path: Path) -> None:
        try:
            relative = path.relative_to(self.root)
        except ValueError as exc:
            raise OSError(f"Transaction path escapes its root: {path}") from exc

        current = self.root
        if current.is_symlink():
            raise OSError(f"Refusing to traverse symbolic link: {current}")
        for part in relative.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise OSError(f"Refusing to traverse symbolic link: {current}")
            if current.exists() and not current.is_dir():
                raise OSError(f"Transaction parent is not a directory: {current}")

    def _validate_directory_path(self, path: Path) -> None:
        try:
            relative = path.relative_to(self.root)
        except ValueError as exc:
            raise OSError(f"Transaction path escapes its root: {path}") from exc
        current = self.root
        if current.is_symlink():
            raise OSError(f"Refusing to traverse symbolic link: {current}")
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise OSError(f"Refusing to traverse symbolic link: {current}")
            if current.exists() and not current.is_dir():
                raise OSError(f"Transaction parent is not a directory: {current}")

    def _ensure_parent(self, path: Path) -> None:
        missing: list[Path] = []
        current = path.parent
        while not current.exists():
            missing.append(current)
            current = current.parent
        if current.is_symlink():
            raise OSError(f"Refusing to traverse symbolic link: {current}")
        for directory in reversed(missing):
            if directory.is_symlink():
                raise OSError(f"Refusing to traverse symbolic link: {directory}")
            directory.mkdir()
            self._created_dirs.append(directory)

    def _restore(self, path: Path) -> None:
        self._validate_parent_chain(path)
        existed, original, mode = self._snapshots[path]
        if path in self._directory_operations:
            if not existed:
                if path.is_symlink():
                    raise OSError(f"Refusing to remove symbolic link: {path}")
                if path.exists() and not path.is_dir():
                    raise OSError(f"Refusing to remove non-directory transaction output: {path}")
                if path.exists():
                    path.rmdir()
            return
        if not existed:
            if path.is_symlink():
                if path in self._symlink_operations:
                    path.unlink()
                    return
                raise OSError(f"Refusing to remove symbolic link: {path}")
            if path.exists():
                if not path.is_file():
                    raise OSError(f"Refusing to remove non-file transaction output: {path}")
                path.unlink()
            return
        if path.is_symlink():
            raise OSError(f"Refusing to replace symbolic link during recovery: {path}")
        assert original is not None
        path.write_bytes(original)
        if mode is not None:
            os.chmod(path, mode)
