#!/usr/bin/env python3
"""Regression tests for the combined startup and ship snapshot."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "repo-snapshot.py"

assert SCRIPT.is_file(), "repo-snapshot.py is missing"


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )


def snapshot(root: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Test")
    (root / "docs").mkdir()
    (root / "AGENTS.md").write_text("# Repo\n", encoding="utf-8")
    (root / ".rad-repo.json").write_text(
        json.dumps({"profile": "core", "validation": {"allow_empty": True}}),
        encoding="utf-8",
    )
    (root / "docs" / "handoff.md").write_text(
        """---
rad_repo_handoff: 2
updated: 2026-08-14
branch: main
head: pending
worktree: clean
active_task: T4
next_action: Add the recall contract.
---
# Handoff

## Next action

Add the recall contract.
""",
        encoding="utf-8",
    )
    (root / "docs" / "plan.md").write_text("# Plan\n", encoding="utf-8")
    (root / "app.py").write_text("print('one')\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-qm", "initial")

    report = snapshot(root)
    assert report["profile"] == "core", report
    assert report["git"]["branch"] == "main" and report["git"]["clean"], report
    assert report["git"]["changed_paths"] == [], report
    assert report["handoff"]["metadata"]["rad_repo_handoff"] == "2", report
    assert report["handoff"]["metadata"]["updated"] == "2026-08-14", report
    assert report["handoff"]["metadata"]["branch"] == "main", report
    assert report["handoff"]["metadata"]["head"] == "pending", report
    assert report["handoff"]["metadata"]["worktree"] == "clean", report
    assert report["handoff"]["metadata"]["active_task"] == "T4", report
    assert report["handoff"]["metadata"]["next_action"] == "Add the recall contract.", report
    assert report["repo_scan"]["severity"] == "green", report
    assert "trust" in report["freshness"], report
    for field in ("repo_scan_ms", "freshness_ms", "total_ms"):
        assert isinstance(report["timing"][field], int), report
        assert report["timing"][field] >= 0, report
    assert report["timing"]["total_ms"] >= report["timing"]["repo_scan_ms"], report
    assert report["timing"]["total_ms"] >= report["timing"]["freshness_ms"], report

    (root / "app.py").write_text("print('two')\n", encoding="utf-8")
    report = snapshot(root)
    assert not report["git"]["clean"], report
    assert report["git"]["changed_paths"] == ["app.py"], report

print("repo-snapshot regression tests passed")
