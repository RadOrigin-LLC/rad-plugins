#!/usr/bin/env python3
"""Recall a small set of relevant decisions and lessons from repository Markdown."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ENTRY_RE = re.compile(r"^\s*-\s*(\d{4}-\d{2}-\d{2})\s*·\s*(.*)$")
FIELD_RE = re.compile(r"^\[([^\]:]+)(?::\s*([^\]]+))?\]\s*")
WORD_RE = re.compile(r"[a-z0-9][a-z0-9._/-]*", re.IGNORECASE)
INACTIVE = {"deprecated", "superseded"}
MEMORY_FILES = (
    ("docs/decisions.md", "decision"),
    ("docs/lessons.md", "lesson"),
)


def normalize_words(value: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(value)]


def parse_entry(path: str, line_number: int, kind: str, line: str) -> dict | None:
    match = ENTRY_RE.match(line)
    if not match:
        return None
    recorded, remainder = match.groups()
    fields: dict[str, str | None] = {}
    record_id: str | None = None
    while field := FIELD_RE.match(remainder):
        name, value = field.groups()
        if value is None and record_id is None:
            record_id = name.strip()
        elif value is not None:
            fields[name.strip().lower()] = value.strip()
        remainder = remainder[field.end():]
    stale_after = fields.get("stale-after", "never") or "never"
    stale = stale_after.lower() != "never" and stale_after <= date.today().isoformat()
    return {
        "id": record_id,
        "type": kind,
        "date": recorded,
        "scope": fields.get("scope", "repo") or "repo",
        "status": (fields.get("status", "active") or "active").lower(),
        "source": fields.get("source"),
        "verified": fields.get("verified"),
        "stale_after": stale_after,
        "stale": stale,
        "supersedes": fields.get("supersedes"),
        "text": remainder.strip(),
        "path": path,
        "line": line_number,
        "typed": record_id is not None,
    }


def load_records(root: Path) -> list[dict]:
    records: list[dict] = []
    for relative, kind in MEMORY_FILES:
        path = root / relative
        if not path.is_file():
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            record = parse_entry(relative, number, kind, line)
            if record:
                records.append(record)
    return records


def scope_matches(scope: str, target: str | None) -> bool:
    if not target or scope.lower() in {"repo", "all", "*"}:
        return True
    normalized_scope = scope.replace("\\", "/").strip("/").lower()
    normalized_target = target.replace("\\", "/").strip("/").lower()
    return normalized_target == normalized_scope or normalized_target.startswith(
        normalized_scope + "/"
    )


def score_record(record: dict, query: str, target: str | None) -> int:
    words = normalize_words(query)
    haystack = " ".join(
        str(record.get(key) or "")
        for key in ("id", "type", "scope", "source", "text")
    ).lower()
    matches = sum(1 for word in words if word in haystack)
    if not matches:
        return 0
    score = matches * 10
    if query.lower() in haystack:
        score += 20
    if target and record["scope"].lower() not in {"repo", "all", "*"}:
        score += 5
    if record["typed"]:
        score += 2
    if record["verified"] and record["verified"].lower() != "unverified":
        score += 1
    return score


def recall(
    root: Path,
    query: str,
    target: str | None = None,
    limit: int = 5,
    include_inactive: bool = False,
) -> dict:
    found: list[dict] = []
    for record in load_records(root):
        if not include_inactive and record["status"] in INACTIVE:
            continue
        if not scope_matches(record["scope"], target):
            continue
        score = score_record(record, query, target)
        if score:
            found.append({**record, "score": score})
    found.sort(key=lambda item: (item["score"], item["date"], item["id"] or ""), reverse=True)
    results = found[:limit]
    return {
        "query": query,
        "path_filter": target,
        "count": len(results),
        "results": results,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("query")
    parser.add_argument("--path", dest="target")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--include-inactive", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    report = recall(
        root,
        args.query,
        target=args.target,
        limit=max(1, min(args.limit, 20)),
        include_inactive=args.include_inactive,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for item in report["results"]:
            marker = " STALE" if item["stale"] else ""
            print(f"{item['path']}:{item['line']} [{item['status']}{marker}] {item['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
