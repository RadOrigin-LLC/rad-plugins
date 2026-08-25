#!/usr/bin/env python3
"""Plan and apply safe PARA moves inside one approved root.

The command has two phases.  A dry run validates every source and target and
writes a ledger.  Apply reads that ledger, requires approval, and records each
move.  If a later move fails, earlier moves are restored in reverse order.
The ledger is kept so an incomplete restoration can be recovered by hand.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence


LEDGER_FORMAT = "rad-para-move-ledger"
LEDGER_VERSION = 1
MoveFn = Callable[[Path, Path], object]


class MoveContractError(ValueError):
    """Raised when a move plan or ledger does not meet the safety contract."""


class MoveApplyError(RuntimeError):
    """Raised after an apply failure, including the restoration result."""

    def __init__(self, message: str, result: Mapping[str, object]):
        super().__init__(message)
        self.result = dict(result)


def _absolute(path: Path) -> Path:
    """Return an absolute lexical path without following links."""
    return Path(os.path.abspath(os.fspath(path)))


def approved_root(root: str | os.PathLike[str]) -> Path:
    """Validate and resolve the one root allowed by this module."""
    candidate = Path(root)
    if not candidate.exists():
        raise MoveContractError(f"approved root does not exist: {candidate}")
    if candidate.is_symlink():
        raise MoveContractError(f"approved root cannot be a link: {candidate}")
    if not candidate.is_dir():
        raise MoveContractError(f"approved root is not a directory: {candidate}")
    try:
        return candidate.resolve(strict=True)
    except OSError as exc:
        raise MoveContractError(f"cannot read approved root {candidate}: {exc}") from exc


def _lexically_inside(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath([os.fspath(root), os.fspath(candidate)]) == os.fspath(root)
    except ValueError:
        return False


def _symlink_component(root: Path, candidate: Path) -> Path | None:
    """Return the first link component between root and candidate, if any."""
    lexical_root = _absolute(root)
    lexical_candidate = _absolute(candidate)
    if not _lexically_inside(lexical_root, lexical_candidate):
        return None
    relative = os.path.relpath(os.fspath(lexical_candidate), os.fspath(lexical_root))
    current = lexical_root
    if relative == ".":
        return None
    for part in Path(relative).parts:
        current = current / part
        try:
            if current.is_symlink():
                return current
        except OSError as exc:
            raise MoveContractError(f"cannot inspect {current}: {exc}") from exc
    return None


def _inside_root(root: Path, value: str | os.PathLike[str], *, label: str) -> Path:
    raw = Path(value)
    candidate = raw if raw.is_absolute() else root / raw
    lexical = _absolute(candidate)
    if not _lexically_inside(_absolute(root), lexical):
        raise MoveContractError(f"{label} escapes the approved root: {value}")
    link = _symlink_component(root, lexical)
    if link is not None:
        raise MoveContractError(f"{label} uses a link: {link}")
    try:
        resolved = lexical.resolve(strict=False)
    except OSError as exc:
        raise MoveContractError(f"cannot resolve {label} {value}: {exc}") from exc
    if not _lexically_inside(root, resolved):
        raise MoveContractError(f"{label} escapes the approved root: {value}")
    return resolved


def _inspect_source(root: Path, source: str | os.PathLike[str]) -> Path:
    path = _inside_root(root, source, label="source")
    if path == root:
        raise MoveContractError("source cannot be the approved root")
    try:
        path.lstat()
    except FileNotFoundError as exc:
        raise MoveContractError(f"source does not exist: {source}") from exc
    except OSError as exc:
        raise MoveContractError(f"cannot inspect source {source}: {exc}") from exc
    if path.is_symlink():
        raise MoveContractError(f"source is a link: {source}")
    return path


def _inspect_target(root: Path, target: str | os.PathLike[str]) -> Path:
    path = _inside_root(root, target, label="target")
    if path == root:
        raise MoveContractError("target cannot be the approved root")
    if path.exists() or path.is_symlink():
        raise MoveContractError(f"target already exists: {target}")
    parent = path.parent
    if not parent.exists() or not parent.is_dir():
        raise MoveContractError(f"target parent does not exist: {parent}")
    if _symlink_component(root, parent) is not None:
        raise MoveContractError(f"target parent uses a link: {parent}")
    try:
        parent.lstat()
    except OSError as exc:
        raise MoveContractError(f"cannot inspect target parent {parent}: {exc}") from exc
    return path


def _coerce_pair(item: object) -> tuple[object, object]:
    if isinstance(item, Mapping):
        if "source" not in item or "target" not in item:
            raise MoveContractError("each move must contain source and target")
        return item["source"], item["target"]
    if isinstance(item, Sequence) and not isinstance(item, (str, bytes)) and len(item) == 2:
        return item[0], item[1]
    raise MoveContractError("each move must be a two-item source/target pair")


def validate_moves(
    root: str | os.PathLike[str], moves: Iterable[object]
) -> list[dict[str, str]]:
    """Validate and normalize a move list without changing the filesystem."""
    root_path = approved_root(root)
    entries: list[dict[str, str]] = []
    sources: set[str] = set()
    targets: set[str] = set()
    for item in moves:
        source_value, target_value = _coerce_pair(item)
        source = _inspect_source(root_path, os.fspath(source_value))
        target = _inspect_target(root_path, os.fspath(target_value))
        source_key = os.path.normcase(os.fspath(source))
        target_key = os.path.normcase(os.fspath(target))
        if source_key in sources:
            raise MoveContractError(f"source appears more than once: {source}")
        if target_key in targets:
            raise MoveContractError(f"target appears more than once: {target}")
        if source == target:
            raise MoveContractError(f"source and target are the same: {source}")
        if source.is_dir() and target.is_relative_to(source):
            raise MoveContractError(f"target is inside source: {target}")
        sources.add(source_key)
        targets.add(target_key)
        entries.append({"source": os.fspath(source), "target": os.fspath(target), "status": "planned"})
    if not entries:
        raise MoveContractError("move plan is empty")
    return entries


def _ledger_path(root: Path, ledger: str | os.PathLike[str]) -> Path:
    path = _inside_root(root, ledger, label="ledger")
    if path.exists() and path.is_dir():
        raise MoveContractError(f"ledger path is a directory: {path}")
    return path


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=False, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _write_recovery_evidence(path: Path, value: Mapping[str, object]) -> Path | None:
    """Keep recovery evidence even when the normal ledger writer fails."""
    payload = json.dumps(value, indent=2) + "\n"
    candidates = (path, path.with_name(path.name + ".recovery.json"))
    for candidate in candidates:
        try:
            candidate.write_text(payload, encoding="utf-8")
            return candidate
        except OSError:
            continue
    return None


def _new_ledger(root: Path, entries: list[dict[str, str]]) -> dict[str, object]:
    return {
        "format": LEDGER_FORMAT,
        "version": LEDGER_VERSION,
        "root": os.fspath(root),
        "approved": False,
        "status": "dry-run",
        "entries": entries,
    }


def write_dry_run_ledger(
    root: str | os.PathLike[str], moves: Iterable[object], ledger: str | os.PathLike[str]
) -> dict[str, object]:
    """Validate moves and write an unapproved dry-run ledger."""
    root_path = approved_root(root)
    ledger_path = _ledger_path(root_path, ledger)
    entries = validate_moves(root_path, moves)
    value = _new_ledger(root_path, entries)
    _write_json(ledger_path, value)
    value["ledger"] = os.fspath(ledger_path)
    return value


def load_ledger(
    ledger: str | os.PathLike[str], root: str | os.PathLike[str] | None = None
) -> tuple[Path, Path, dict[str, object]]:
    if root is None:
        raise MoveContractError("approved root is required before reading a ledger")
    root_path = approved_root(root)
    path = _ledger_path(root_path, ledger)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MoveContractError(f"cannot read ledger {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("format") != LEDGER_FORMAT:
        raise MoveContractError(f"invalid PARA move ledger: {path}")
    if value.get("version") != LEDGER_VERSION or not isinstance(value.get("entries"), list):
        raise MoveContractError(f"unsupported PARA move ledger: {path}")
    stored_root = approved_root(value.get("root", ""))
    if os.path.normcase(os.fspath(root_path)) != os.path.normcase(os.fspath(stored_root)):
        raise MoveContractError("ledger root does not match the approved root")
    return root_path, path, value


def approve_ledger(
    ledger: str | os.PathLike[str], root: str | os.PathLike[str]
) -> dict[str, object]:
    """Mark an existing dry-run ledger approved after human review."""
    root_path, ledger_path, value = load_ledger(ledger, root)
    if value.get("status") != "dry-run":
        raise MoveContractError("only a dry-run ledger can be approved")
    value["approved"] = True
    value["status"] = "approved"
    _write_json(ledger_path, value)
    return value


def _validate_ledger_entries(root: Path, value: Mapping[str, object]) -> list[dict[str, str]]:
    raw_entries = value.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise MoveContractError("ledger has no move entries")
    normalized = validate_moves(root, [(item.get("source"), item.get("target")) for item in raw_entries if isinstance(item, Mapping)])
    if len(normalized) != len(raw_entries):
        raise MoveContractError("ledger contains an invalid move entry")
    for index, entry in enumerate(raw_entries):
        if not isinstance(entry, Mapping):
            raise MoveContractError("ledger contains an invalid move entry")
        if os.path.normcase(entry.get("source", "")) != os.path.normcase(normalized[index]["source"]):
            raise MoveContractError("ledger source changed since dry run")
        if os.path.normcase(entry.get("target", "")) != os.path.normcase(normalized[index]["target"]):
            raise MoveContractError("ledger target changed since dry run")
    return normalized


def apply_ledger(
    ledger: str | os.PathLike[str],
    *,
    root: str | os.PathLike[str] | None = None,
    move_fn: MoveFn | None = None,
    restore_fn: MoveFn | None = None,
) -> dict[str, object]:
    """Apply an approved ledger and restore prior moves after the first failure.

    Approval must be durable in the ledger. There is no in-memory approval
    bypass for callers.
    """
    if not isinstance(ledger, (str, os.PathLike)):
        raise MoveContractError("apply requires a durable ledger path")
    root_path, ledger_path, value = load_ledger(ledger, root)
    if value.get("status") not in {"dry-run", "approved"}:
        raise MoveContractError(f"ledger is not ready to apply: {value.get('status')}")
    if not value.get("approved"):
        raise MoveContractError("apply requires an approved dry-run ledger")
    entries = _validate_ledger_entries(root_path, value)
    value["approved"] = True
    value["status"] = "applying"
    value["entries"] = entries
    _write_json(ledger_path, value)

    mover = move_fn or (lambda source, target: shutil.move(os.fspath(source), os.fspath(target)))
    restorer = restore_fn or mover
    moved: list[int] = []
    failure: str | None = None
    for index, entry in enumerate(entries):
        source = Path(entry["source"])
        target = Path(entry["target"])
        try:
            mover(source, target)
        except Exception as exc:  # the ledger must record every operational failure
            entry["status"] = "failed"
            entry["error"] = f"{type(exc).__name__}: {exc}"
            failure = entry["error"]
            break
        entry["status"] = "applied"
        moved.append(index)
        try:
            _write_json(ledger_path, value)
        except Exception as exc:
            entry["status"] = "ledger_write_failed"
            entry["error"] = f"{type(exc).__name__}: {exc}"
            failure = entry["error"]
            break

    if failure is None:
        value["status"] = "applied"
        value["partial_success"] = False
        try:
            _write_json(ledger_path, value)
        except Exception as exc:
            failure = f"{type(exc).__name__}: {exc}"
            value["ledger_write_error"] = failure
        else:
            value["ledger"] = os.fspath(ledger_path)
            return value

    value["partial_success"] = bool(moved)
    restoration_errors: list[str] = []
    for index in reversed(moved):
        entry = entries[index]
        source = Path(entry["source"])
        target = Path(entry["target"])
        try:
            restorer(target, source)
        except Exception as exc:  # keep exact paths when manual recovery is needed
            entry["status"] = "restoration_failed"
            entry["restoration_error"] = f"{type(exc).__name__}: {exc}"
            restoration_errors.append(f"{source} <- {target}: {entry['restoration_error']}")
        else:
            entry["status"] = "restored"
    value["status"] = "restoration_incomplete" if restoration_errors else "failed_restored"
    value["apply_error"] = failure
    value["restoration_errors"] = restoration_errors
    try:
        _write_json(ledger_path, value)
    except Exception as exc:
        value["recovery_write_error"] = f"{type(exc).__name__}: {exc}"
        evidence = _write_recovery_evidence(ledger_path, value)
        if evidence is not None:
            value["recovery_evidence"] = os.fspath(evidence)
    value["ledger"] = os.fspath(ledger_path)
    raise MoveApplyError(
        "move failed; prior moves were restored" if not restoration_errors else "move failed; manual recovery is required",
        value,
    )


def _parse_moves(args: argparse.Namespace) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = list(args.move or [])
    sources = args.source or []
    targets = args.target or []
    if len(sources) != len(targets):
        raise MoveContractError("--source and --target must have the same count")
    pairs.extend(zip(sources, targets))
    if not pairs:
        raise MoveContractError("provide at least one --move SOURCE TARGET pair")
    return pairs


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="approved PARA root")
    parser.add_argument("--ledger", help="ledger path, inside the approved root")
    parser.add_argument("--move", nargs=2, action="append", metavar=("SOURCE", "TARGET"))
    parser.add_argument("--source", action="append", help="source path, paired with --target")
    parser.add_argument("--target", action="append", help="target path, paired with --source")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--approve", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.approve:
            if not args.ledger or not args.root:
                raise MoveContractError("--approve requires --root and --ledger")
            approve_ledger(args.ledger, args.root)
            print(json.dumps({"status": "approved", "ledger": os.fspath(Path(args.ledger))}))
            return 0
        if not args.root:
            raise MoveContractError("--root is required for --dry-run or --apply")
        root_path = approved_root(args.root)
        ledger_path = args.ledger or root_path / ".rad-para-move-ledger.json"
        if args.dry_run:
            value = write_dry_run_ledger(root_path, _parse_moves(args), ledger_path)
            print(json.dumps(value, indent=2))
            return 0
        if not args.ledger:
            raise MoveContractError("--apply requires --ledger")
        value = apply_ledger(args.ledger, root=root_path)
        print(json.dumps(value, indent=2))
        return 0
    except MoveApplyError as exc:
        print(json.dumps(exc.result, indent=2), file=sys.stderr)
        return 1
    except MoveContractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
