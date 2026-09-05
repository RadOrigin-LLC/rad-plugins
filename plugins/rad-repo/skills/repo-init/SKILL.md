---
name: repo-init
description: Initialize the RAD Repo document model in a new or nearly empty repository. Use adopt for an established repository.
allowed-tools: Read Glob Grep Bash Write AskUserQuestion
---

# Repo Init — build the container

Lay the foundation for a fresh, nearly empty repo. Build the **container only** —
the shelf docs (`decisions.md`, `ideas.md`, `prd.md`, `plan.md`, …) are created later,
each when its trigger fires (see `../../references/shelf-spec.md`). **Do not
write product, plan, or design content** — that's the owner's and the planning
workflow's job. Templates live in `../../templates/`.

Use this only for greenfield setup. An established repo with history and docs goes to
`adopt` (archaeology first); an on-model repo with drift goes to `repo-align`.

## 1. Look before scaffolding

```bash
git status --short
git remote get-url origin   # for the AGENTS.md remote line, if set
```

Glob the repo. Detect the app type and package manager if obvious (`package.json`,
lockfiles, `pyproject.toml`, `Cargo.toml`, framework config) — this only informs the
`AGENTS.md` identity line, not product content.

Confirm this is greenfield: no `AGENTS.md`, no real docs, little or no git history.
If the repo is established, stop and recommend `adopt`.

## 2. Agent scope and profile

RAD Repo creates `AGENTS.md` as the repository contract. Codex and OpenCode load it natively. In other harnesses, read it explicitly when it is not loaded. Create or edit client-specific import files only when requested.

The default RAD Repo profile is `core`. Do not create `.rad-repo.json` only to
record that default. If the owner wants the full profile to persist, add
`"profile": "full"` to the config after approval.

## 3. Scaffold — container only, only what's missing

Create only files that don't already exist. **Never overwrite a user-authored file
without explicit confirmation.**

- `AGENTS.md` ← `templates/AGENTS.md` — the L0 skeleton: identity line, `deploy:`
  line, stack/commands placeholders, the **doc-model block** (stamp it verbatim from
  `templates/doc-model-block.md` — it's what makes every other tool conform), the
  "How we work" contract, and the hard-rule slots. Keep it within its 40-line budget.
- `docs/` and `docs/archive/` folders; `docs/archive/README.md` ← `templates/archive-README.md`.
- `docs/handoff.md` ← `templates/handoff.md` — the stub, placeholder values, including
  the `## Deferred — do not re-raise` section.

Do **not** create any shelf doc — no `prd.md`, `plan.md`, `decisions.md`, `ideas.md`,
`lessons.md`, `design.md`, `architecture.md`, or `api.md`. Their triggers haven't
fired; planning births prd/plan, and the rest appear on first real content.
Do **not** run fit-out here. No code exists yet, so there are no traits to detect.
Fit-out runs during `adopt` or from an explicit fit-out request. Do not create `docs/status.md`,
`docs/roadmap.md`, `docs/inbox/`, or loose root-level status docs. Do not create a
scoped `AGENTS.md` unless a subtree already has materially different commands,
constraints, ownership, or generated-code rules; root defaults remain authoritative
everywhere else and scoped files must not duplicate them.

Do not create `docs/initiatives/` speculatively. When an approved, finite migration
cannot fit cleanly in `docs/plan.md`, create one file from `templates/initiative.md`,
link it from the plan, and archive it when its `retire_when` condition is met.

## 4. Fill only what's mechanical

Set the remote line from `git remote get-url origin` if available. Leave `deploy:`
as `none` unless the user names a target. Stamp the handoff stub's `**Updated:**`
with today's date. Note in one line that future sessions should start with
`startup`, end with `wrapup`, and use `repo-align` for drift cleanup. Leave every
other `<PLACEHOLDER>` for the owner. Do not invent goals,
stack, rules, or validation promises.

## 5. Hand off

Tell the user, plainly: the container is in place; the docs themselves get created
when they're first needed. **The next step is the planning workflow** — its interview
births `docs/prd.md` and `docs/plan.md` and seeds the first decisions and ideas.

## Output format

```text
Repo init:
Detected repo type:
Agent scope:
Files created:
Files skipped (already exist):
Next step for the user:   planning workflow
Notes:
```

## References

- `../../templates/`: AGENTS.md skeleton, doc-model block, handoff stub, archive README
- `../../references/shelf-spec.md` — the shelf, triggers, budgets, one-writer table
