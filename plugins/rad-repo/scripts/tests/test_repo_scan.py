#!/usr/bin/env python3
"""Regression test: repo-scan.py's floating-doc allowlist must track the shelf.

Background (2026-06-19): find_floating() allowed only the three core doc names
under docs/, so it flagged model-sanctioned docs as "floating" — crying wolf, the
exact thing its docstring promises it never does. The fix added ALLOWED_DOCS.

v2 (2026-07-02): the doc model is the shelf (references/shelf-spec.md). This test
pins the contract so it can't silently drift: the shelf filenames are read
*straight out of* shelf-spec.md's shelf table, and every docs/<name>.md the spec
shelves must NOT be flagged. Add a doc to the shelf without teaching the scan
about it and this test goes red.

It also keeps the scan honest in the other direction — genuinely off-shelf docs
must still be flagged, the glob must stay shallow, and the L0/L1 size budgets
must fire.

Plain stdlib; no pytest. Override the script under test with REPO_SCAN_PY (used to
prove the test has teeth against the pre-fix logic).

Run:  python test_repo_scan.py     (exits non-zero on failure)
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
PLUGIN = os.path.dirname(SCRIPTS)
SCRIPT = os.environ.get("REPO_SCAN_PY", os.path.join(SCRIPTS, "repo-scan.py"))
SHELF_SPEC = os.path.join(PLUGIN, "references", "shelf-spec.md")
PY = sys.executable

AGENTS = "# AGENTS\n\n## Cold-start read path\n1. docs/handoff.md\n"

_failures = []
_tmp = tempfile.mkdtemp()


def check(cond, msg):
    print(("PASS" if cond else "FAIL") + ": " + msg)
    if not cond:
        _failures.append(msg)


def make_repo(files):
    """files: {relpath: content}. Returns the repo dir."""
    d = tempfile.mkdtemp(dir=_tmp)
    for rel, content in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p) or d, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
    return d


def scan(root):
    r = subprocess.run([PY, SCRIPT, root, "--json", "--no-record"],
                       capture_output=True, text=True)
    assert r.returncode == 0, "scan exited %d: %s" % (r.returncode, r.stderr[:300])
    return json.loads(r.stdout)


def floating(root):
    return scan(root)["breakdown"].get("floating", [])


def shelf_docs_from_spec():
    """docs/<name>.md the shelf spec sanctions — read from the shelf table's rows
    so the test follows the spec, not a hardcoded copy of it."""
    names = []
    for ln in open(SHELF_SPEC, encoding="utf-8"):
        m = re.match(r"\|\s*`docs/([A-Za-z0-9._-]+\.md)`", ln)
        if m:
            names.append(m.group(1))
    return names


# --- centerpiece: every doc the SHELF declares must be allowed ---
shelf = shelf_docs_from_spec()
check(len(shelf) >= 8, "shelf-spec.md shelf table parsed (found %r)" % shelf)
for name in shelf:
    d = make_repo({"AGENTS.md": AGENTS, "docs/handoff.md": "x\n", "docs/" + name: "x\n"})
    check("docs/" + name not in floating(d),
          "shelf doc docs/%s is not flagged as floating" % name)

# --- teeth: genuinely off-shelf docs must STILL be flagged ---
d = make_repo({"AGENTS.md": AGENTS, "docs/handoff.md": "x\n",
               "docs/status.md": "x\n", "docs/scratch.md": "x\n",
               "docs/2026-07-01-widget-spec.md": "x\n"})
fl = floating(d)
check("docs/status.md" in fl, "off-shelf docs/status.md is flagged")
check("docs/scratch.md" in fl, "off-shelf docs/scratch.md is flagged")
check("docs/2026-07-01-widget-spec.md" in fl,
      "transient brainstorm spec is flagged (routing candidate)")

# --- size budgets: L0 (AGENTS.md > 40 lines) and L1 (handoff > 60 lines) fire ---
d = make_repo({"AGENTS.md": "x\n" * 41, "docs/handoff.md": "x\n" * 61})
rep = scan(d)
check("l0_over_budget" in rep["breakdown"], "AGENTS.md over 40 lines flags l0_over_budget")
check("l1_over_budget" in rep["breakdown"], "handoff over 60 lines flags l1_over_budget")
d = make_repo({"AGENTS.md": "x\n" * 40, "docs/handoff.md": "x\n" * 60})
rep = scan(d)
check(rep["loose_ends"] == 0, "at-budget L0/L1 stay green (got %s)" % rep["breakdown"])

# --- root allowlist: furniture allowed, stray status doc flagged ---
d = make_repo({"AGENTS.md": AGENTS, "README.md": "x\n", "LICENSE.md": "x\n",
               "CHANGELOG.md": "x\n", "STATUS.md": "x\n", "docs/handoff.md": "x\n"})
fl = floating(d)
check("STATUS.md" in fl, "stray root STATUS.md is flagged")
check(not ({"README.md", "LICENSE.md", "CHANGELOG.md", "AGENTS.md"} & set(fl)),
      "root furniture (README/LICENSE/CHANGELOG/AGENTS) is not flagged (got %r)" % fl)

# --- shallow by design: a properly-filed catalog doc in docs/reference/ is ignored ---
d = make_repo({"AGENTS.md": AGENTS, "docs/handoff.md": "x\n",
               "docs/reference/architecture.md": "x\n",
               "docs/reference/decision-log.md": "x\n"})
check(floating(d) == [], "docs/reference/* is ignored (subdir, not floating)")

# --- scoped instructions: legitimate overlays are reported, not root-budgeted ---
d = make_repo({"AGENTS.md": AGENTS, "docs/handoff.md": "x\n",
               "src/AGENTS.md": "x\n" * 75,
               "packages/web/AGENTS.md": "x\n" * 50,
               "node_modules/noise/AGENTS.md": "x\n" * 100,
               ".worktrees/feature/AGENTS.md": "x\n" * 100,
               "templates/project/AGENTS.md": "x\n" * 100,
               "fixtures/repo/AGENTS.md": "x\n" * 100})
rep = scan(d)
check("l0_over_budget" not in rep["breakdown"],
      "root L0 budget does not apply to scoped AGENTS.md overlays")
check(rep["instruction_files"] == ["AGENTS.md", "packages/web/AGENTS.md", "src/AGENTS.md"],
      "instruction map reports root and scoped overlays while excluding dependencies")

# --- active initiatives: lifecycle metadata is required ---
initiative = """---
title: AI abstraction migration
owner: Ryan
status: active
baseline: abc1234
linked_plan: docs/plan.md
retire_when: All acceptance criteria pass
archive_to: docs/archive/ai-abstraction.md
---

