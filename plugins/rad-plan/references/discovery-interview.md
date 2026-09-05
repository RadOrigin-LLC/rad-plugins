# Discovery interview

Use repository evidence and the user's request to establish scope and acceptance. Ask about material gaps; keep unresolved choices visible.

## The eight coverage areas

Every area must end in one of two states: **settled** (you can state the answer in one
sentence) or **explicitly unknown** (captured as an assumption or risk — never silently
skipped).

| # | Area | What "settled" looks like |
|---|---|---|
| 1 | **End goal** | One sentence describing the truly-done state, 6–12 months out — what makes the user say "this is what I set out to build." Not the MVP; the destination. |
| 2 | **Users & core workflow** | Who uses it, and the ONE workflow that must work end-to-end. |
| 3 | **MVP** | The smallest version the user would put in front of a real person. Extracted by question ("what's the first thing you want to see working?") — never assumed. |
| 4 | **Success criteria** | Observable signs it's working — not feelings ("it feels fast") but checkable facts ("a link shortens in under a second"). |
| 5 | **Hard constraints** | Money, time, skills, platform/devices, accounts and services already paid for or ruled out. |
| 6 | **Existing assets** | Repo, designs, data, domain names, prior attempts — anything that exists already. |
| 7 | **Deliberate exclusions** | Scope exclusions that matter to this project. Ask when an unresolved boundary would change the plan; do not invent exclusions to meet a count. |
| 8 | **Danger zones** | Does this touch auth, payments, personal data, or external integrations? These change planning rigor (extra checkpoints, stop conditions, security tasks). |

## Protocol

Use the coverage table to find gaps, not to force an interview. Fill answers from the request, approved product documents, and relevant repository evidence. Treat settled decisions as inputs unless current evidence contradicts them.

Use the depth chosen under the `plan` skill. For quick planning, ask at most one batch of five unresolved questions. For full planning, use up to three rounds, stopping as soon as scope and acceptance are clear. Use the host's question tool when helpful, or concise plain text.

Ask only about choices that affect the plan. Summarize a complex or disputed scope for correction; do not require repeated mirror-back or confirmation of already approved facts. Record unresolved points as assumptions or risks. Never assume permission for data loss, production access, or expanded scope.

## Closing the interview

Proceed with the settled scope. The plan remains DRAFT until owner approval.

**2. The PRD gap check.** Run this on the full path, or on the quick path only when
the owner asks. If `docs/prd.md` is missing, a skeleton, or contradicts
what the interview established: offer to draft it — *"You've just told me everything
a PRD needs. Want me to write it up? You'll confirm each section."* On yes, draft each
PRD section (Goal, Users & primary workflow, Releases — Now / Next / Later, Non-goals,
Acceptance criteria; the repo's AGENTS.md doc-model block overrides these headings
when present) **from the user's own interview answers** — no invention — and confirm
per section (apply / reword / skip) before writing the file. The
user owns the decision; the planner does the typing. On no, plan anyway and note the
gap in Key assumptions.

## Interview → output mapping

| Interview area | Lands in |
|---|---|
| End goal | `## Objective` (**End goal** line) + `## Release map` (Later) |
| Users & workflow | PRD draft; plan `## Objective` |
| MVP | `## Release map` (Now) — the scope of this plan's milestones |
| Success criteria | PRD Acceptance criteria; plan `## Validation` |
| Constraints | `## Key assumptions` + `## Scope` |
| Existing assets | build sequencing, plan step 3 (don't rebuild what exists) |
| Deliberate exclusions | `## Scope` non-goals; PRD Non-goals |
| Danger zones | `## Stop conditions`, checkpoints, security tasks |
