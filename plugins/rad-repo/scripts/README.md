# rad-repo scripts

All scripts are Python-standard-library tools. Mechanical gates can block; heuristic
reports remain evidence for human or agent judgment.

## Executable contract

### `repo_contract.py`

Discovers root and scoped `AGENTS.md` files, excludes dependency, build, worktree,
template, and fixture trees plus out-of-repository symlinks, parses labeled validation commands, records each command
source, and merges optional global or path-scoped commands from `.rad-repo.json`.
Every configured scope target must exist. When `allow_empty` is false, the JSON
plan reports and blocks every changed path that has no matching command.

```bash
python repo_contract.py <project-dir> src/app.py --json
```

### `repo-doctor.py`

Shows profile, path scopes, validation command sources, command fingerprint, local
approval state, document-model version, and packaged resource state. `--approve`
writes only the reviewed fingerprint to local Git settings. It never runs validation.

```bash
python repo-doctor.py <project-dir> --json
python repo-doctor.py <project-dir> --approve --json
```

### `pre_ship.py`

Inspects staged Git blobs rather than untrusted working-tree copies. It blocks
protected paths, high-confidence secret patterns, unexpected generated output, oversized files,
unreviewed contract changes, unapproved commands, failed validation commands, and missing validation
declarations unless `validation.allow_empty` is explicitly true.

```bash
python pre_ship.py <project-dir> --run-validation --json
```

Exit `1` means shipping is blocked. Review contract changes before adding
`--allow-contract-change`; unstaged contract edits cannot be bypassed, and the flag
is never a general bypass.

Validation results include per-command and total timing so slow repository checks
can be scoped or moved to CI with evidence.

### `repo-snapshot.py`

Collects Git state, repository scan output, document freshness, workflow profile,
handoff metadata, and phase timing in one read-only JSON result for startup and ship.

```bash
python repo-snapshot.py <project-dir> --json
```

### `memory-recall.py`

Searches decisions and lessons by keyword and optional repository path. It returns
five active records by default and marks stale or unverified evidence. It never writes.

```bash
python memory-recall.py <project-dir> "validation scope" --path src/api --json
```

## Context validators

### `code-hotspots.py`

Ranks tracked source files by recent Git changes and file size. It excludes common
generated and dependency folders, reports raw evidence, and detects available
quality tools without running or installing them.

```bash
python code-hotspots.py <project-dir> --months 12 --limit 10 --json
```

### `repo-scan.py`

Reports deterministic shelf drift, size budgets, instruction files, and malformed
active initiatives. It exits `0`; consumers use JSON severity and findings.

### `doc-freshness.py`

Reports commit-distance trust bands. Managed docs may add frontmatter `tracks:` paths;
the report then identifies missing paths and code changes since the document's last
commit. This is stronger evidence than age alone but is not proof that prose is
semantically current.

### `vocab-lint.py`

Uses `.rad-repo.json` vocabulary profiles. `advisory` is the default and exits
`0`; `strict` emits error findings and exits `1`; `off` disables synonym checks.

### `doc-contradiction.py`

Checks PRD non-goals against plan commitments and locked decision constraints against
plan objectives. Matching is lexical/containment-based and must be reviewed before
editing authoritative docs.

### `doc-redundancy.py`

Checks managed shelf docs and active initiatives for substantial cross-document
duplication while filtering common template headings. Medium findings exit `1`.

### `audit-user-content.py`

Audits user-owned portions of all in-repository `AGENTS.md` files for dead paths and
orphan terminology. It never edits content and exits `0` with advisory findings.

## Configuration

Copy `../templates/repo.json` to `.rad-repo.json`. The workflow profile defaults to
`core`. JSON is validated;
invalid modes, scopes, lists, command objects, or shipping values fail closed in the
contract and pre-ship tools.

## Tests

```bash
python tests/run_all.py
```

Each executable behavior has a focused regression file. Fixtures cover malformed
Markdown, nested instructions and monorepos, Unicode and Windows-style paths,
out-of-root symlinks, Git and no-history repositories, staged blobs, and configured
exceptions.
