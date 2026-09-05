---
name: startup
description: Give a read-only repository session briefing from Git state, document freshness, and the current handoff.
allowed-tools: Read Glob Grep Bash
---

# Startup — orient, fast and read-only

Get oriented at the top of a session. **Read-only and
lean** — read the docs and git state, report trust, state the next task, stop. This
is not onboarding (`repo-init` / `adopt`) and not an audit (`repo-align`).

## What this skill does NOT do

- No scaffolding or onboarding — a fresh repo gets pointed at `repo-init`; an
  established repo without the doc model gets pointed at `adopt`.
- No deep audit, contradiction check, or doc filing — that's `repo-align`. (The
  mechanical scans are read-only and near-instant — evidence, not an audit.)
- No reading of `docs/archive/`.
- No cleanup, no writes of any kind, no commits, no fixing anything the trust
  report flags.
- No offering to run `wrapup`/`ship` or any end-of-session action.

## Procedure

1. **Gather evidence** with one read-only snapshot (`python` on Windows / PowerShell,
   `python3` elsewhere):

   ```bash
   python3 ../../scripts/repo-snapshot.py . --json
   ```

   (If Python is unavailable, compute commits-behind by hand with
   `git rev-list --count $(git log -1 --format=%H -- <doc>)..HEAD` per doc, or say
   the scans were skipped — don't guess at hygiene.)
2. **Read the instruction map** returned by repo-scan and glob the `docs/` shelf.
   Root `AGENTS.md` supplies defaults; for any current focus path, also read each
   scoped `AGENTS.md` from root to the closest containing directory. Closest scope
   wins on conflicts. Decide the path:
   - **Fresh repo** — no `AGENTS.md`, no docs, little history → recommend
     `repo-init` and stop.
   - **Established but un-managed** — real code/history but no doc model →
     recommend `adopt` and stop.
   - **Managed repo** — orient (below).
3. **Read L0/L1 + direction**: report the snapshot profile. Read applicable
   `AGENTS.md` files and `docs/handoff.md` in one batch. When handoff schema 2 is
   fresh and supplies `active_task` plus `next_action`, do not read the plan. Read
   `docs/plan.md` only when the handoff is missing, stale, legacy, or links a plan
   section needed to understand the next action. Read one linked active initiative
   when it owns the task.
4. **Recall only relevant durable memory**: when the next action names a component,
   path, past choice, or prior failure, run `memory-recall.py` with that subject and
   path. Return at most five records. Skip recall when it adds no task value.
5. **Build the trust report** from the snapshot freshness JSON (`trust` block) — one line
   per managed doc that exists, measured in **commits-behind** (commits on HEAD since
   the doc's last modifying commit). Thresholds (from
   `references/shelf-spec.md`): handoff 0–3 green · 4–10 yellow (nudge a quick
   wrapup) · >10 red (recommend `repo-align` first). decisions/ideas/lessons are
   append-only — always green. prd/plan/AGENTS.md lines are informational
   (commits-behind, no verdict). Add the repo-scan line: loose docs and any L0/L1
   size-budget overage. Grounded counts and file names, not impressions. If the
   handoff is stale, treat its resume point with suspicion and say so.
6. **Surface the briefing** (format below) and **end with the next task from the
   handoff** — that line is the deliverable. The only forward actions you may
   suggest: `repo-init` (fresh), `adopt` (un-managed), a quick `wrapup` (yellow
   handoff), or `repo-align` (red / drift).

## Output format

```text
Startup:
Branch:           <current branch>
Profile:          <core / full>
Working tree:     <clean / dirty summary>
Trust:
  handoff.md      <✅ N behind | ⚠️ N behind — quick wrapup? | ❌ N behind — align first>
  plan.md         <N behind (informational, e.g. "M4 shipped?") | missing>
  prd.md          <N behind | missing>
  AGENTS.md       <N behind | over budget (N lines > 40)>
  decisions.md    <✅ append-only | missing>
Hygiene:          <from repo-scan: "tidy" | "N loose ends: <names>" | budget overages>
Instructions:     <root only | root + scoped overlays for current focus>
Current focus:    <from docs/plan.md, one line, if present>
Deferred:         <count of items in the handoff's Deferred ledger, or "none">
Recall:           <N relevant records / not needed>
Next task:        <the Next action from docs/handoff.md — the last line of the briefing>
```

## References

- `../../references/shelf-spec.md` — the shelf, trust thresholds, size budgets.
