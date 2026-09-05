---
name: repo-align
description: Review RAD Repo documentation drift and propose approved corrections to structure, references, or conflicting guidance.
allowed-tools: Read Glob Grep Bash Write Edit AskUserQuestion
---

# Repo Align — bring the repo back to the shelf

The deep, opt-in pass — run it every ~25 commits or when the trust report goes red.
Find documentation drift, surface it in plain English, and **propose one disposition
per judgment call — always confirmed before acting. Never silently merge, delete,
archive, or rewrite.**

The model you're aligning to is `../../references/shelf-spec.md` — the
context stack (L0 `AGENTS.md` ≤40 lines, L1 `docs/handoff.md` ≤60 lines), the closed
shelf of docs under `docs/`, the vocabulary ladder, the one-writer table, and the
domain-authority matrix. Read it before judging.

With `--report-only`, do steps 1–3 (find and present) and stop — propose no changes.

## 1. Run the mechanical scans

Pure-stdlib, advisory. Capture each JSON; they surface **candidates**, not verdicts.
Your judgment decides which are real. (Use `python3`, or `python` on Windows.)

```bash
python3 ../../scripts/repo-scan.py . --json --no-record      # floating docs, inbox, L0/L1 size budgets
python3 ../../scripts/doc-freshness.py . --json              # trust report, stale docs
python3 ../../scripts/vocab-lint.py . --json                 # profile-driven synonyms, wrong-doc ladder terms
python3 ../../scripts/doc-contradiction.py . --json          # prd non-goals vs plan commitments
python3 ../../scripts/doc-redundancy.py . --json             # same fact in two docs
python3 ../../scripts/audit-user-content.py . --json         # orphan terms, dead paths in AGENTS.md
```

(If Python 3 is unavailable, do the same checks by reading the docs directly and say
the mechanical pass was skipped.)

**Size budgets:** the repo-scan JSON flags `l0_over_budget` (AGENTS.md > 40 lines)
and `l1_over_budget` (handoff > 60 lines). L0 overflow is a rules-audit trigger
(step 2d); L1 overflow means durable content leaked into the handoff — route it to
`plan.md`/`prd.md`/`lessons.md` in step 4.
The same report returns the root-to-leaf instruction map and flags active initiative
files missing required lifecycle metadata. Root L0 budgets do not apply to scoped
overlays.

## 2. The judgment passes

### 2a. Doc router — read what's off the shelf, route its content