# AI Abstraction Migration

## Acceptance Criteria
- Existing assistant behavior remains covered.

## Rollback Strategy
- Revert the integration commit.
"""
d = make_repo({"AGENTS.md": AGENTS, "docs/handoff.md": "x\n",
               "docs/initiatives/ai-abstraction.md": initiative})
rep = scan(d)
check(rep["loose_ends"] == 0,
      "well-formed active initiative is accepted")

d = make_repo({"AGENTS.md": AGENTS, "docs/handoff.md": "x\n",
               "docs/initiatives/unfinished.md": "# Unfinished\n"})
rep = scan(d)
check("initiative_metadata" in rep["breakdown"],
      "initiative missing lifecycle metadata is flagged")
check(rep["breakdown"].get("initiative_metadata", {}).get(
          "docs/initiatives/unfinished.md"),
      "initiative finding names missing requirements")

# --- green path: a clean on-model repo reports zero loose ends ---
agents_full = ("# AGENTS\n\n## Cold-start read path\n"
               "1. AGENTS.md\n2. docs/prd.md\n3. docs/plan.md\n4. docs/handoff.md\n")
d = make_repo({"AGENTS.md": agents_full, "docs/prd.md": "x\n", "docs/plan.md": "x\n",
               "docs/handoff.md": "x\n", "docs/design.md": "x\n"})
rep = scan(d)
check(rep["loose_ends"] == 0 and rep["severity"] == "green",
      "clean on-model repo is green (got loose_ends=%s severity=%s)"
      % (rep["loose_ends"], rep["severity"]))

print()
if _failures:
    print("REGRESSION TEST FAILED: %d check(s) failed" % len(_failures))
    sys.exit(1)
print("ALL REPO-SCAN CHECKS PASSED")
sys.exit(0)
