#!/usr/bin/env python3
"""Discover scoped repository instructions and executable validation commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

CONFIG_NAME = ".rad-repo.json"
DEFAULT_PROFILE = "core"
PROFILE_NAMES = {"core", "full"}
APPROVAL_KEY = "rad-repo.approvedValidationSha"
COMMAND_LABELS = ("build", "test", "lint", "type-check", "typecheck", "validate", "check")
COMMAND_RE = re.compile(
    rf"(?:{'|'.join(re.escape(label) for label in COMMAND_LABELS)})\s*:\s*`([^`]+)`",
    re.IGNORECASE,
)
TABLE_COMMAND_RE = re.compile(
    rf"^\s*\|\s*(?:{'|'.join(re.escape(label) for label in COMMAND_LABELS)})\s*\|\s*`?([^|`]+)`?\s*\|",
    re.IGNORECASE,
)
PLACEHOLDER_COMMANDS = {"<command>", "none", "n/a", "not configured", "not applicable"}
IGNORED_INSTRUCTION_DIRS = {
    ".git", ".hg", ".svn", ".next", ".venv", ".worktrees", "build",
    "coverage", "dist", "fixtures", "node_modules", "target", "templates", "vendor",
}


@dataclass(frozen=True)
class RepositoryContract:
    root: Path
    config: dict
    config_path: Path


def load_config(root: Path, config_path: Path | None = None) -> dict:
    path = config_path or root / CONFIG_NAME
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid repository config {path}: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"invalid repository config {path}: root must be an object")
    return data


def load_contract(root: Path, config_path: Path | None = None) -> RepositoryContract:
    resolved = root.resolve()
    resolved_config = (config_path or resolved / CONFIG_NAME).resolve(strict=False)
    return RepositoryContract(
        root=resolved,
        config=load_config(resolved, resolved_config),
        config_path=resolved_config,
    )


def all_instruction_files(root: Path) -> list[Path]:
    root = root.resolve()
    files: list[Path] = []
    for path in root.rglob("AGENTS.md"):
        relative = path.relative_to(root)
        if _is_ignored_instruction_path(relative):
            continue
        try:
            path.resolve().relative_to(root)
        except (OSError, ValueError):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def _is_ignored_instruction_path(relative: Path) -> bool:
    return any(part in IGNORED_INSTRUCTION_DIRS for part in relative.parts[:-1])


def applicable_instruction_files(root: Path, target: str | Path) -> list[Path]:
    root = root.resolve()
    target_path = Path(target)
    if not target_path.is_absolute():
        target_path = root / target_path
    target_path = target_path.resolve(strict=False)
    try:
        relative = target_path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"target is outside repository: {target}") from error

    parent = relative if target_path.is_dir() else relative.parent
    candidates = [root / "AGENTS.md"]
    current = root
    for part in parent.parts:
        current /= part
        candidates.append(current / "AGENTS.md")
    applicable: list[Path] = []
    for path in candidates:
        candidate_relative = path.relative_to(root)
        if _is_ignored_instruction_path(candidate_relative):
            continue
        if path.is_file():
            applicable.append(path)
    return applicable


def commands_from_instruction(path: Path) -> list[str]:
    commands: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    candidates = [match.group(1) for match in COMMAND_RE.finditer(text)]
    candidates.extend(
        match.group(1)
        for line in text.splitlines()
        if (match := TABLE_COMMAND_RE.match(line))
    )
    for candidate in candidates:
        command = candidate.strip()
        if command and command.lower() not in PLACEHOLDER_COMMANDS and command not in commands:
            commands.append(command)
    return commands


def repository_profile(contract: RepositoryContract) -> str:
    profile = contract.config.get("profile", DEFAULT_PROFILE)
    if profile not in PROFILE_NAMES:
        raise ValueError("profile must be 'core' or 'full'")
    return profile


def _matches_scope(path: str, scope: str) -> bool:
    normalized_path = Path(path).as_posix().strip("/")
    normalized_scope = Path(scope).as_posix().strip("/")
    return normalized_path == normalized_scope or normalized_path.startswith(normalized_scope + "/")


def validation_plan(contract: RepositoryContract, changed_paths: list[str]) -> dict:
    command_entries: list[dict] = []
    instruction_map: dict[str, list[str]] = {}
    matched_paths: set[str] = set()

    def add(command: str, source: str) -> None:
        if command and not any(entry["command"] == command for entry in command_entries):
            command_entries.append({"command": command, "source": source})

    targets = changed_paths or ["."]
    for target in targets:
        instructions = applicable_instruction_files(contract.root, target)
        instruction_map[target] = [
            instruction.relative_to(contract.root).as_posix()
            for instruction in instructions
        ]
        for instruction in instructions:
            instruction_commands = commands_from_instruction(instruction)
            if instruction_commands and target in changed_paths:
                matched_paths.add(target)
            for command in instruction_commands:
                add(command, instruction.relative_to(contract.root).as_posix())

    validation = contract.config.get("validation", {})
    if not isinstance(validation, dict):
        raise ValueError("validation config must be an object")
    root_commands = validation.get("commands", [])
    if not isinstance(root_commands, list) or not all(isinstance(item, str) for item in root_commands):
        raise ValueError("validation.commands must be a list of strings")
    for command in root_commands:
        add(command, f"{contract.config_path.name}#validation.commands")
    if root_commands:
        matched_paths.update(changed_paths)

    scopes = validation.get("scopes", {})
    if not isinstance(scopes, dict):
        raise ValueError("validation.scopes must be an object")
    for scope, scoped_commands in scopes.items():
        if not isinstance(scope, str) or not scope.strip():
            raise ValueError("validation.scopes keys must be non-empty paths")
        if not isinstance(scoped_commands, list) or not all(isinstance(item, str) for item in scoped_commands):
            raise ValueError(f"validation.scopes.{scope} must be a list of strings")
        scope_path = (contract.root / Path(scope)).resolve(strict=False)
        try:
            scope_path.relative_to(contract.root)
        except ValueError as error:
            raise ValueError(f"validation scope target is outside repository: {scope}") from error
        if not scope_path.exists():
            raise ValueError(f"validation scope target does not exist: {scope}")
        if any(_matches_scope(path, scope) for path in changed_paths):
            if scoped_commands:
                matched_paths.update(path for path in changed_paths if _matches_scope(path, scope))
            for command in scoped_commands:
                add(command, f"{contract.config_path.name}#validation.scopes.{scope}")

    allow_empty = validation.get("allow_empty", False)
    if not isinstance(allow_empty, bool):
        raise ValueError("validation.allow_empty must be a boolean")
    return {
        "profile": repository_profile(contract),
        "instruction_map": instruction_map,
        "commands": command_entries,
        "allow_empty": allow_empty,
        "unmatched_paths": [path for path in changed_paths if path not in matched_paths],
    }


def validation_commands(contract: RepositoryContract, changed_paths: list[str]) -> list[str]:
    return [entry["command"] for entry in validation_plan(contract, changed_paths)["commands"]]


def validation_fingerprint(plan: dict) -> str:
    payload = {
        "commands": plan["commands"],
        "allow_empty": plan["allow_empty"],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def approved_validation_fingerprint(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "config", "--local", "--get", APPROVAL_KEY],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    value = result.stdout.strip()
    return value or None


def approve_validation_fingerprint(root: Path, fingerprint: str) -> None:
    subprocess.run(
        ["git", "config", "--local", APPROVAL_KEY, fingerprint],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        contract = load_contract(Path(args.root), args.config)
        paths = args.paths or ["."]
        plan = validation_plan(contract, paths)
        fingerprint = validation_fingerprint(plan)
        approved = approved_validation_fingerprint(contract.root)
        report = {
            "profile": plan["profile"],
            "instruction_map": plan["instruction_map"],
            "validation_commands": [entry["command"] for entry in plan["commands"]],
            "command_sources": plan["commands"],
            "allow_empty": plan["allow_empty"],
            "unmatched_paths": plan["unmatched_paths"],
            "validation_fingerprint": fingerprint,
            "validation_trusted": (
                not plan["commands"] and plan["allow_empty"]
            ) or (
                bool(plan["commands"]) and approved == fingerprint
            ),
        }
    except ValueError as error:
        report = {"error": str(error)}
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"ERROR: {error}")
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for path, instructions in report["instruction_map"].items():
            print(f"{path}: {', '.join(instructions) or '(no AGENTS.md)'}")
        for command in report["validation_commands"]:
            print(f"validate: {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