For every file the scan flagged as floating (created since the last pass, not on the
shelf): **read it** — don't just report the filename. Classify what's *inside* and
propose a routing per finding, e.g. "this file is three settled decisions and one
idea — append them to `docs/decisions.md` / `docs/ideas.md`, then archive the file?"
Transient brainstorm specs (`docs/*-spec.md` / `*-design.md`) whose plan already
exists get proposed for `docs/archive/`. A domain reference doc with no shelf slot is
a **satellite**, not a loose end — propose a link from the nearest core doc if it's
unlinked, and leave it in place (shelf-spec "Satellite docs" / "Conformance without
loss"). Propose, never silently act.

A substantial approved migration may be relocated to `docs/initiatives/<slug>.md`
only when it has an owner, baseline, plan link, acceptance criteria, rollback
strategy, retirement condition, and archive destination. Never use an initiative as
a permanent second plan or as a loophole for untriaged notes.

### 2b. Vocabulary lint

Read the configured vocab-lint profile and findings. Advisory synonym hits invite a
proposed reword; strict hits must be resolved or explicitly reconfigured. Judge each
candidate — "staging environment" is not a tracked unit — and do not force changes
for advisory prose hits. Ladder terms in the wrong doc still need routing. Content-level plan
problems get flagged to the planner replan skill, not fixed here (format is this
plugin's lane; plan substance is the planner's).

Name `rad-plan:replan` only when a structural plan problem exists and that exact
skill appears in the current available-skill list. When it is unavailable, report
the planning need without naming RAD Plan. Do not invoke it unless the owner asks
or accepts the suggestion. Apply this rule to every planner handoff in this skill.

### 2c. api.md route-diff — only when `docs/api.md` exists

Mechanical-first: grep the code for route definitions and diff against the doc.
Typical patterns — Express/Fastify `app.get|post|put|patch|delete(`, Next.js
`app/**/route.ts` / `pages/api/**`, Flask/FastAPI `@app.route|@router.get(...)`,
Rails `routes.rb`. Compare the endpoint list against `docs/api.md`: routes in code
but not the doc → undocumented; routes in the doc but not the code → stale. Propose
the specific doc edits. If no route patterns match the codebase, say the diff was
inconclusive rather than guessing.

### 2d. Rules audit — on request (`--rules-audit`) or when L0 is over budget

For each rule in `AGENTS.md`, classify by evidence (git history, lessons.md, what
you can observe in the repo — say when evidence is thin):

- **Promote to validator** — violated in practice AND mechanically checkable.
- **Keep** — violated in practice, needs judgment; it earns one of the ≤7 hard-rule
  slots.
- **Demote** — dormant (no sign it's been needed in months) → move to a referenced
  guardrails file (`docs/archive/` or a linked doc), leaving L0 lean.

Present the classification with one line of reasoning per rule. Propose-only — the
owner decides every move; this is how a beloved-but-bloated AGENTS.md gets condensed
without losing the guardrails the owner values.

### 2e. The classic drift checks

Read the shelf docs that exist plus `README.md`, `docs/archive/` names
(not contents). Identify: duplicate authorities, stale docs, pointer chains, missing
docs whose triggers have clearly fired, contradictory read paths, off-model
status/roadmap docs, and root-README content that has become stale status. For scoped
`AGENTS.md`, flag only orphaned overlays, duplicated root facts, or rules without a
material subtree-specific reason.

**Resolve contradictions by domain authority** (shelf-spec): applicable instructions
and ADRs govern constraints; PRD governs product intent; architecture/API plus code
evidence govern current state; plan and linked initiatives govern approved future
change; design governs visual direction; handoff is only a resume snapshot. A plan
cannot override a locked ADR or make future work current. Propose bringing the stale
source into line as a drafted edit (step 5). **If domain authority cannot decide, or
code and docs conflict without a settled decision, STOP and surface it under "Needs
a decision." Never silently merge two conflicting decisions.**

**Check the role boundaries** — each doc holds only its own kind of content:
execution detail in the PRD → plan.md; permanent product rules in the plan → prd.md;
durable facts in the handoff → plan/prd/lessons; product summaries or roadmap in
AGENTS.md → replace with a pointer. Settled decisions stranded in a brainstorm, the
handoff, or AGENTS.md → propose appending to `docs/decisions.md` (visual/design
decisions → `docs/design.md`).

**Terminology / superseded sweep.** If `AGENTS.md` has a `## Retired terminology`
table, grep the managed docs for each retired term and flag stray uses (suggest the
replacement). Regardless, flag any doc that calls something "current" when its
domain authority has overtaken it, and any superseded content lacking a
superseded banner.

## 3. Present findings — plain language, grouped

```markdown
# Repo alignment

## Needs a decision
- The plan builds offline mode, but the PRD lists offline as a non-goal. Which wins?

## Doc router
- `docs/2026-06-28-notes.md` — contains two settled decisions and an idea: append to decisions.md/ideas.md, archive the file?

## Vocabulary
- `docs/prd.md:14` says "sprint 2" — the ladder term is Milestone (M2), and it belongs in plan.md, not the PRD.

## Size budgets
- `AGENTS.md` is 57 lines (budget 40) — rules audit below proposes what to demote.

## api.md route-diff
- `POST /api/upload` exists in code but not in docs/api.md.

## Conflicts / redundancy / role-boundary leaks
- `docs/prd.md` and `AGENTS.md` both define the validation steps — pick one home.

## Rules audit (when run)
- "Never push without tests" — violated twice, mechanically checkable -> promote to a validator or L0 rule.

## Loose / misplaced docs · pointer problems · missing docs
- `smoke-2026-05-30.md` (repo root) — a smoke-test report sitting loose.

## Suggested actions
[per-item dispositions below]
```

No jargon, no validator names in the user-facing report — describe the problem and
the fix in words a non-coder follows.

## 4. Offer fixes — closed disposition set, confirmed per item

For each finding, propose ONE disposition and ask before acting (via
AskUserQuestion, `ask_question` on Antigravity, or a clear yes/no per item):

1. **Route** — append the content to its shelf home (decisions/ideas/lessons/design), then archive the original.
2. **Fold** — merge durable content into the owning shelf doc, then archive the original.
3. **Archive** — historical / done → `git mv` into `docs/archive/`, add the archive banner.
4. **Relocate** — a misplaced doc → move to its shelf home.
5. **Banner** — content overtaken but staying in place → add a superseded banner pointing at the current authority.
6. **Reword** — a vocabulary or budget fix inside a doc this plugin may edit.

Rules:

- **Propose, never auto-act.** Every route/fold/move/delete waits for the user's yes.
- **Preserve history:** move tracked files with `git mv`, never delete-and-recreate.
- **Append-only files stay append-only** — route content by appending new entries,
  never by editing existing decisions/ideas/lessons lines.
- After approved moves, confirm the L0/L1 read path still points at reality.

## 5. Durable changes — draft the edit, apply only on explicit confirmation

When a finding implies a change to a doc the manager doesn't write — `docs/prd.md`,
`docs/design.md`, or `docs/plan.md` content — the user owns the *decision*, not the
typing. Draft the exact edit (old → new) and ask per doc via AskUserQuestion:
**apply / skip / let me reword**. Apply only on an explicit "apply" for that specific
edit; a skip means hands off, restated in one line at the end. Never bundle
user-owned edits into a blanket OK. Structural plan problems go to the planner
replan skill, not to an edit here.

## What this skill does NOT do

- Does not auto-apply judgment calls — every move/merge/archive/reword is user-confirmed.
- Does not write `docs/prd.md`/`docs/design.md` without an explicit per-edit "apply".
- Does not edit existing entries in append-only docs.
- Does not create `docs/status.md`, `docs/roadmap.md`, `docs/implementation-plan.md`,
  or loose root status docs. Scoped agent files are allowed only for evidenced
  subtree-specific commands, constraints, ownership, or generated-code rules.
- Does not run on every session — it's the opt-in deep pass (`ship` runs only the
  mechanical scans, none of the judgment passes).

## References

- `../../references/shelf-spec.md` — the shelf, ladder, budgets, one-writer table, domain authority
- `../../scripts/` — the six drift-signal scans
