# The shelf spec — the single source for the doc model

This file is THE contract. Every skill in this plugin, rad-plan, rad-brainstormer,
and any other tool that writes docs in a managed repo conforms to what's written here.
Skills reference this file; they never restate it. The repo itself carries a ~10-line
summary (the doc-model block in `AGENTS.md`, stamped by `/rad-repo:repo-init`)
so the contract travels with the repo across machines and harnesses.

The idea in one sentence: **a closed system** — every kind of information has exactly
one home, every home has exactly one update trigger, and nothing depends on anyone
remembering anything.

## The context stack

Five layers, ordered by how often they're loaded. L0 + L1 together are ~1.5–2k tokens
(a token is roughly ¾ of a word) — cheap enough to inject into every session.

| Layer | File(s) | Role | Size budget | Loaded |
|---|---|---|---|---|
| L0 | root + scoped `AGENTS.md` | root defaults plus material subtree overlays | root ≤40 lines; scoped concise | `startup`, then by target path |
| L1 | `docs/handoff.md` | state: where we are, what's next, the `## Deferred — do not re-raise` ledger | ≤60 lines | `startup`, `wrapup`, `ship` |
| L2 | `docs/decisions.md` | settled decisions, append-only | 1 line each | checked before re-litigating |
| L3 | `docs/prd.md`, `docs/plan.md`, `docs/initiatives/*.md` | direction plus approved finite migrations | none | when planning or executing that initiative |
| L4 | `docs/archive/` | everything superseded | unbounded | never by default |

**Convention:** the root `AGENTS.md` carries repository-wide defaults. A scoped
`AGENTS.md` is allowed only where a subtree has materially different commands,
constraints, ownership, or generated-code rules; the closest file wins and must not
duplicate root facts. Root budgets are enforced by the mechanical scans (`repo-align`
routes overflow down the stack — an L0 rule
that's really a lesson goes to `docs/lessons.md`, durable handoff content goes
to `plan.md`, and so on).

## Workflow profiles

`core` is the default. It uses scoped instructions, one handoff, the executable
contract, startup, wrapup, and ship. Deeper shelf files still remain valid and are
read when the task needs them.

`full` makes deeper document reconcile and alignment the normal default. A first
`adopt` recommends one full pass, then routine work returns to core unless the owner
sets `"profile": "full"` in `.rad-repo.json` or asks for full.

Profiles change read depth. They do not create a second document model.

## The shelf

A **closed** set of reference docs. No doc exists until its trigger fires; every doc
declares who updates it and when. Anything that isn't one of these kinds goes to
`docs/archive/`, lives as a **satellite** (below), or doesn't get written.

| File | Holds | Created when | Updated when / by | Freshness check |
|---|---|---|---|---|
| `docs/decisions.md` | settled choices + one-line why; existing ADR systems can remain linked satellites | first decision | anyone appends; never edited | append-only = never stale |
| `docs/ideas.md` | ideas, pivots, cut features — the parking lot | first idea | anyone appends; `/rad-plan:replan` annotates rejections | consumed at `/rad-plan:replan` |
| `docs/lessons.md` | mistakes worth remembering; doubles as a learning journal | first lesson | wrapup question appends | append-only |
| `docs/design.md` | **sole source of the design system**: brand, UI tokens, layout/visual specs | UI work begins | when a visual/design decision is settled — recorded here, not in decisions.md | align cross-check |
| `docs/architecture.md` | how the system hangs together (1 page + diagram) | repo gains >1 moving part | when a decisions.md entry touches structure; align nudges | align cross-check |
| `docs/api.md` | endpoint inventory | repo exposes an API **now** (not "Later") | route change | **mechanical**: align diffs routes in code vs the doc |
| `docs/handoff.md` | state + deferred ledger | repo-init | refreshed by wrapup/ship only | ≤3 commits behind in startup trust report |
| `docs/prd.md` | goal + releases, owner's voice, plain language | `/rad-plan:plan` interview | owner, at replan boundaries | reviewed at replan |
| `docs/plan.md` | milestones + tasks | `/rad-plan:plan` | planner only (`/plan`, `/replan`) | re-baselined per milestone |

**Transient spec docs** (`docs/<date>-*-spec.md` / `docs/<date>-*-design.md`, written
by rad-brainstormer) are the one sanctioned pass-through: each names
`/rad-plan:plan` as its consumer in its header and is archived once planning has
consumed it. They are not shelf docs — a spec still sitting under `docs/` after its
plan exists is a loose end.

