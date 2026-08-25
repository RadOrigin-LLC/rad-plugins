#!/usr/bin/env python3
"""
repo-scan.py — mechanical drift signals consumed by rad-repo's repo-align.

High-precision, mechanical signals only — so the loose-ends count is trustworthy and
never cries wolf. Fuzzy checks (contradiction, redundancy) have their own scripts.

Signals (each a "loose end"):
  1. Active-set growth — AGENTS.md's declared cold-start read path (legacy repos)
     lists more than the 4 core docs.
  2. Floating docs — a .md at the repo root or directly under docs/ that isn't on the
     shelf (see references/shelf-spec.md). Transient brainstorm specs
     (docs/*-spec.md / *-design.md) count: they're supposed to be archived once
     planning consumes them. (Scoped narrowly on purpose: .md inside source trees,
     packages, etc. is NOT considered — component READMEs must never false-flag.)
  3. Legacy inbox items — docs/inbox/*.md (a retired tier; flagged so contents get filed out).
  4. Size budgets — AGENTS.md (L0) past 40 lines; docs/handoff.md (L1) past 60 lines.
  5. Initiative lifecycle — docs/initiatives/*.md must declare ownership, status,
     baseline, plan linkage, retirement, archive routing, acceptance, and rollback.

The report also includes an instruction map containing root and scoped AGENTS.md
files. Root size budgets do not apply to scoped overlays.

Severity: 0 -> green, 1-4 -> yellow, >=5 -> red.

Nudge cooldown: the optional "run repo-align" suggestion (red only, standalone runs
only) is rate-limited via a small state file (.rad/repo-manager-state.json) so it
can't nag. repo-align itself calls with --no-record, so it never writes state.

Usage:
  python3 repo-scan.py <project-dir>
  python3 repo-scan.py <project-dir> --json
  python3 repo-scan.py <project-dir> --json --no-record   # don't update nudge state

Output: human text by default; --json emits a single object. Exit 0 always (advisory).
No third-party dependencies. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CORE_DOCS = ("docs/prd.md", "docs/plan.md", "docs/handoff.md")

# Root-level .md files that are normal project furniture — never "floating".
ALLOWED_ROOT = {
    "AGENTS.md", "README.md", "LICENSE.md",
    "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "CHANGELOG.md",
}

# The shelf (references/shelf-spec.md): docs sanctioned directly under docs/ —
# allowed, never "floating". Anything else under docs/ is a routing candidate.
ALLOWED_DOCS = {
    "prd.md", "plan.md", "handoff.md",
    "decisions.md", "ideas.md", "lessons.md",
    "design.md", "architecture.md", "api.md", "README.md",
}

# Size budgets from the shelf spec: L0 (AGENTS.md) and L1 (docs/handoff.md).
L0_LINE_BUDGET = 40
L1_LINE_BUDGET = 60
SEVERITY_YELLOW = 1
SEVERITY_RED = 5
NUDGE_COOLDOWN_SCANS = 3

IGNORED_INSTRUCTION_DIRS = {
    ".git", ".hg", ".svn", ".next", ".venv", ".worktrees", "build",
    "coverage", "dist", "fixtures", "node_modules", "target", "templates", "vendor",
}
INITIATIVE_FIELDS = {
    "title", "owner", "status", "baseline", "linked_plan", "retire_when", "archive_to",
}
INITIATIVE_HEADINGS = {"acceptance criteria", "rollback strategy"}

READ_PATH_HEADING = re.compile(r"cold-start read path", re.IGNORECASE)
NUMBERED_ITEM = re.compile(r"^\s*\d+\.\s+")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")


def find_floating(root: Path) -> list[str]:
    """Floating = a .md at repo root (not in ALLOWED_ROOT) or directly under docs/
    (not a core doc or a model-sanctioned conditional doc). Deliberately shallow —
    code-adjacent .md is ignored."""
    floating: list[str] = []

    for p in sorted(root.glob("*.md")):
        if p.name not in ALLOWED_ROOT:
            floating.append(p.name)

    docs = root / "docs"
    if docs.is_dir():
        allowed = {Path(c).name for c in CORE_DOCS} | ALLOWED_DOCS
        for p in sorted(docs.glob("*.md")):
            if p.name not in allowed:
                floating.append(f"docs/{p.name}")

    return floating


def count_inbox(root: Path) -> list[str]:
    inbox = root / "docs" / "inbox"
    if not inbox.is_dir():
        return []
    return [f"docs/inbox/{p.name}" for p in sorted(inbox.glob("*.md"))
            if p.name.lower() != "readme.md"]


def declared_active_count(root: Path) -> int | None:
    """Count the numbered entries under AGENTS.md's 'cold-start read path' heading.
    Returns None if AGENTS.md or the section is absent."""
    agents = root / "AGENTS.md"
    if not agents.is_file():
        return None
    lines = agents.read_text(encoding="utf-8", errors="replace").splitlines()
    in_section = False
    count = 0
    for ln in lines:
        if READ_PATH_HEADING.search(ln):
            in_section = True
            continue
        if in_section:
            if NUMBERED_ITEM.match(ln):
                count += 1
            elif ln.strip().startswith("#"):
                break  # next heading ends the section
            elif count > 0 and not ln.strip():
                # blank after the list ends it
                if count >= 1:
                    break
    return count if count else None


def line_count(root: Path, rel: str) -> int | None:
    f = root / rel
    if not f.is_file():
        return None
    return len(f.read_text(encoding="utf-8", errors="replace").splitlines())


def find_instruction_files(root: Path) -> list[str]:
    """Return root and scoped AGENTS.md files, excluding dependencies and output."""
    found: list[str] = []
    for path in root.rglob("AGENTS.md"):
        relative = path.relative_to(root)
        if any(part in IGNORED_INSTRUCTION_DIRS for part in relative.parts[:-1]):
            continue
        found.append(relative.as_posix())
    return sorted(found)


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return {}
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip().lower()] = value.strip().strip('"\'')
    return values


def validate_initiatives(root: Path) -> dict[str, list[str]]:
    initiatives = root / "docs" / "initiatives"
    if not initiatives.is_dir():
        return {}
    findings: dict[str, list[str]] = {}
    for path in sorted(initiatives.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        metadata = parse_frontmatter(text)
        headings = {
            match.group(1).strip().lower()
            for line in text.splitlines()
            if (match := HEADING.match(line))
        }
        missing = [f"field:{field}" for field in sorted(INITIATIVE_FIELDS - metadata.keys())]
        missing.extend(
            f"heading:{heading}" for heading in sorted(INITIATIVE_HEADINGS - headings)
        )
        if missing:
            findings[path.relative_to(root).as_posix()] = missing
    return findings


def load_state(root: Path) -> dict:
    state_file = root / ".rad" / "repo-manager-state.json"
    if state_file.is_file():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(root: Path, state: dict) -> None:
    rad = root / ".rad"
    try:
        rad.mkdir(exist_ok=True)
        (rad / "repo-manager-state.json").write_text(
            json.dumps(state, indent=2), encoding="utf-8"
        )
    except OSError:
        pass  # state is best-effort; never fail the scan over it


def scan(root: Path, record: bool) -> dict:
    floating = find_floating(root)
    inbox = count_inbox(root)
    active = declared_active_count(root)
    agents_lines = line_count(root, "AGENTS.md")
    handoff_lines = line_count(root, "docs/handoff.md")
    instruction_files = find_instruction_files(root)
    initiative_findings = validate_initiatives(root)

    breakdown: dict[str, object] = {}
    loose = 0

    if active is not None and active > 4:
        breakdown["active_set_overflow"] = active - 4
        loose += active - 4
    if floating:
        breakdown["floating"] = floating
        loose += len(floating)
    if inbox:
        breakdown["inbox"] = inbox
        loose += len(inbox)
    if agents_lines is not None and agents_lines > L0_LINE_BUDGET:
        breakdown["l0_over_budget"] = {"lines": agents_lines, "budget": L0_LINE_BUDGET}
        loose += 1
    if handoff_lines is not None and handoff_lines > L1_LINE_BUDGET:
        breakdown["l1_over_budget"] = {"lines": handoff_lines, "budget": L1_LINE_BUDGET}
        loose += 1
    if initiative_findings:
        breakdown["initiative_metadata"] = initiative_findings
        loose += len(initiative_findings)

    if loose == 0:
        severity = "green"
    elif loose < SEVERITY_RED:
        severity = "yellow"
    else:
        severity = "red"

    # Nudge cooldown — only the red repo-align tail is rate-limited.
    state = load_state(root)
    scan_count = int(state.get("scan_count", 0)) + 1
    last_nudge = int(state.get("last_red_nudge_scan", -NUDGE_COOLDOWN_SCANS))
    show_nudge = severity == "red" and (scan_count - last_nudge) >= NUDGE_COOLDOWN_SCANS
    if record:
        state["scan_count"] = scan_count
        if show_nudge:
            state["last_red_nudge_scan"] = scan_count
        save_state(root, state)

    return {
        "loose_ends": loose,
        "severity": severity,
        "show_nudge": show_nudge,
        "breakdown": breakdown,
        "agents_present": agents_lines is not None,
        "instruction_files": instruction_files,
    }


def render_text(report: dict) -> str:
    n = report["loose_ends"]
    sev = report["severity"]
    if sev == "green":
        return "Repo's tidy — nothing loose."
    if sev == "yellow":
        return f"A few loose ends ({n}) — fine for now."
    tail = " — worth a /rad-repo:repo-align to sort it." if report["show_nudge"] else "."
    return f"Getting cluttered ({n}){tail}"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("path", help="Project directory to scan")
    p.add_argument("--json", action="store_true", help="Emit a single JSON object")
    p.add_argument("--no-record", action="store_true", help="Don't update nudge state")
    args = p.parse_args(argv)

    root = Path(args.path)
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    report = scan(root, record=not args.no_record)
    print(json.dumps(report, indent=2) if args.json else render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
