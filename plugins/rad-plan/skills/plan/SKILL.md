---
name: plan
description: Create an evidence-backed implementation plan for a clear project or feature before coding.
---

# Plan

Produce an approved implementation plan that a solo owner can read and a fresh coding agent can execute.

Do not write application code or source files. Planning artifacts are the only allowed output.

## Resolve paths

Resolve the plugin root as two directories above this skill directory. Convert each referenced plugin path to an absolute path before reading or running it.

Read `references/plan-template.md` as the authority for the plan contract. A repository `AGENTS.md` document model overrides its default names and headings.

## Write boundary

- Write the current plan at the detected plan path. Use `docs/plan.md` for a new plan.
- Create `docs/prd.md` only when it is missing or skeletal, only from confirmed interview answers, and only after section approval.
- Append confirmed decisions or ideas only when `docs/decisions.md` or `docs/ideas.md` already exists.
- Put other confirmed document changes in the plan's optional `## Durable follow-ups` section.
- Do not create decisions, ideas, architecture, API, status, roadmap, timeline, or update-prompt files.
- Propose an `AGENTS.md` stack block in chat when useful. Write it only after separate owner approval.

## Harness support

Use the host's available subagent tool for independent reviewers; role names such as `risk_assessor` describe the assignment, not a required model or tool name. If independent review is unavailable, complete the mechanical checks and draft, report the missing review, and leave approval pending. Do not label self-review as independent review.

## Companion-skill rule

Name a RAD Repo or RAD Brainstorm skill only when all conditions are true:

1. Current evidence needs that exact workflow.
2. The exact skill appears in the current available-skill list.
3. Using it would add clear value for this project.

When a companion is absent, report the need in plain language. Never invoke a companion from a suggestion unless the owner asks for it or accepts the suggestion.

The public brainstorming plugin namespace is `rad-brainstorm:*`.

## 1. Understand the work

Read `references/discovery-interview.md`.

### Route first

- Use `rescue` when the project goal or current state is unclear.
- Use `replan` when a real plan exists and work has changed or shipped since it was written.
- Continue here for greenfield work or a clear next effort.

If the idea is still undecided, explain which product or design questions must be settled. Suggest an exact `rad-brainstorm:*` skill only under the companion-skill rule.

If a bare repository has no `AGENTS.md` and no `docs/`, explain that a small repository contract would help. Suggest `rad-repo:repo-init` only under the companion-skill rule. Continue with built-in defaults when it is unavailable or declined.

### Read evidence before questions

For an existing repository, start with applicable instructions, the current plan or handoff, and the approved product scope. Read the README, configuration, or relevant specs only to resolve a planning question. Treat the PRD as product authority; ask about contradictions and unresolved choices.

### Choose depth

Use the user's requested depth. Otherwise use quick for one known change without a new service, deployment target, auth, payment, personal-data, or schema risk; use full for new products, cross-system work, or those risks. State the choice and proceed. Ask only when the depth would materially change the requested outcome.

### Run discovery

Full planning uses the coverage areas in `discovery-interview.md` to find gaps, with at most three question rounds and no repeated confirmation of settled scope.

Quick planning uses the available evidence and asks only unresolved questions that affect scope, correctness, or acceptance. Combine needed questions into one batch of at most five. Summarize the settled scope; do not require a separate interview or assumption-confirmation round when the user already supplied it. Keep remaining unknowns visible as assumptions or risks. Draft a PRD only when requested.

For full planning, offer the PRD gap check from `discovery-interview.md`. Confirm each proposed section before writing.

### Check the implementation surface

After scope is settled and before task paths are written, inspect the likely implementation surface.

1. Find the entry point, affected module, nearest tests, and relevant configuration.
2. Read only those files and their direct callers or imports when needed.
3. Expand the inspection only when a named uncertainty affects the plan.
4. Mark every planned path as `[existing]` or `[new]`.
5. When a path remains uncertain, make bounded discovery part of the task instead of inventing a path.

Stop the read when the task boundary is clear. Do not build a permanent code map.

## 2. Decide the stack only when needed

