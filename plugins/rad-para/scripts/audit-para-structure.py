#!/usr/bin/env python3
"""Audit one explicitly supplied PARA root without following links.

The scanner accepts plain and numbered category names.  It recognizes
``Archive`` and ``Archives`` and treats ``Inbox`` and ``Templates`` as optional
support folders.  It reports read errors instead of treating an incomplete
scan as clean.  Project counts are configurable advice, not health claims.
"""
from __future__ import annotations

import argparse
import json
import re
import stat
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


CANONICAL_FOLDERS = ("Projects", "Areas", "Resources", "Archive")
CANONICAL_KEYS = ("projects", "areas", "resources", "archive")
OPTIONAL_FOLDERS = ("Inbox", "Templates")
OPTIONAL_KEYS = ("inbox", "templates")
DEFAULT_PROJECT_MIN = 10
DEFAULT_PROJECT_MAX = 15

ANTI_PARA_FOLDERS = frozenset(
    {
        "inbox",
        "todo",
        "notes",
        "documents",
        "downloads",
        "misc",
        "general",
        "stuff",
        "random",
        "untitled",
        "new folder",
    }
)

PROJECT_VERB_PREFIXES = (
    "build",
    "ship",
    "launch",
    "write",
    "publish",
    "deliver",
    "create",
    "design",
    "implement",
    "migrate",
    "rewrite",
    "refactor",
    "research",
    "investigate",
    "decide",
    "choose",
    "evaluate",
    "plan",
    "draft",
    "produce",
    "record",
    "organize",
    "complete",
    "finish",
    "fix",
    "audit",
    "review",
    "prepare",
    "buy",
    "sell",
    "move",
    "renovate",
)
TOPIC_WORDS = frozenset(
    {
        "ideas",
        "thoughts",
        "notes",
        "stuff",
        "thinking",
        "general",
        "miscellaneous",
        "misc",
        "untitled",
        "topics",
        "things",
    }
)
DATE_HINT = re.compile(
    r"(?:20\d{2}|q[1-4]|h[12]|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
    re.IGNORECASE,
)
NUMBER_PREFIX = re.compile(r"^\s*\d+\s*(?:[-_.]\s*|\s+)?")


@dataclass
class Finding:
    severity: str
    category: str
    code: str
    path: str
    message: str
    fix: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def is_hidden(name: str) -> bool:
    return name.startswith(".") or name in {"$RECYCLE.BIN", "System Volume Information"}


def normalize_folder_name(name: str) -> str:
    """Normalize a plain or numbered category name for case-insensitive matching."""
    value = NUMBER_PREFIX.sub("", name).strip().casefold()
    return value


def category_key(name: str) -> str | None:
    value = normalize_folder_name(name)
    if value == "archives":
        return "archive"
    if value in CANONICAL_KEYS or value in OPTIONAL_KEYS:
        return value
    return None


def _inside(root: Path, value: Path) -> bool:
    return value.resolve(strict=False).is_relative_to(root.resolve(strict=True))


def _issue(issues: list[dict[str, str]], kind: str, path: Path, error: str) -> None:
    issues.append({"kind": kind, "path": str(path), "error": error})


def list_visible(
    directory: Path,
    issues: list[dict[str, str]] | None = None,
    approved_root: Path | None = None,
) -> tuple[list[Path], list[Path]]:
    """List direct children, skipping hidden entries and all link traversal.

    ``issues`` receives incomplete-read and skipped-link records.  The return
    shape stays compatible with the earlier scanner.
    """
    issues = issues if issues is not None else []
    dirs: list[Path] = []
    files: list[Path] = []
    try:
        entries: Iterable[Path] = directory.iterdir()
        for entry in entries:
            if is_hidden(entry.name):
                continue
            if approved_root is not None:
                try:
                    inside = _inside(approved_root, entry)
                except (OSError, RuntimeError, ValueError) as exc:
                    _issue(issues, "incomplete_read", entry, f"cannot determine root boundary: {exc}")
                    continue
                if not inside:
                    _issue(issues, "outside_root", entry, "entry resolved outside the approved root")
                    continue
            try:
                if entry.is_symlink():
                    _issue(issues, "skipped_link", entry, "link was not followed")
                    continue
                entry_mode = entry.lstat().st_mode
                if stat.S_ISDIR(entry_mode):
                    dirs.append(entry)
                elif stat.S_ISREG(entry_mode):
                    files.append(entry)
            except OSError as exc:
                _issue(issues, "incomplete_read", entry, str(exc))
    except OSError as exc:
        _issue(issues, "incomplete_read", directory, str(exc))
    return sorted(dirs, key=lambda item: item.name.casefold()), sorted(
        files, key=lambda item: item.name.casefold()
    )


