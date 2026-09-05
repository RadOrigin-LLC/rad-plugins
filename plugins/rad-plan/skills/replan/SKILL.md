---
name: replan
description: Revise an existing implementation plan when scope, shipped work, or new evidence changes the remaining work.
---

# Replan

Bring the current plan back in line with evidence. Preserve history and require owner approval before structural changes.

Do not write application code or run project tests. Write the detected plan path and, when already present, append-only decisions or ideas entries. Put other document changes in `## Durable follow-ups` inside the plan.

## Resolve paths and contract

Resolve the plugin root as two directories above this skill directory. Read `references/plan-template.md` as the plan authority. A repository `AGENTS.md` document model overrides its defaults.

## Harness support

Use the host's available subagent tool for independent reviewers; role names such as `risk_assessor` describe the assignment, not a required model or tool name. If independent review is unavailable, complete the mechanical checks and draft, report the missing review, and leave approval pending. Do not label self-review as independent review.

## Companion-skill rule

Name a RAD Repo or RAD Brainstorm skill only when current evidence needs the exact workflow, the exact skill appears in the current available-skill list, and it would add clear value. Report the need in plain language when absent. Never invoke a suggested companion unless the owner asks or accepts.

## 1. Gather evidence

Detect the plan in this order: `docs/plan.md`, `docs/planning/current-execution.md`, `docs/planning/current.md`, `PLAN.md`.

If no plan exists, route to `plan` for clear work or `rescue` for an unclear project.

Read in one batch when present:

- the full plan;
- `docs/handoff.md`, `docs/prd.md`, `docs/ideas.md`, `docs/decisions.md`, and `AGENTS.md`;
- Git history and changed paths since the plan's Updated date;
- current worktree status.

Use repository evidence instead of chat memory. Do not classify unverified work as shipped.

## 2. Classify the current plan

Classify every live milestone and task:

- **Shipped:** artifacts and validation evidence support completion.
- **Partially done:** some evidence exists; name what is missing.
- **Not started:** no implementation evidence exists.
- **Obsolete:** the work no longer fits current approved direction.
- **Drifted:** implementation exists that the plan did not name.

Ask one batched question set for ambiguous items. The owner confirms obsolete work and surprises.

If `docs/ideas.md` exists, give each relevant parked idea a fair hearing:

- pull in;
- keep parked;
- reject with a short reason appended to the existing entry.

## 3. Preview the delta

Before editing, show:

```text
Plan versus evidence:
Shipped: <items and evidence>
Partial: <items and missing work>
Unstarted: <items>
Obsolete: <items and reason needing confirmation>
Drifted: <unplanned implementation>

Proposed plan delta:
Added: <new outcomes, milestones, tasks, or assumptions>
Modified: <scope, order, validation, or meaning changes>
Removed: <obsolete live work moving to preserved history>
```

Wait for owner approval before restructuring.

## 4. Update the plan

On approval:

1. Move shipped task blocks to `## Shipped`, newest first.
2. Rewrite live dependencies that pointed to shipped tasks as `none - predecessor shipped` without the old task ID.
3. Split partial work into a shipped note and a new live task.
4. Strike obsolete milestones with a reason and move their tasks to `## Shipped`.
5. Pull Next into detailed Now work only after the owner confirms its scope.
6. Strike invalid assumptions and keep them. Add confirmed replacements.
7. Refresh `## Outcome coverage` so every live outcome maps to live tasks and final proof.
8. Mark task file entries `[existing]` or `[new]` after a bounded check of the relevant code surface.
9. Warn when a milestone has more than five tasks or the plan has more than 20 live tasks.
10. Add one dated Added/Modified/Removed note under `## Durable follow-ups` only when a durable document also needs a later change.
11. Set Status to DRAFT, update the date, and add the 7.1 marker when the plan is upgraded to the new contract.

Use safe recovery rules from `references/failure-state-template.md`. Do not place destructive Git or recursive-delete commands in Rollback.

## 5. Check and approve

Run the linter against the detected plan path:

```bash
python <plugin-root>/scripts/plan-lint.py <plan-path> --json
```

Fix CRITICAL and HIGH findings.

Run one bounded, read-only risk pass using `references/subagent-prompts/risk-assessment.md`. Pass the detected plan path and note that `## Shipped` is history and outside review. Validate the JSON with `validate-json.py`. Fix blocking issues once and surface anything unresolved.

Present the new release map, outcome coverage, Added/Modified/Removed summary, milestones, and checks. The plan stays DRAFT until the owner approves it.

After approval, set Status to APPROVED, update the date, append confirmed entries only to decisions or ideas files that already exist, and run the linter once on the final plan.

## Boundaries

- Preserve shipped and obsolete history.
- Do not edit an existing PRD or other durable document.
- Do not create a temporary update-prompt.
- Do not execute or test application code.
- Do not invoke companion skills without owner acceptance.
