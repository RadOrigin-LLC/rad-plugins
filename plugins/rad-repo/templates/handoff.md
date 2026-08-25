---
rad_repo_handoff: 2
updated: <YYYY-MM-DD>
branch: <branch>
head: <full commit SHA or none>
worktree: <clean / dirty summary>
active_task: <task ID or short label>
next_action: <one exact action>
---
# Handoff

<!-- A snapshot, not a log. Refreshed by /wrapup or /ship from git evidence.
     Target ≤60 lines while preserving facts needed to resume. History lives in git and docs/archive/. Anything
     that must stay true after the next session belongs in docs/plan.md, not here.
     The Deferred section is the one part carried forward verbatim on every
     refresh. Prune an item only when its wake condition fires or the owner
     closes it. -->

## Last completed

<1–3 bullets grounded in the actual diff / commits / tests — not memory.>

## Current focus

<The current milestone or active task, from docs/plan.md.>

## Next action

<The single next step to pick up — for a new chat or after compaction.>

## Validation

<Commands run this session and their result, or "Not run this session.">

## Resume anchors

- Commit: <full SHA or none>
- Changed paths: <paths or none>
- Active initiative: <path or none>

## Watchouts

<Only material gotchas that will bite the next session. Omit if none.>

## Deferred — do not re-raise

<Items the owner knows about and has parked. Hooks and skills suppress anything
 matching a line here until its wake condition is met. `wake: never` means never.>

- <item> (wake: <condition or never>)
