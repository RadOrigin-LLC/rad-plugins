---
name: adopt
description: Bring an existing repository onto the RAD Repo document model, preserving code and approving document migrations.
allowed-tools: Read Glob Grep Bash Write Edit AskUserQuestion
---

# Adopt — bring an existing repo onto the doc model

`repo-init`'s sibling for repos that already have a life: code, history, and a pile
of docs written before the shelf existed. Archaeology first, questions second,
writes last — and **never a code change**. The target model is
`../../references/shelf-spec.md`.

**Boundaries:** evidence before questions (never ask what git can answer); propose
every doc move (never silently delete — `git mv` preserves history); the only
commands you run are read-only git/inspection plus the build/test commands in step 2
(to verify them, not to fix anything).

**Non-destructive by contract** — state this up front if the migration looks scary
(to the owner or to you): every move is `git mv`, every write is confirm-gated,
nothing is ever deleted. And a repo that already has a *working* doc model (homegrown
or an older version of this one) gets **mapped, not flattened** — apply "Conformance
without loss" from the shelf spec: rich existing content becomes a linked satellite,
shelf formats govern only new entries. Don't balk at the conversion; shrink it.

## 0. Choose the first-run depth

Recommend a **full** first adoption because it maps the existing document set once.
Ask the owner to choose full or core.

- **Full:** map and triage all candidate documents in bounded batches.
- **Core:** create or repair L0/L1, verify the contract, and inventory deeper docs
  without triaging them.

After adoption, routine workflows default to the core profile. The owner can ask for
full at any time or set `"profile": "full"` in `.rad-repo.json`.

## 1. Archaeology: inventory first, change nothing

In parallel batches:

```bash
git log --oneline -30
git log --format="%cs" -1          # last activity — the dormancy signal
git shortlog -sn --since="6 months ago"
git remote get-url origin
git branch -a && git worktree list
```

Inventory tracked file names, sizes, Markdown line counts, and recent Git activity
before reading document bodies. Classify the documentation set:

- **Small:** up to 50 candidate docs and 10,000 Markdown lines.
- **Medium:** up to 250 candidate docs and 50,000 Markdown lines.
- **Large:** above either medium limit.

Read small sets in one pass. Read medium sets in batches of at most 50 documents or
10,000 lines. Start with root instructions, README, likely authority docs, active
work, and recently changed docs. Keep a ledger of read and unread files. For a large
set, present the inventory and ask the owner to narrow the first pass.

Read the manifest, CI config, and at most 20 code entry points or 10,000 code lines
to identify the project. Expand only when a specific conflict needs more evidence.
Build an instruction map from root defaults to closest-scope overlays and preserve
overlays that carry materially different subtree commands, constraints, ownership,
or generated-code rules. Note candidate build, test, and run commands.

## 2. Review and verify the commands

Show the exact candidate commands and their sources. Ask once before running them.
Run only the approved build and test commands. Never run deploys, migrations, or
commands with external side effects. Record what works; a drafted AGENTS.md must
never claim a command you did not see pass. If a command fails, record it as
`documented but currently failing`. Do not fix it during adoption.

## 3. Draft L0–L2 from evidence

Draft — show the user before writing:

- **`AGENTS.md` (L0, ≤40 lines)** from `templates/AGENTS.md`: identity line from
  what the code actually does; verified commands from step 2; the doc-model block
  stamped verbatim from `templates/doc-model-block.md`; `deploy:` only if a target
  is evidenced. Existing AGENTS.md content is triaged, not clobbered: rules worth
  keeping go to the hard-rule slots (≤7 — if there are more, run the rules-audit
  classification from `repo-align` and propose promote/keep/demote), the rest to the
  step-4 triage. If another agent manual already exists, treat it as an existing doc
  to route, fold, or archive. Do not create a new agent manual.
- **`docs/handoff.md` (L1)** from the template: last completed from recent commits,
  next action from wherever the evidence points (or "unknown — owner to confirm"),
  an empty Deferred section.
