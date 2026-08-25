#!/usr/bin/env python3
"""
lint-dockerfile.py — Coolify-specific Dockerfile linter.

Catches file patterns used by the coolify-review skill.

Used by:
  - coolify-review skill
  - Standalone CLI for users who want a quick pre-deploy check

Usage:
  python3 lint-dockerfile.py <path-to-Dockerfile>
  python3 lint-dockerfile.py <project-root>          # finds Dockerfile* recursively
  python3 lint-dockerfile.py <path> --json
  python3 lint-dockerfile.py <path> --strict          # promote SUGGESTION to WARNING

Output:
  Default — text report (severity-grouped)
  --json  — single JSON object for skill consumption

Exit codes:
  0  no issues
  1  issues found (CRITICAL or WARNING)
  2  script error (file not found, parse failure)

Honest framing: this script catches mechanical patterns. It does NOT validate that
the resulting image actually builds, that the application code is correct, or that
the Coolify deployment will succeed. It catches the structural and security issues
that humans (and the LLM reviewer) commonly miss.

Pure stdlib Python 3.8+. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# Pattern recognition for Dockerfile directives
DIRECTIVE_RE = re.compile(r"^\s*([A-Z]+)\s+(.*)$")
COMMENT_RE = re.compile(r"^\s*#")
FROM_RE = re.compile(r"^\s*FROM\s+(\S+)(?:\s+(?:AS|as)\s+(\S+))?", re.IGNORECASE)
USER_RE = re.compile(r"^\s*USER\s+(\S+)", re.IGNORECASE)
EXPOSE_RE = re.compile(r"^\s*EXPOSE\s+(\d+)", re.IGNORECASE)
HEALTHCHECK_RE = re.compile(r"^\s*HEALTHCHECK\s+", re.IGNORECASE)
ARG_RE = re.compile(r"^\s*ARG\s+([A-Z_][A-Z0-9_]*)", re.IGNORECASE)
ENV_RE = re.compile(r"^\s*ENV\s+([A-Z_][A-Z0-9_]*)\s*[=\s]\s*(.*)", re.IGNORECASE)
COPY_ALL_RE = re.compile(r"^\s*COPY\s+(\.|\.\s+\S+)\s+", re.IGNORECASE)

SECRET_LIKE_NAMES = re.compile(
    r"(?:^|_)(SECRET|TOKEN|KEY|PASSWORD|PASSWD|PWD|API[-_]?KEY|ACCESS[-_]?KEY|PRIVATE[-_]?KEY|"
    r"AUTH|CREDENTIAL|DATABASE_URL)(?:_|$)",
    re.IGNORECASE,
)
SECRET_LIKE_VALUE = re.compile(
    r"\b(?:sk_live_|sk_test_|pk_live_|gh[ousp]_|ghp_|xoxb-|xoxp-|AIza[0-9A-Za-z_-]{35}|"
    r"AKIA[0-9A-Z]{16}|[A-Za-z0-9+/]{40,})",
    re.IGNORECASE,
)

@dataclass
class Finding:
    severity: str  # CRITICAL | WARNING | SUGGESTION
    category: str
    line: int
    message: str
    fix: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def parse_dockerfile(text: str) -> tuple[list[tuple[int, str, str]], list[str]]:
    """Return (directives, raw_lines) where directives is [(line_no, name, args), ...]."""
    raw_lines = text.splitlines()
    directives: list[tuple[int, str, str]] = []
    # Handle line continuations
    accumulated = ""
    accumulated_start = 0
    for lineno, line in enumerate(raw_lines, start=1):
        stripped = line.rstrip()
        if not stripped or COMMENT_RE.match(stripped):
            continue
        if accumulated:
            accumulated += " " + stripped.lstrip()
        else:
            accumulated = stripped
            accumulated_start = lineno
        if accumulated.endswith("\\"):
            accumulated = accumulated[:-1].rstrip()
            continue
        match = DIRECTIVE_RE.match(accumulated)
        if match:
            directives.append((accumulated_start, match.group(1).upper(), match.group(2)))
        accumulated = ""
    return directives, raw_lines


def lint(text: str, strict: bool) -> list[Finding]:
    findings: list[Finding] = []
    directives, raw_lines = parse_dockerfile(text)
    if not directives:
        findings.append(Finding(
            severity="WARNING", category="structure", line=1,
            message="No directives parsed — file empty or only comments",
            fix="Verify the file is a valid Dockerfile",
        ))
        return findings

    from_lines: list[tuple[int, str, str | None]] = []  # (line, base, alias)
    user_directives: list[tuple[int, str]] = []
    expose_directives: list[tuple[int, str]] = []
    has_healthcheck = False
    arg_names: list[tuple[int, str]] = []
    env_pairs: list[tuple[int, str, str]] = []
    copy_all_lines: list[int] = []

    for lineno, name, args in directives:
        if name == "FROM":
            m = FROM_RE.match(f"FROM {args}")
            if m:
                from_lines.append((lineno, m.group(1), m.group(2)))
        elif name == "USER":
            m = USER_RE.match(f"USER {args}")
            if m:
                user_directives.append((lineno, m.group(1)))
        elif name == "EXPOSE":
            m = EXPOSE_RE.match(f"EXPOSE {args}")
            if m:
                expose_directives.append((lineno, m.group(1)))
        elif name == "HEALTHCHECK":
            has_healthcheck = True
        elif name == "ARG":
            m = ARG_RE.match(f"ARG {args}")
            if m:
                arg_names.append((lineno, m.group(1)))
        elif name == "ENV":
            m = ENV_RE.match(f"ENV {args}")
            if m:
                env_pairs.append((lineno, m.group(1), m.group(2)))
        elif name == "COPY":
            if COPY_ALL_RE.match(f"COPY {args}"):
                copy_all_lines.append(lineno)

    # ---------- Checks ----------

    # FROM: image pinning
    for lineno, base, alias in from_lines:
        if ":" not in base or base.endswith(":latest"):
            findings.append(Finding(
                severity="WARNING", category="reproducibility", line=lineno,
                message=f"Base image '{base}' is not pinned to a specific tag (uses 'latest' or no tag)",
                fix=f"Pin to a specific version: '{base.split(':')[0]}:24-alpine' or similar. "
                    "Floating tags break reproducibility and silently change builds.",
            ))
        elif "@sha256:" not in base and base.endswith(("-alpine", "-slim")) is False:
            # Soft suggestion — not all images need digest pinning
            if strict:
                findings.append(Finding(
                    severity="SUGGESTION", category="reproducibility", line=lineno,
                    message=f"Base image '{base}' uses a tag but no digest",
                    fix="For maximum reproducibility, pin to digest: 'image:tag@sha256:...'",
                ))

    # Multi-stage build detection
    if len(from_lines) == 1 and any(name in ("RUN",) for _, name, _ in directives):
        # Single-stage with RUN — likely candidate for multi-stage
        findings.append(Finding(
            severity="SUGGESTION", category="size", line=from_lines[0][0],
            message="Single-stage build — final image likely contains build tools and intermediate files",
            fix="Consider multi-stage build: 'FROM image AS builder' for build, then 'FROM minimal-image' "
                "and COPY artifacts from builder. Reduces image size dramatically.",
        ))

    # USER directive (non-root)
    if not user_directives:
        findings.append(Finding(
            severity="CRITICAL" if strict else "WARNING",
            category="security", line=from_lines[-1][0] if from_lines else 1,
            message="No USER directive — container will run as root",
            fix="Add 'USER node' / 'USER nobody' / 'USER 1001:1001' (or create a dedicated user) "
                "before CMD/ENTRYPOINT. Required by most security baselines.",
        ))
    else:
        last_user = user_directives[-1]
        if last_user[1] in ("root", "0", "0:0"):
            findings.append(Finding(
                severity="CRITICAL", category="security", line=last_user[0],
                message=f"Final USER directive sets '{last_user[1]}' — container runs as root",
                fix="Switch to a non-root user before CMD/ENTRYPOINT.",
            ))

    # EXPOSE directive (Coolify needs this for port detection)
    if not expose_directives:
        findings.append(Finding(
            severity="WARNING", category="coolify-compatibility", line=1,
            message="No EXPOSE directive — Coolify auto-detects the port from EXPOSE; without it, "
                    "you must configure 'Ports Exposes' manually in Coolify UI",
            fix="Add 'EXPOSE 3000' (or your port) so Coolify auto-routes traffic.",
        ))

    # HEALTHCHECK directive
    if not has_healthcheck:
        findings.append(Finding(
            severity="WARNING", category="coolify-compatibility", line=1,
            message="No HEALTHCHECK directive — Coolify rolling updates depend on this for "
                    "zero-downtime deployments. Without it, Coolify can't verify the new container is healthy.",
            fix="Add 'HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:PORT/healthz || exit 1'. "
                "Pair with a /healthz endpoint that checks dependencies (DB, cache).",
        ))

    # ARG / build-arg secret detection
    for lineno, arg_name in arg_names:
        if SECRET_LIKE_NAMES.search(arg_name):
            findings.append(Finding(
                severity="CRITICAL", category="security", line=lineno,
                message=f"ARG '{arg_name}' looks secret-shaped — build args bake into image layers and "
                        "are visible to anyone with image access",
                fix=f"Use Docker BuildKit secrets instead: 'RUN --mount=type=secret,id={arg_name.lower()} ...'. "
                    "Or pass via runtime ENV (Coolify env vars, NOT build args).",
            ))

    # ENV with secret-like value
    for lineno, env_name, env_value in env_pairs:
        if SECRET_LIKE_NAMES.search(env_name) and env_value and "${" not in env_value and "$(" not in env_value:
            # Might be a literal secret
            stripped_value = env_value.strip().strip('"').strip("'")
            if stripped_value and stripped_value not in ("placeholder", "change-me", "TODO", "REPLACE_ME"):
                findings.append(Finding(
                    severity="CRITICAL", category="security", line=lineno,
                    message=f"ENV '{env_name}' may be a hardcoded secret baked into image",
                    fix=f"Don't set secrets via ENV in Dockerfile. Set them via Coolify UI environment variables "
                        "(scoped Build / Runtime separately).",
                ))
        elif SECRET_LIKE_VALUE.search(env_value):
            findings.append(Finding(
                severity="CRITICAL", category="security", line=lineno,
                message=f"ENV '{env_name}' contains a secret-shaped value",
                fix="Move to runtime env via Coolify UI; never commit secrets in Dockerfile.",
            ))

    # COPY . . without .dockerignore
    if copy_all_lines:
        # We can't check for .dockerignore from the Dockerfile alone; only flag if user runs at project root
        for lineno in copy_all_lines:
            findings.append(Finding(
                severity="SUGGESTION", category="size",  line=lineno,
                message=f"COPY . copies entire build context — make sure .dockerignore excludes "
                        "node_modules, .git, .env, dist, build, *.log, test directories",
                fix="Create/verify .dockerignore in project root with at minimum: "
                    "node_modules/, .git/, .env, .env.*, dist/, build/, *.log, coverage/, .vscode/, .idea/",
            ))

    return findings


def render_text(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"lint-dockerfile: {report['file']}")
    findings = report["findings"]
    if not findings:
        lines.append("OK — no issues.")
        return "\n".join(lines)

    by_severity: dict[str, list[dict]] = {}
    for f in findings:
        by_severity.setdefault(f["severity"], []).append(f)

    lines.append("")
    lines.append(
        f"Issues: {len(findings)} total — "
        + ", ".join(f"{sev}: {len(by_severity[sev])}" for sev in ("CRITICAL", "WARNING", "SUGGESTION") if sev in by_severity)
    )
    for sev in ("CRITICAL", "WARNING", "SUGGESTION"):
        for f in by_severity.get(sev, []):
            lines.append(f"  {sev:11} L{f['line']:<4} ({f['category']}) {f['message']}")
            if f["fix"]:
                lines.append(f"      fix: {f['fix']}")
    return "\n".join(lines)


def find_dockerfiles(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        results: list[Path] = []
        for pattern in ("Dockerfile", "Dockerfile.*", "*.dockerfile"):
            results.extend(target.rglob(pattern))
        # Filter out node_modules, .git, etc.
        return [p for p in results if not any(part in {"node_modules", ".git", "vendor"} for part in p.parts)]
    return []


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("path", help="Path to a Dockerfile or directory containing Dockerfiles")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    p.add_argument("--strict", action="store_true", help="Promote SUGGESTION to WARNING")
    args = p.parse_args(argv)

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"error: not found: {target}", file=sys.stderr)
        return 2

    dockerfiles = find_dockerfiles(target)
    if not dockerfiles:
        print(f"error: no Dockerfile(s) found at {target}", file=sys.stderr)
        return 2

    all_reports: list[dict] = []
    any_blocking = False
    for df in dockerfiles:
        text = df.read_text(encoding="utf-8", errors="replace")
        findings = lint(text, args.strict)
        if any(f.severity in ("CRITICAL", "WARNING") for f in findings):
            any_blocking = True
        all_reports.append({"file": str(df), "findings": [f.to_dict() for f in findings]})

    if args.json:
        print(json.dumps({"reports": all_reports}, indent=2))
    else:
        for r in all_reports:
            print(render_text(r))
            print()

    return 1 if any_blocking else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
