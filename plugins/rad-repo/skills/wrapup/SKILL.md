---
name: wrapup
description: Save a repository session handoff from Git and recorded validation evidence. Does not run tests or push.
allowed-tools: Read Glob Grep Bash Write Edit AskUserQuestion
---

# Wrapup

Leave enough evidence for a new session to continue without guesswork.

## Hard rules

- Use Git and recorded command output as evidence.
- Record validation that already ran. Do not run tests, builds, or linters.
- Read the current handoff before editing it.
- Preserve recovery facts that a new agent would need.
- Carry `## Deferred - do not re-raise` forward. Remove an item only when its wake condition fired or the owner closed it.
- Do not push.

## 1. Gather evidence

Run the read-only snapshot in one batch:

```powershell
python ../../scripts/repo-snapshot.py . --json
```

Use the conversation only for validation output that ran during this session. If no proof exists, write `Not recorded this session.`

## 2. Refresh the handoff

Use `../../templates/handoff.md` as the shape.

Edit the current handoff instead of replacing useful content with a shorter summary. Keep accurate reconstruction detail. Update stale facts and remove repeated history.

The normal target is 60 lines. If the active work needs more detail, link to the current file under `docs/initiatives/`. When no approved initiative holds the detail, preserve the useful handoff content and report the size note. Do not create a new status or resume document.

Required sections:

- Last completed
- Current focus
- Next action
- Validation
- Watchouts, when needed
- Deferred - do not re-raise

Add the current branch and working-tree state. Use one next action. Write handoff
schema 2 frontmatter and the Resume anchors from snapshot evidence.

## 3. Record durable facts only when evidence exists

When the owner already approved a lasting decision during this session, append one
typed dated line to `docs/decisions.md`. When validated session evidence established
a reusable lesson, append one typed dated line to `docs/lessons.md`. Use the format
in `references/shelf-spec.md`.

When approval or evidence is unclear, put at most one `Memory candidate` in the
closure report. Do not interrupt normal wrapup with a memory question. A full
wrapup may ask once for all real candidates. Design-system decisions belong in
`docs/design.md` and require approval for that exact edit.

## 4. Choose the requested close

### Normal `wrapup`

Write the handoff and leave repository changes uncommitted.

### `wrapup and commit`

This phrase authorizes one local documentation commit. Stage only the handoff and the approved decision, lesson, or plan-status files changed by this wrapup. Run `git diff --cached --check`.

If unrelated paths are already staged, stop and show them. Do not mix them into the wrapup commit. When the staged set is clean, commit with `docs: record session handoff`. Do not push.

### `wrapup and ship`

Use the `ship` workflow. Let ship own the commit and push.

## 5. Full reconcile

Run this only when the user asks for a full wrapup or the repository profile is `full`.

- Check whether this session made `AGENTS.md`, `docs/prd.md`, or `docs/plan.md` stale.
- Propose exact edits and ask per user-owned document.
- Make status-only plan edits. A structural plan change creates a planning need.
  Name a RAD Plan skill only when the exact skill is in the current available-skill
  list. Otherwise, report the need without naming RAD Plan. Invoke it only when the
  owner asks or accepts the suggestion.
- Run the cheap `repo-scan.py` hygiene check. Report findings without fixing them.

## Closure report

```text
Wrapup:
Handoff:      <updated / already current / preserved with size note>
Commit:       <not requested / hash>
Push:         not requested
Working tree: <clean / changed paths remain>
Validation:   <recorded result / not recorded>
Memory:       <appended record ID / one candidate / none>
Next action:  <one action>
```

Stop after this report.
