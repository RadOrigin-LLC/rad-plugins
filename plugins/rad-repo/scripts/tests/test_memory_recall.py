#!/usr/bin/env python3
"""Regression tests for bounded, read-only durable-memory recall."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "memory-recall.py"

assert SCRIPT.is_file(), "memory-recall.py is missing"


def recall(root: Path, query: str, *args: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(root), query, *args, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    docs = root / "docs"
    docs.mkdir()
    (docs / "decisions.md").write_text(
        """# Decisions

- 2026-08-14 · [DEC-20260814-01] [scope: plugins/rad-repo] [status: active] [source: docs/plan.md] [verified: 2026-08-14] [stale-after: never] [supersedes: DEC-20260813-01] Validation commands use path scopes.
- 2026-08-13 · [DEC-20260813-01] [scope: plugins/rad-repo] [status: superseded] [source: chat] [verified: unverified] [stale-after: never] [supersedes: none] Validation commands run globally.
- 2026-06-07 · push to main means push to origin/main
""",
        encoding="utf-8",
    )
    (docs / "lessons.md").write_text(
        """# Lessons

- 2026-08-14 · [LES-20260814-01] [scope: plugins/rad-repo] [status: active] [source: test] [verified: 2026-08-14] [stale-after: never] [supersedes: none] Template AGENTS files are inert and must stay out of instruction discovery.
- 2020-01-01 · [LES-20200101-01] [scope: repo] [status: active] [source: old-test] [verified: 2020-01-01] [stale-after: 2020-02-01] [supersedes: none] Obsolete cache advice.
""",
        encoding="utf-8",
    )
    (docs / "archive").mkdir()
    (docs / "archive" / "old.md").write_text(
        "- 2026-08-14 · validation path scopes\n", encoding="utf-8"
    )
    (root / "README.md").write_text("validation path scopes\n", encoding="utf-8")

    report = recall(root, "validation path scopes", "--path", "plugins/rad-repo")
    assert report["count"] == 1, report
    record = report["results"][0]
    assert record["id"] == "DEC-20260814-01", record
    assert record["scope"] == "plugins/rad-repo", record
    assert record["status"] == "active" and record["verified"] == "2026-08-14", record
    assert not record["stale"], record
    assert record["path"] == "docs/decisions.md" and record["line"] == 3, record

    report = recall(root, "validation", "--include-inactive")
    assert [item["id"] for item in report["results"]] == [
        "DEC-20260814-01", "DEC-20260813-01"
    ], report
    assert all(item["path"] in {"docs/decisions.md", "docs/lessons.md"} for item in report["results"]), report

    report = recall(root, "obsolete cache")
    assert report["results"][0]["stale"], report

    report = recall(root, "validation path scopes", "--path", "plugins/other")
    assert report["count"] == 0, report

print("memory-recall regression tests passed")