Skip this step when the current stack can meet the requirement and the work adds no new platform, service, or dependency.

When a real choice exists, read `references/golden-path-matrix.md` and dispatch one bounded, read-only `stack_advisor` subagent using `references/subagent-prompts/stack-eval.md`. Require JSON-only output and no file edits. Pass the project context, current stack, mode, and absolute plugin root.

Validate the result:

```bash
python <plugin-root>/scripts/validate-json.py \
  <plugin-root>/references/subagent-prompts/stack-eval.schema.json - --extract-from-markdown
```

Use `python3` when that is the repository command. Re-prompt once on schema failure. Stop for the owner when requirements conflict or no supported option fits.

Record only the final choice and short reason in the plan. Put any confirmed durable change in `## Durable follow-ups` or append it to an existing decisions file after approval.

## 3. Build the plan

Use `references/plan-template.md` for required fields. Consult `failure-state-template.md` for recovery, `tdd-constraints.md` for task validation, `context-management.md` for work that spans sessions, and `anti-patterns.md` when reviewing a specific planning weakness. Read only relevant sections; do not reload a reference already in context.

Build in this order:

1. Write the Now, Next, and Later release map. Only Now receives tasks.
2. Define observable outcomes for Now.
3. Map each outcome to at least one task and one final proof in `## Outcome coverage`.
4. Decompose Now goal-backward into shippable milestones.
5. Put the hardest unknown first when it can invalidate later work.
6. Aim for two or three tasks per milestone. Warn above five.
7. Warn and ask for a smaller current release when the live plan exceeds 20 tasks.
8. Give every task the six fields from the plan contract.
9. Use `[existing]` and `[new]` labels in Files.
10. Add a checkpoint after each milestone.
11. Use safe recovery rules from `failure-state-template.md`.
12. Put task-specific test detail in Validate using `tdd-constraints.md`.

Write the draft with `**Status:** DRAFT` and the 7.1 contract marker.

## 4. Check the plan

Run the mechanical check against the detected plan path:

```bash
python <plugin-root>/scripts/plan-lint.py <plan-path> --json
```

Fix CRITICAL and HIGH findings before judgment review.

Dispatch one bounded, read-only `risk_assessor` subagent with the detected plan path and `references/subagent-prompts/risk-assessment.md`. Require JSON-only output and no file edits. Validate it with `validate-json.py` and the risk schema.

- **Quick:** run one risk pass. Fix blocking issues once and surface anything unresolved.
- **Full:** run one first pass. Repeat only after a `REVISE` result and only after the plan changes. Stop after three total passes.
- **RETHINK:** stop and explain the product, scope, or architecture decision that needs more work. Suggest an exact `rad-brainstorm:*` skill only under the companion-skill rule.

## 5. Review with the owner

Present the result at the depth the owner needs. For a full plan, include:

1. Four to six plain sentences about the product, Now release, next horizon, and largest risk.
2. The release map.
3. The outcome coverage table.
4. Three to five decisions inside the plan.
5. Milestones and After this ships lines.
6. Task detail, lint result, and risk result.

Ask: "Does this match what you are trying to build? What should change before I approve it?"

The plan stays DRAFT until the owner approves it. Challenge one risky choice once with its cost and your recommendation. If the owner confirms it, record the decision and continue without repeating the objection.

## 6. Approve and finish

After approval:

1. Change the status to APPROVED and update the date.
2. Append confirmed decisions and ideas only to shelf files that already exist.
3. Keep absent-shelf entries and other document changes in `## Durable follow-ups`.
4. Propose a useful `AGENTS.md` stack block in chat when needed.
5. Run `plan-lint.py` once on the final plan and report the result.

## Plan location

Detect the current plan in this order:

1. `docs/plan.md`
2. `docs/planning/current-execution.md`
3. `docs/planning/current.md`
4. `PLAN.md`

Use `replan` when real work happened after the current plan. Update a stub in place. Create a new plan at `docs/plan.md`.

## Context use

Batch independent reads. Keep user approvals and workflow steps in order. Load only references required by the current step.