- **`docs/decisions.md` (L2)** — only if the archaeology surfaced clearly settled
  decisions (in old ADRs, READMEs, commit messages). Append one dated line each,
  marked with their source. Don't invent decisions.

## 4. Triage every existing doc onto the shelf

For every doc included in the selected full batch, read it and propose exactly one
disposition. Use the same closed set as
`repo-align`: **route** (append content to decisions/ideas/lessons/design), **fold**
(merge into a shelf doc), **keep** (it already is a shelf doc — rename/move into
place with `git mv` if needed), **satellite** (no shelf slot but still useful — stays
in `docs/`, linked from the nearest core doc, per the shelf spec's satellite rule),
**archive** (`git mv` to `docs/archive/` + banner).

After any moves, grep the repo (code, CI, scripts, remaining docs) for the old paths
and fix every reference in the same pass — a triage that ships dead links isn't done.
Present the whole triage as a table, get the owner's call per row, then execute the
approved rows. Never silently delete anything.

An approved finite migration with a plan link, baseline, owner, acceptance criteria,
rollback strategy, and retirement trigger may become `docs/initiatives/<slug>.md`
from the initiative template. It is a temporary execution packet, not a second plan;
anything without that lifecycle metadata remains a routing candidate.

## 5. Ask only what evidence can't answer

Ask only unresolved questions that affect adoption, in one batch when possible. Use the host's question tool or plain text. Cover these when evidence has not settled them:

- **Active or dormant?** Dormant → stamp `Status: dormant — maintenance only` in
  AGENTS.md's identity line and skip fit-out extras that only matter for active work.
- The genuinely unanswerable: current goal still true? which of two conflicting old
  docs was right? deploy target? who else works here?

## 6. Fit-out

Run the fit-out step (`../../references/fit-out.md`): detect traits from the
code you just read, propose the equipment menu once, install what's approved, record
the fit-out line in AGENTS.md.

## 7. Check the installed contract

Run `../../scripts/repo-doctor.py . --json`. Show missing validation by path and the
exact drafted commands. Ask before `--approve`. Approval stays in local Git settings
and does not enter a commit.

## 8. Hand off

If the repo needs its plan reconstructed — no trustworthy `docs/plan.md`, unclear
state, half-built direction — **hand off to the planner rescue skill**: adopt built
the container and shelf (structure archaeology); rescue rebuilds intent and the
plan (content archaeology). If a usable plan exists, the planner replan skill
re-baselines it instead.

Name `rad-plan:rescue` or `rad-plan:replan` only when the need exists and that exact
skill appears in the current available-skill list. When it is unavailable, report
the planning need in plain language. Do not invoke it unless the owner asks or
accepts the suggestion.

## Output format

```text
Adopt:
Repo:               <name — what it is, from evidence>
Activity:           <active / dormant (last commit <date>)>
Profile:            <full first run / core first run; routine default core>
Doc scale:          <small / medium / large; read N of N>
Commands verified:  <build/test results — ran and passed / ran and failed / not found>
L0-L2 written:      <AGENTS.md, handoff.md, decisions.md (N entries) — after approval>
Doc triage:         <N docs: N routed, N folded, N kept, N archived, N skipped by owner>
Fit-out:            <installed items | declined | skipped (dormant)>
Next step:          <planner rescue | planner replan | none needed>
```

## What this skill does NOT do

- Never changes, formats, or "fixes" code — archaeology only.
- Never deletes a doc — every removal is a `git mv` to `docs/archive/`, confirmed.
- Never invents decisions, goals, or commands that evidence didn't show.
- Never writes `docs/prd.md` or `docs/plan.md` — that's the planner's lane
  (rescue/plan birth them from the owner's own answers).
- No commits, no pushes.

## References

- `../../references/shelf-spec.md` — the target model
- `../../references/fit-out.md` — trait table + menu procedure
- `../../templates/`: AGENTS.md skeleton, doc-model block, handoff stub
