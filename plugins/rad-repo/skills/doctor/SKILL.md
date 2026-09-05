---
name: doctor
description: Diagnose RAD Repo validation declarations, command trust, path scopes, or missing resources without running project validation.
---

# RAD Repo Doctor

Explain the repository contract before another workflow runs it.

## Check

Run this from the target repository. Resolve the script relative to this skill file.

```powershell
python ../../scripts/repo-doctor.py . --json
```

Use `python3` when `python` is unavailable.

Report:

- Active `core` or `full` profile.
- Changed paths and their nearest instruction files.
- Each validation command and its source.
- `validation.allow_empty` state.
- Local command approval state.
- Document-model stamp state.
- Missing packaged resources.

If no commands were found, name each affected path and show where RAD Repo looked. Recommend a labeled command in the nearest `AGENTS.md` or an exact `.rad-repo.json` entry. Do not invent a command.

## Approve commands

When `approval_required` is true, show the exact command list and ask once. After explicit approval, run:

```powershell
python ../../scripts/repo-doctor.py . --approve --json
```

Approval writes the command fingerprint to local Git settings. It is clone-local and never enters a commit. A command change invalidates the old approval.

## Boundaries

- Do not run validation, builds, tests, deploys, or migrations.
- Do not approve commands without the owner's explicit answer.
- Do not edit repository files during diagnosis.
- Treat a missing document-model stamp as an upgrade note. It does not prove the repository is unsafe.