def looks_like_project_name(name: str) -> bool:
    lower = name.casefold().strip()
    lower_clean = re.sub(r"^\d{4}[-_]?(?:\d{2}[-_]?)?(?:\d{2}[-_]?)?", "", lower)
    first_word = re.split(r"[\s_\-]", lower_clean.lstrip("-_ "))[0]
    if first_word in TOPIC_WORDS:
        return False
    if first_word in PROJECT_VERB_PREFIXES:
        return True
    if DATE_HINT.search(name):
        return True
    if " " not in name and "_" not in name and "-" not in name and len(name.split()) <= 1:
        return False
    return True


def project_has_outcome_marker(project_dir: Path, issues: list[dict[str, str]] | None = None) -> bool:
    """Check only direct files, without traversing child links."""
    _, files = list_visible(project_dir, issues)
    marker_names = {
        "readme",
        "charter",
        "plan",
        "definition",
        "scope",
        "outcome",
        "dod",
        "_index",
        "00-readme",
        "0-readme",
        "deliverable",
        "criteria",
    }
    for file in files:
        name = file.stem.casefold()
        if name in marker_names or name.endswith(("plan", "outcome", "scope")):
            return True
    return False


def _project_advice(count: int, minimum: int, maximum: int) -> dict[str, object]:
    if count < minimum:
        status = "below"
    elif count > maximum:
        status = "above"
    else:
        status = "within"
    return {
        "minimum": minimum,
        "maximum": maximum,
        "status": status,
        "advisory": True,
    }


def _record_read_issues(findings: list[Finding], issues: list[dict[str, str]]) -> None:
    for issue in issues:
        if issue["kind"] == "incomplete_read":
            findings.append(
                Finding(
                    "warning",
                    "read",
                    "incomplete_read",
                    issue["path"],
                    f"The scan could not fully read '{issue['path']}': {issue['error']}",
                    "Check permissions and run the scan again before treating the report as complete.",
                )
            )
        elif issue["kind"] == "skipped_link":
            findings.append(
                Finding(
                    "info",
                    "read",
                    "skipped_link",
                    issue["path"],
                    "A link was skipped, so the scan did not traverse outside the approved root.",
                )
            )
        elif issue["kind"] == "outside_root":
            findings.append(
                Finding(
                    "warning",
                    "read",
                    "outside_root",
                    issue["path"],
                    "An entry resolved outside the approved root and was excluded.",
                )
            )


def audit(
    root: Path,
    strict: bool = False,
    findings: list[Finding] | None = None,
    project_min: int = DEFAULT_PROJECT_MIN,
    project_max: int = DEFAULT_PROJECT_MAX,
) -> dict[str, object]:
    """Audit the supplied root and return a summary plus diagnostics."""
    if findings is None:
        findings = []
    if project_min < 0 or project_max < project_min:
        raise ValueError("project count guidance requires 0 <= project_min <= project_max")
    input_root = root
    if input_root.is_symlink():
        raise ValueError(f"approved root must be a real directory: {input_root}")
    try:
        root = input_root.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"cannot read root {root}: {exc}") from exc
    if not root.is_dir():
        raise ValueError(f"approved root must be a real directory: {root}")

    issues: list[dict[str, str]] = []
    top_dirs, top_files = list_visible(root, issues, root)
    categories: dict[str, Path] = {}
    category_names: dict[str, str] = {}
    optional: dict[str, Path] = {}
    extras: list[Path] = []
    duplicates: list[Path] = []
    for directory in top_dirs:
        key = category_key(directory.name)
        if key in CANONICAL_KEYS:
            if key in categories:
                duplicates.append(directory)
            else:
                categories[key] = directory
                category_names[key] = directory.name
        elif key in OPTIONAL_KEYS:
            if key in optional:
                duplicates.append(directory)
            else:
                optional[key] = directory
        else:
            extras.append(directory)

    missing = [key for key in CANONICAL_KEYS if key not in categories]
    for key in missing:
        display = "Archives" if key == "archive" else key.title()
        findings.append(
            Finding(
                "critical",
                "structure",
                f"missing_canonical_folder:{key}",
                str(root / display),
                f"PARA category '{display}' is missing.",
                f"Create or document the category under the approved root: {display}.",
            )
        )
    for directory in extras:
        key = normalize_folder_name(directory.name)
        findings.append(
            Finding(
                "warning",
                "structure",
                f"extra_top_level_folder:{key}",
                str(directory),
                f"Top-level folder '{directory.name}' is outside the documented PARA categories.",
                "Keep only the four categories and documented optional Inbox or Templates folders at this level.",
            )
        )
    for directory in duplicates:
        findings.append(
            Finding(
                "warning",
                "structure",
                "duplicate_category",
                str(directory),
                f"'{directory.name}' duplicates a PARA category already present at the root.",
                "Choose one folder name for each category before moving files.",
            )
        )
    for file in top_files:
        findings.append(
            Finding(
                "warning",
                "structure",
                "orphan_root_file",
                str(file),
                f"File '{file.name}' sits at the root outside a PARA category.",
                "Classify it into Projects, Areas, Resources, or Archive before moving it.",
            )
        )

    projects_dir = categories.get("projects")
    active_project_count = 0
    if projects_dir is not None:
        project_subdirs, _ = list_visible(projects_dir, issues, root)
        active_project_count = len(project_subdirs)
        for project in project_subdirs:
            if not looks_like_project_name(project.name):
                findings.append(
                    Finding(
                        "warning",
                        "false_project",
                        "topic_shaped_name",
                        str(project),
                        f"'{project.name}' reads as a topic rather than a time-bound project.",
                        "Confirm its outcome, or classify it as an Area or Resource.",
                    )
                )
            if strict and not project_has_outcome_marker(project, issues):
                findings.append(
                    Finding(
                        "info",
                        "false_project",
                        "no_outcome_marker",
                        str(project),
                        f"'{project.name}' has no direct outcome or plan marker file.",
                        "Add a short plan or outcome note if the project needs one.",
                    )
                )

    advice = _project_advice(active_project_count, project_min, project_max)
    if active_project_count < project_min or active_project_count > project_max:
        findings.append(
            Finding(
                "info",
                "count",
                "project_count_advice",
                str(projects_dir or root / "Projects"),
                f"{active_project_count} active projects; configured guidance is {project_min}-{project_max}. This is advice only.",
                "Review project status and choose the next action from current work.",
            )
        )

    _record_read_issues(findings, issues)
    present = [key for key in CANONICAL_KEYS if key in categories]
    return {
        "top_dirs": [directory.name for directory in top_dirs],
        "top_files": [file.name for file in top_files],
        "canonical_present": present,
        "canonical_missing": missing,
        "extra_top_level": [directory.name for directory in extras],
        "duplicate_categories": [directory.name for directory in duplicates],
        "optional_present": [key for key in OPTIONAL_KEYS if key in optional],
        "category_names": category_names,
        "active_project_count": active_project_count,
        "project_count_advice": advice,
        "incomplete_reads": [issue for issue in issues if issue["kind"] == "incomplete_read"],
        "skipped_links": [issue for issue in issues if issue["kind"] == "skipped_link"],
    }


