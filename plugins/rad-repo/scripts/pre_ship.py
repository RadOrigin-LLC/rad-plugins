#!/usr/bin/env python3
"""Inspect staged changes and optionally run the repository validation contract."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import time
from pathlib import Path

from repo_contract import (
    all_instruction_files,
    approved_validation_fingerprint,
    load_contract,
    validation_fingerprint,
    validation_plan,
)

DEFAULT_LARGE_FILE_BYTES = 5 * 1024 * 1024
DEFAULT_GENERATED_DIRS = {".next", "build", "coverage", "dist", "node_modules", "target", "vendor"}
PROTECTED_NAMES = {"credentials.json", "id_dsa", "id_ed25519", "id_rsa", "service-account.json", "secrets.json"}
PROTECTED_SUFFIXES = {".key", ".p12", ".pem", ".pfx"}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
)


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, check=check
    )


def staged_paths(root: Path) -> list[str]:
    result = run_git(root, "-c", "core.quotepath=false", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")
    return [item.decode("utf-8", errors="replace") for item in result.stdout.split(b"\0") if item]


def staged_blob(root: Path, path: str) -> bytes:
    return run_git(root, "show", f":{path}").stdout


def dirty_contract_files(root: Path) -> list[str]:
    paths = [path.relative_to(root).as_posix() for path in all_instruction_files(root)]
    config_path = root / ".rad-repo.json"
    if config_path.exists():
        paths.append(".rad-repo.json")
    if not paths:
        return []
    result = run_git(
        root,
        "-c",
        "core.quotepath=false",
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        *paths,
    )
    dirty: list[str] = []
    for line in result.stdout.decode("utf-8", errors="replace").splitlines():
        status = line[:2]
        if status == "??" or (len(status) == 2 and status[1] != " "):
            dirty.append(line[3:].strip())
    return sorted(dirty)


def is_protected_path(path: str, allowed_patterns: list[str]) -> bool:
    normalized = Path(path).as_posix()
    if any(fnmatch.fnmatch(normalized, pattern) for pattern in allowed_patterns):
        return False
    name = Path(normalized).name.lower()
    if name == ".env.example" or name.startswith(".env.example."):
        return False
    return (
        name == ".env"
        or name.startswith(".env.")
        or name in PROTECTED_NAMES
        or Path(name).suffix in PROTECTED_SUFFIXES
    )


def scan_staged(root: Path, config: dict, allow_contract_change: bool = False) -> tuple[list[str], list[dict]]:
    shipping = config.get("shipping", {})
    if not isinstance(shipping, dict):
        raise ValueError("shipping config must be an object")
    large_limit = shipping.get("large_file_bytes", DEFAULT_LARGE_FILE_BYTES)
    if not isinstance(large_limit, int) or large_limit < 1:
        raise ValueError("shipping.large_file_bytes must be a positive integer")
    generated_config = shipping.get("generated_dirs", sorted(DEFAULT_GENERATED_DIRS))
    if not isinstance(generated_config, list) or not all(isinstance(item, str) for item in generated_config):
        raise ValueError("shipping.generated_dirs must be a list of strings")
    generated_dirs = set(generated_config)
    allowed_patterns = shipping.get("allow_protected_paths", [".env.example", ".env.example.*"])
    if not isinstance(allowed_patterns, list) or not all(isinstance(item, str) for item in allowed_patterns):
        raise ValueError("shipping.allow_protected_paths must be a list of strings")

    paths = staged_paths(root)
    findings: list[dict] = []
    for path in paths:
        if not allow_contract_change and (Path(path).name == "AGENTS.md" or path == ".rad-repo.json"):
            findings.append({
                "kind": "contract_change", "path": path,
                "message": "repository contract changed; review it and rerun with --allow-contract-change",
            })
            continue
        if is_protected_path(path, allowed_patterns):
            findings.append({"kind": "protected_path", "path": path, "message": "protected credential path is staged"})
            continue
        if any(part in generated_dirs for part in Path(path).parts[:-1]):
            findings.append({"kind": "generated_output", "path": path, "message": "generated or dependency output is staged"})

        content = staged_blob(root, path)
        if len(content) > large_limit:
            findings.append({
                "kind": "large_file", "path": path,
                "message": f"staged blob is {len(content)} bytes; limit is {large_limit}",
            })
        if len(content) <= 1024 * 1024 and any(pattern.search(content) for pattern in SECRET_PATTERNS):
            findings.append({"kind": "secret_content", "path": path, "message": "high-confidence secret material detected"})
    return paths, findings


def run_validation(root: Path, commands: list[str]) -> list[dict]:
    results: list[dict] = []
    for command in commands:
        started = time.perf_counter()
        completed = subprocess.run(command, cwd=root, shell=True, capture_output=True, text=True)
        duration_ms = round((time.perf_counter() - started) * 1000)
        output = (completed.stdout or "") + (completed.stderr or "")
        results.append({
            "command": command,
            "returncode": completed.returncode,
            "duration_ms": duration_ms,
            "output_redacted": bool(output),
        })
        if completed.returncode != 0:
            break
    return results


def main() -> int:
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--run-validation", action="store_true")
    parser.add_argument("--allow-contract-change", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        contract = load_contract(root, args.config)
        paths, findings = scan_staged(root, contract.config, args.allow_contract_change)
        for path in dirty_contract_files(root):
            findings.append({
                "kind": "contract_dirty",
                "path": path,
                "message": "repository contract has unstaged changes; stage and review it or restore it",
            })
        diff_check = run_git(root, "diff", "--cached", "--check", check=False)
        if diff_check.returncode:
            findings.append({
                "kind": "diff_check", "path": None,
                "message": diff_check.stdout.decode("utf-8", errors="replace").strip(),
            })
        commands: list[str] = []
        validation: list[dict] = []
        validation_contract: dict = {}
        if args.run_validation and not findings:
            plan = validation_plan(contract, paths)
            commands = [entry["command"] for entry in plan["commands"]]
            fingerprint = validation_fingerprint(plan)
            trusted = approved_validation_fingerprint(root) == fingerprint
            validation_contract = {
                "commands": plan["commands"],
                "allow_empty": plan["allow_empty"],
                "unmatched_paths": plan["unmatched_paths"],
                "fingerprint": fingerprint,
                "trusted": (not commands and plan["allow_empty"]) or trusted,
            }
            if plan["unmatched_paths"] and not plan["allow_empty"]:
                findings.append({
                    "kind": "validation_missing", "path": None,
                    "message": "no validation command matched changed paths: " + ", ".join(plan["unmatched_paths"]),
                })
            elif not commands and not plan["allow_empty"]:
                findings.append({
                    "kind": "validation_missing", "path": None,
                    "message": "no validation commands were found; run repo-doctor.py for path-by-path details",
                })
            elif commands and not trusted:
                findings.append({
                    "kind": "validation_untrusted", "path": None,
                    "message": "validation commands are not approved in this clone; review repo-doctor.py output and approve the exact command set",
                })
            elif commands:
                validation = run_validation(root, commands)
        failed = next((item for item in validation if item["returncode"] != 0), None)
        if failed:
            findings.append({
                "kind": "validation_failed", "path": None,
                "message": f"command failed: {failed['command']}",
            })
        report = {
            "staged_paths": paths,
            "findings": findings,
            "validation": validation,
            "validation_contract": validation_contract,
            "blocking": bool(findings),
        }
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        report = {"staged_paths": [], "findings": [{"kind": "gate_error", "path": None, "message": str(error)}], "validation": [], "validation_contract": {}, "blocking": True}

    report["timing"] = {
        "validation_ms": sum(item.get("duration_ms", 0) for item in report["validation"]),
        "total_ms": round((time.perf_counter() - started) * 1000),
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for finding in report["findings"]:
            location = f" {finding['path']}" if finding.get("path") else ""
            print(f"BLOCK {finding['kind']}:{location} — {finding['message']}")
        for result in report["validation"]:
            output_state = "validation output redacted" if result["output_redacted"] else "no validation output"
            print(f"{'PASS' if result['returncode'] == 0 else 'FAIL'} {result['command']} [{output_state}]")
        if not report["blocking"]:
            print(f"PASS: {len(report['staged_paths'])} staged path(s) are safe")
    return 1 if report["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
