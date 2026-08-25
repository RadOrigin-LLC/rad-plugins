#!/usr/bin/env python3
"""Collect startup and ship evidence in one read-only repository snapshot."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from repo_contract import load_contract, repository_profile


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )


def null_paths(result: subprocess.CompletedProcess[str]) -> list[str]:
    if result.returncode:
        return []
    return [path for path in result.stdout.split("\0") if path]


def git_state(root: Path) -> dict:
    inside = run_git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode or inside.stdout.strip() != "true":
        return {"available": False, "clean": None, "changed_paths": []}
    status = run_git(root, "-c", "core.quotepath=false", "status", "--short")
    branch = run_git(root, "branch", "--show-current")
    head = run_git(root, "rev-parse", "HEAD")
    upstream = run_git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    changed = set(null_paths(run_git(root, "diff", "--name-only", "-z")))
    changed.update(null_paths(run_git(root, "diff", "--cached", "--name-only", "-z")))
    changed.update(null_paths(run_git(root, "ls-files", "--others", "--exclude-standard", "-z")))
    diff_stat = run_git(root, "diff", "--stat", "HEAD") if head.returncode == 0 else status
    log = run_git(root, "log", "-10", "--pretty=format:%h %s")
    return {
        "available": True,
        "branch": branch.stdout.strip() or None,
        "head": head.stdout.strip() if head.returncode == 0 else None,
        "upstream": upstream.stdout.strip() if upstream.returncode == 0 else None,
        "clean": not bool(status.stdout.strip()),
        "status": status.stdout.splitlines(),
        "changed_paths": sorted(changed),
        "diff_stat": diff_stat.stdout.splitlines(),
        "recent_commits": log.stdout.splitlines() if log.returncode == 0 else [],
    }


def run_json_script(root: Path, name: str, *args: str) -> tuple[dict, int]:
    script = Path(__file__).resolve().parent / name
    started = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(script), str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    duration_ms = round((time.perf_counter() - started) * 1000)
    if result.returncode:
        return {"error": (result.stderr or result.stdout).strip(), "exit_code": result.returncode}, duration_ms
    try:
        return json.loads(result.stdout), duration_ms
    except json.JSONDecodeError as error:
        return {"error": f"invalid JSON from {name}: {error}", "exit_code": result.returncode}, duration_ms


def handoff_state(root: Path) -> dict:
    path = root / "docs" / "handoff.md"
    if not path.is_file():
        return {"exists": False, "metadata": {}, "lines": 0}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    metadata: dict[str, str] = {}
    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip("\"'")
    return {"exists": True, "metadata": metadata, "lines": len(lines)}


def snapshot(root: Path) -> dict:
    started = time.perf_counter()
    scan, scan_ms = run_json_script(root, "repo-scan.py", "--json", "--no-record")
    freshness, freshness_ms = run_json_script(root, "doc-freshness.py", "--json")
    contract = load_contract(root)
    report = {
        "root": str(root),
        "profile": repository_profile(contract),
        "git": git_state(root),
        "handoff": handoff_state(root),
        "repo_scan": scan,
        "freshness": freshness,
    }
    report["timing"] = {
        "repo_scan_ms": scan_ms,
        "freshness_ms": freshness_ms,
        "total_ms": round((time.perf_counter() - started) * 1000),
    }
    return report


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    try:
        report = snapshot(root)
    except (OSError, ValueError) as error:
        if args.json:
            print(json.dumps({"root": str(root), "error": str(error)}, indent=2))
        else:
            print(f"ERROR: {error}")
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        state = "clean" if report["git"].get("clean") else "dirty"
        print(f"{report['git'].get('branch') or '(no branch)'} {state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
