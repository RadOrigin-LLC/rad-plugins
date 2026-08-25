#!/usr/bin/env python3
"""Explain the RAD Repo contract, local command trust, and packaged resources."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from repo_contract import (
    approve_validation_fingerprint,
    approved_validation_fingerprint,
    load_contract,
    validation_fingerprint,
    validation_plan,
)

DOC_MODEL_VERSION = "1"
VERSION_RE = re.compile(r"rad-repo-doc-model:\s*([0-9]+)")
REQUIRED_RESOURCES = (
    "references/shelf-spec.md",
    "scripts/code-hotspots.py",
    "scripts/memory-recall.py",
    "scripts/pre_ship.py",
    "scripts/repo-snapshot.py",
    "scripts/repo-doctor.py",
    "scripts/repo_contract.py",
    "templates/AGENTS.md",
    "templates/doc-model-block.md",
    "templates/handoff.md",
    "skills/adopt/SKILL.md",
    "skills/repo-align/SKILL.md",
    "skills/repo-init/SKILL.md",
    "skills/startup/SKILL.md",
    "skills/wrapup/SKILL.md",
    "skills/ship/SKILL.md",
    "skills/doctor/SKILL.md",
    "skills/complexity-audit/SKILL.md",
    "skills/recall/SKILL.md",
)


def git_paths(root: Path) -> list[str]:
    for args in (
        ("diff", "--cached", "--name-only", "--diff-filter=ACMR"),
        ("diff", "--name-only", "--diff-filter=ACMR"),
    ):
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True
        )
        paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if paths:
            return paths
    return ["."]


def doc_model_state(root: Path) -> dict:
    path = root / "AGENTS.md"
    if not path.is_file():
        return {"status": "missing", "expected": DOC_MODEL_VERSION, "found": None}
    match = VERSION_RE.search(path.read_text(encoding="utf-8", errors="replace"))
    found = match.group(1) if match else None
    status = "current" if found == DOC_MODEL_VERSION else "legacy"
    return {"status": status, "expected": DOC_MODEL_VERSION, "found": found}


def resource_state() -> dict:
    plugin_root = Path(__file__).resolve().parent.parent
    missing = [relative for relative in REQUIRED_RESOURCES if not (plugin_root / relative).is_file()]
    return {"plugin_root": str(plugin_root), "missing": missing, "ok": not missing}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        contract = load_contract(root, args.config)
        paths = args.paths or git_paths(root)
        plan = validation_plan(contract, paths)
        fingerprint = validation_fingerprint(plan)
        missing_validation = (
            not plan["allow_empty"]
            and (not plan["commands"] or bool(plan["unmatched_paths"]))
        )
        if args.approve:
            if missing_validation:
                raise ValueError("no validation commands were found and allow_empty is false")
            if plan["commands"]:
                approve_validation_fingerprint(root, fingerprint)
        approved = approved_validation_fingerprint(root)
        trusted = (
            not plan["commands"] and plan["allow_empty"]
        ) or (
            bool(plan["commands"]) and approved == fingerprint
        )
        resources = resource_state()
        report = {
            "root": str(root),
            "paths": paths,
            "profile": plan["profile"],
            "instruction_map": plan["instruction_map"],
            "commands": plan["commands"],
            "allow_empty": plan["allow_empty"],
            "unmatched_paths": plan["unmatched_paths"],
            "validation_missing": missing_validation,
            "validation_fingerprint": fingerprint,
            "validation_trusted": trusted,
            "approval_required": bool(plan["commands"]) and not trusted,
            "doc_model": doc_model_state(root),
            "resources": resources,
            "ready": resources["ok"] and not missing_validation and trusted,
        }
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        report = {"root": str(root), "error": str(error), "ready": False}

    if args.json:
        print(json.dumps(report, indent=2))
    elif "error" in report:
        print(f"ERROR: {report['error']}")
    else:
        print(f"Profile: {report['profile']}")
        for entry in report["commands"]:
            print(f"Validate: {entry['command']} [{entry['source']}]")
        if report["unmatched_paths"]:
            print(f"BLOCK: unmatched changed paths: {', '.join(report['unmatched_paths'])}")
        elif report["validation_missing"]:
            print("BLOCK: no validation commands were found and allow_empty is false")
        elif report["approval_required"]:
            print("APPROVAL NEEDED: review the commands, then rerun with --approve")
        else:
            print("Validation trust: ready")
        print(f"Doc model: {report['doc_model']['status']}")
        print(f"Resources: {'ready' if report['resources']['ok'] else 'missing files'}")
    return 0 if report.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
