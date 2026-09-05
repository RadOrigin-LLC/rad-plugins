---
name: ship
description: Commit and push reviewed repository work when requested, using the RAD Repo handoff and validation gates. Stops after push.
allowed-tools: Read Glob Grep Bash Write Edit AskUserQuestion
---

# Ship

Close the work with reviewed Git state and repository checks. Invoking `ship` authorizes the commit and push. Do not ask again for those two actions.

## Companion-skill rule

RAD Repo Ship owns the exact Git commit and push. RAD Coolify Actions owns platform deployment. RAD Repo Verify Release owns read-only commit-to-production proof.

After a successful push, offer `rad-coolify:coolify-actions` only when the current task needs platform deployment and that exact skill appears in the current available-skill list. Offer `rad-repo:verify-release` only when the current task needs commit-to-production proof and that exact skill appears in the current available-skill list. Ask whether the owner accepts each handoff and wait for acceptance before invoking it. If a skill is absent or the owner declines, report the next step without invoking it. Never invoke a companion silently. Ship still stops after push.

## 1. One context snapshot

Collect Git state, repository signals, freshness, handoff metadata, and phase timing
with one read-only command. Report findings. They block only for a real safety or
contract problem.

```powershell
python ../../scripts/repo-snapshot.py . --json
```

## 2. Quick wrapup

Run the normal wrapup steps inline. Preserve useful handoff detail. Ask about a decision or lesson only when session evidence gives a real candidate.

Suggest a RAD Plan skill only when a real planning need exists and the exact skill
appears in the current available-skill list. When it is unavailable, report the need
without naming RAD Plan. Do not invoke it unless the owner asks or accepts the
suggestion.

## 3. Review and stage

```powershell
git status --short
git diff --stat
git add -- <reviewed-paths>
git diff --cached --stat
git diff --cached --check
```

Never use `git add -A`. Stage only requested work and wrapup documents. Stop for unrelated paths, conflict markers, or whitespace errors.

## 4. Run the pre-ship gate

```powershell
python ../../scripts/pre_ship.py . --run-validation --json
```

The gate checks staged blobs, high-confidence secret patterns, protected paths, generated output, file size, reviewed contract changes, local command trust, and validation results.

If `AGENTS.md` or `.rad-repo.json` is staged, show its staged diff and ask the owner to approve that contract change. Then rerun with `--allow-contract-change`. This flag does not bypass other findings.

## 5. Resolve trust only when blocked

The pre-ship report includes resolved validation commands, sources, fingerprint,
and timing. Do not run doctor on the normal trusted path. If the gate reports
missing or untrusted validation, run doctor once, show the exact commands and
sources, and gather all needed owner approvals in one round. After explicit
approval, run:

```powershell
python ../../scripts/repo-doctor.py . --approve --json
python ../../scripts/pre_ship.py . --run-validation --json
```

The approval stays in local Git settings. A changed command requires new approval.

## 6. Commit and push

Create a conventional commit message from the staged diff. Use the user's message hint when supplied.

Push the current branch. If it is not `main`, state the branch name. Stop on a rejected push. Never force-push, merge, or switch branches without a separate request.

## 7. Report local leftovers

List merged local branches and worktrees. Do not delete them without a separate owner approval.

## Final report

```text
Shipped: <commit> pushed to <remote/branch>
Handoff: <fresh / size note>
Validation: <commands and result>
Timing: <snapshot, validation, and total ship overhead>
Working tree: <clean / remaining paths>
Local leftovers: <count>
```

Stop after this report. Release verification belongs in the separate `verify-release` skill and runs only when the user explicitly asks for it. First-use fit-out belongs in `adopt` or an explicit fit-out request. It never runs inside ship.