def render_text(summary: dict[str, object], findings: list[Finding]) -> str:
    output = ["audit-para-structure", ""]
    output.append(f"Top-level folders: {summary['top_dirs']}")
    output.append(f"Top-level files:   {summary['top_files']}")
    output.append(f"PARA present:      {summary['canonical_present']}")
    if summary["canonical_missing"]:
        output.append(f"PARA missing:      {summary['canonical_missing']}")
    if summary["extra_top_level"]:
        output.append(f"Non-canonical:     {summary['extra_top_level']}")
    output.append(f"Active projects:   {summary['active_project_count']}")
    advice = summary["project_count_advice"]
    output.append(f"Project advice:    {advice['minimum']}-{advice['maximum']} ({advice['status']})")
    output.append("")
    if not findings:
        output.append("PASS - PARA structure was read completely.")
        return "\n".join(output)
    by_severity = {"critical": [], "warning": [], "info": []}
    for finding in findings:
        by_severity.setdefault(finding.severity, []).append(finding)
    for severity in ("critical", "warning", "info"):
        items = by_severity.get(severity, [])
        if not items:
            continue
        output.append(f"[{severity.upper()}] {len(items)} finding{'s' if len(items) != 1 else ''}")
        for finding in items:
            output.append(f"  {finding.code}  {finding.path}")
            output.append(f"    {finding.message}")
            if finding.fix:
                output.append(f"    fix: {finding.fix}")
        output.append("")
    return "\n".join(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true", help="check for direct outcome marker files")
    parser.add_argument("--json", action="store_true", help="emit one JSON object")
    parser.add_argument(
        "--project-min",
        "--min-projects",
        "--project-count-min",
        dest="project_min",
        type=int,
        default=DEFAULT_PROJECT_MIN,
        help="lower bound for advisory project-count guidance",
    )
    parser.add_argument(
        "--project-max",
        "--max-projects",
        "--project-count-max",
        dest="project_max",
        type=int,
        default=DEFAULT_PROJECT_MAX,
        help="upper bound for advisory project-count guidance",
    )
    args = parser.parse_args(argv)
    try:
        root = Path(args.root)
        findings: list[Finding] = []
        summary = audit(root, args.strict, findings, args.project_min, args.project_max)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(
            json.dumps(
                {
                    "validator": "audit-para-structure",
                    "version": "1.1.0",
                    "root": str(Path(args.root).resolve()),
                    "strict": args.strict,
                    "summary": summary,
                    "findings": [finding.to_dict() for finding in findings],
                },
                indent=2,
            )
        )
    else:
        print(render_text(summary, findings))
    return 1 if any(finding.severity in {"critical", "warning"} for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