**Satellite docs.** Domain reference docs with no shelf slot (a test runbook, a
data-format contract, a domain model) stay in `docs/` as satellites: each is linked
from the nearest core doc (architecture.md, api.md, or AGENTS.md's doc-model table)
so nothing is orphaned. Satellites are legitimate residents, not loose ends — a loose
end is a doc *nothing links to*.

**Conformance without loss.** The shelf's formats govern *new* entries, not existing
knowledge. When adopt/align meets content richer than a shelf format (e.g. a detailed
symptom/cause/fix lessons file), the shelf file becomes the append surface going
forward and the rich original stays live as a linked satellite (the
`docs/lessons-detail.md` pattern) — never compressed to one-liners, never archived
while still useful. Mapping names and locations is conformance; flattening content is
loss.

## File formats

**decisions.md** — `# Decisions` header, then append-only one-line dated entries.
Never edit an existing line; to overturn a decision, append a new entry (and ask the
owner first — see the interaction contract).

```
# Decisions

- 2026-06-20 · thumbnails: square crops in grids, true aspect ratio in lightbox (settled after 3 sessions)
- 2026-06-07 · "push to main" always means push to origin/main
```

New durable entries use compact typed metadata so recall can filter and check them:

```text
- <date> · [<DEC-or-LES-ID>] [scope: <repo or path>] [status: active] [source: <commit, test, issue, or authority doc>] [verified: <date or unverified>] [stale-after: <date or never>] [supersedes: <ID or none>] <fact>
```

Use `DEC-YYYYMMDD-NN` for decisions and `LES-YYYYMMDD-NN` for lessons. Status is
`active`, `superseded`, or `deprecated`. Append a new record to supersede an old
one; never edit the old line. Existing untyped lines remain valid and searchable,
and recall reports them as legacy evidence. Markdown is authoritative. No generated
index or database is part of the core model.

A paragraph of context is allowed for expensive decisions — same file, still
append-only, no separate directory. Settled *visual/design* decisions go to
`docs/design.md` instead; decisions.md may cross-reference design.md but never
duplicates its content.

**ideas.md** — `# Ideas` header, append-only one-line dated entries. When
`/rad-plan:replan` rejects a parked idea it appends a `rejected: <why>` line under
the entry — the idea stays on record so it doesn't get re-proposed.

```
# Ideas

- 2026-06-19 · offline mode for the field app
  - rejected: 2026-06-28 — sync complexity outweighs demand; revisit if users ask
```

**lessons.md** — `# Lessons` header, append-only one-line dated entries: what bit,
and the fix or rule that prevents it.

```
# Lessons

- 2026-06-12 · Coolify healthcheck path must match the app's route — a 404 healthcheck loops the deploy forever
```

**handoff.md** is a refreshed snapshot, never a session log. Its normal target is
60 lines: Last completed / Current focus / Next action / Validation / Watchouts,
plus the deferred ledger. Preserve facts required for a cold resume. Link long
execution detail from an active initiative when one exists.

```
## Deferred — do not re-raise
- 14 unassigned drafts (owner aware; wake: when count > 30)
- <item> (wake: <condition or never>)
```

Startup, wrapup, ship, and repo-align treat this section as a suppression filter: an item
listed here is not re-raised until its wake condition (the condition after `wake:`)
is met. `wake: never` means never.

**prd.md** — headings: `Goal`, `Users & primary workflow`, `Releases` (Now / Next /
Later), `Non-goals`, `Acceptance criteria`. Owner's voice, plain language, present
tense.

**plan.md** — `Objective` (carrying an `**End goal:**` line that echoes the PRD
Goal), a `Milestones` table whose columns are `# | Milestone | Ships | Key
artifacts`, and `Tasks` (T1…). Written only by the planner.

**initiatives/*.md** — an approved, finite migration or cross-cutting change that
would overload plan.md. Each file uses `templates/initiative.md`: frontmatter carries
title, owner, active status, baseline commit, plan link, retirement condition, and
archive destination; the body carries acceptance criteria and rollback strategy.
`docs/plan.md` links it. Completion retires it to `docs/archive/`; initiatives are
never permanent topic docs or an alternate roadmap.

**Evidence-tracked current-system docs (optional)** — `architecture.md`, `api.md`, or
another managed doc may use YAML frontmatter with a `tracks:` list of repository
paths. `doc-freshness.py` then reports missing paths and commits touching those paths
since the doc's last commit. This is drift evidence, not semantic proof.

## The vocabulary ladder

One set of names for units of work, used everywhere:

| Term | Means | Lives in | Count |
|---|---|---|---|
| **Goal** | end state of the product | prd.md | 1 per project |
| **Release** | horizon: Now / Next / Later (MVP, V1…) | prd.md + plan.md | 2–4 |
| **Milestone** | shippable chunk within a release (M1, M2…) | plan.md | 3–8 per release |
| **Task** | one work item, ideally one session (T1…) | plan.md | 2–5 per milestone (the planner aims for 2–3; over 5 is a split candidate) |

**Vocabulary profiles** — the default profile reports synonyms such as *phase,
slice, sprint, epic, stage*, and tracked *step* as advisory findings in managed docs.
Repositories configure `.rad-repo.json` to set `vocabulary.mode` to
`advisory`, `strict`, or `off`; `vocabulary.scope` can be `all` or `headings`, and
`banned_terms` can replace the default list. Strict mode makes findings blocking.
A ladder term in the wrong doc is evaluated under the same mode: the PRD speaks only
Goal/Release; plan.md speaks only Milestone/Task.
Brainstorm output inside a repo uses none of the ladder terms (vocabulary quarantine
— sequencing belongs to `/rad-plan:plan` alone).

## One writer per file

One format authority for everything (this file), exactly one writing authority per
file:

| File | Format authority | Content written by | Everyone else |
|---|---|---|---|
| AGENTS.md | repo-manager | repo-manager (operational); planner *proposes* the stack block, owner applies | proposes |
| prd.md | repo-manager (headings) | owner, via the planner interview | proposes edits |
| plan.md | repo-manager (vocabulary) | planner (`/plan`, `/replan`) only | reads |
| initiatives/*.md | repo-manager | initiative owner; align verifies lifecycle metadata | reads |
| decisions.md / ideas.md / lessons.md | repo-manager | anyone **appends**; no one edits | — |
| design.md | repo-manager | agent proposes, owner approves; sole design-system authority | reads, never duplicates |
| handoff.md | repo-manager | wrapup/ship only | reads |
| architecture.md / api.md | repo-manager | planner seeds; decisions/align maintain | proposes |

Each tool polices *format* in the other's lane, never *substance*: align lints
plan.md's vocabulary and stamps but flags content issues to `/rad-plan:replan`
rather than fixing them. rad-brainstormer never writes `docs/design.md`; it routes
rejected/parked ideas to `docs/ideas.md` with a one-line why.

## The enforcement ladder

Instructions come in four strengths. Most systems fail by putting everything at the
weakest level.

| Level | Mechanism | Ignorable? | Capacity |
|---|---|---|---|
| 1 | **Mechanical check** — code measures it, the agent doesn't guess | no | targeted validators |
| 2 | **Injected rule** — always in context (L0) | rarely | **≤7 hard rules** |
| 3 | **Skill** — loaded when invoked | if not invoked | the commands |
| 4 | **Reference doc** — read on demand | easily | everything else |

**Promotion rule:** an instruction violated or repeated twice gets promoted one level
(chat -> L0 rule; L0 rule -> mechanical check when it can be measured).
**Demotion:** a rule never violated in months moves down to a referenced
guardrails file or the archive.

**Rules audit** (a `repo-align` capability, run on request or when AGENTS.md exceeds
its 40-line budget): classify each existing rule by evidence — violated + mechanical
-> promote to a validator; violated + judgment -> keep in the 7 slots; dormant -> demote to a
referenced guardrails file. Propose-only; the owner decides every move.

## The interaction contract

Stamped into every repo's L0 so every harness inherits the same personality:

1. **Hard gates** — block-and-ask *only* for irreversible or expensive actions: prod
   data, auth, payments, deletes, publishing, plus the owner's protected-changes
   list. Nothing else blocks.
2. **Challenge once, then commit** — on any pivot or risky choice (including
   reversing the owner's own plan), give one honest, short assessment: what changes,
   what it costs or orphans, a recommendation. If the owner confirms, it becomes a
   decision: log it to decisions.md, execute fully, never relitigate, no hedging.
   Real opinion before the decision; total commitment after it. No reflexive praise
   before it, either.
3. **The pressure valve** — mid-session ideas and pivots append to `ideas.md` in
   seconds, block nothing, and get a fair hearing at the next `/rad-plan:replan`.
   Pivots are cheap *because* they're recorded.
4. **Optional skill routing:** name a RAD Plan skill only when current evidence needs
   that exact workflow and the skill appears in the current available-skill list.
   When it is unavailable, report the planning need in plain language. Never invoke
   it from a suggestion unless the owner asks for it or accepts the suggestion.

Formula: **freedom to decide, obligation to record.**

## Size budgets & trust thresholds

| Check | Budget / threshold | Checked by |
|---|---|---|
| AGENTS.md (L0) | ≤40 lines | `repo-scan.py` (every session) |
| handoff.md (L1) | ≤60 lines | `repo-scan.py` (every session) |
| handoff commits-behind | 0–3 green · 4–10 yellow (nudge a quick wrapup) · >10 red (recommend align first) | `doc-freshness.py` trust report |
| prd/plan commits-behind | informational — reviewed at replan boundaries | `doc-freshness.py` trust report |
| decisions/ideas/lessons | append-only — never stale | — |

"Commits-behind" = commits on HEAD since the doc's last modifying commit. Mechanical,
measured by code, not by anyone's memory.

## Domain authority — resolving contradictions

Authority is typed by subject rather than forced into one global ladder:

| Domain | Authority | What it governs |
|---|---|---|
| Current instruction | owner's instruction in the current session | immediate intent; cannot silently rewrite durable constraints |
| Repository constraints | applicable `AGENTS.md`, then decisions/ADRs | commands, safety, provider/import boundaries, settled constraints |
| Product intent | `docs/prd.md` | users, behavior, non-goals, acceptance criteria |
| Current system | `docs/architecture.md`, `docs/api.md`, then code | implemented topology and interfaces; code evidence wins stale prose |
| Approved change | `docs/plan.md`, linked `docs/initiatives/*.md` | future execution and migration sequence, not current-state claims |
| Visual direction | `docs/design.md` | brand, UI, and visual-system decisions |
| Session state | `docs/handoff.md` | resume snapshot only |
| Historical context | `docs/archive/*` | never current authority |

`docs/decisions.md` and ADRs constrain every domain they explicitly address. A plan
cannot override a locked ADR, and an architecture document cannot claim unimplemented
plan work is current. The conflicting doc is brought into line as a **drafted** edit
under per-edit confirmation — never silently. If the domain authorities still conflict,
or code and docs disagree without a settled decision, stop and surface the conflict.

## Superseded content & retired terminology

- **Superseded banner.** Overtaken content kept in place for context gets a top
  banner: `> **Superseded YYYY-MM-DD:** replaced by <doc/section> — kept for
  context.` Distinct from the archive banner (which marks a file *moved* to
  `docs/archive/`). No active doc carries obsolete direction without one of the two.
- **Retired terminology (optional).** A repo may keep a `## Retired terminology`
  table in AGENTS.md mapping dead terms to replacements; `repo-align` greps managed
  docs for stray uses. Project-supplied — no terms are hardcoded. Vocabulary-profile
  synonym checks use the same sweep mechanism with configurable terms and severity.

## Executable repository contract

Applicable `AGENTS.md` files and optional `.rad-repo.json` define validation
commands. Root instructions are defaults; closest-scope overlays add only materially
different commands or constraints. `repo_contract.py` resolves this map for changed
paths. `pre_ship.py` inspects staged Git blobs and blocks high-confidence secret patterns, protected paths,
unexpected generated output, oversized files, missing/failed validation, and
unreviewed contract changes. `repo-doctor.py` shows each command and source. Command
approval is stored in local Git settings and expires when the command set changes.
Heuristic doc scans do not substitute for code checks.

## Non-goals

No status/roadmap/general implementation-plan/per-feature status docs. The controlled
initiative exception above is only for an approved finite migration. No `docs/inbox/`
staging tier. RAD Repo does not create a second ADR system; an established ADR folder
can remain as a linked satellite. No doc scaffolding "for later"; a shelf doc exists
only after its trigger fires. No dashboards or per-session logs. No writing durable
content without confirmation. Every required write stays under a minute or it won't
survive contact with a real Tuesday.
