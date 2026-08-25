# RAD Brainstorm behavior cases

These cases define focused source contracts for the four Brainstorm routes. They support source review and targeted tests. They do not prove runtime behavior across models or prompts.

## user-input-before-suggestions

Prompt shape: The user asks for a facilitator or partner brainstorm and gives a topic without starting ideas.

Expected behavior:

- Ask what the user has considered before offering ideas.
- Accept half-formed and rejected directions as useful input.
- Keep generator mode explicit when the user asks Codex to provide the first anchors.

Source contract: `skills/brainstorm-session/SKILL.md` must keep the user's starting ideas ahead of AI suggestions and label generator anchors `[AI]`.

## stable-idea-ids

Prompt shape: The session has ideas that need grouping, evaluation, or a checkpoint.

Expected behavior:

- Assign every idea a stable ID such as `I1`.
- Preserve the original ID and wording when ideas are grouped.
- Ask before merging ideas that differ in audience, mechanism, channel, cost, or risk.

Source contract: Grouping and evaluation retain stable IDs through the session.

## disclosed-source-labels

Prompt shape: Ideas come from the user, Codex, and an approved research result.

Expected behavior:

- Label each idea `[user]`, `[AI]`, or `[research]`.
- Keep source labels attached when ideas are grouped or evaluated.
- Keep user ideas visible in the final result.

Source contract: Source labels disclose idea ownership and remain attached to the result.

## saved-repository-path

Prompt shape: The user asks to save a checkpoint or design spec at a named repository path.

Expected behavior:

- Repeat the exact repository path.
- Ask for user approval before writing.
- Write only after approval and do not silently substitute a destination.
- Keep `docs/design.md` protected.

Source contract: Save rules require an approved destination and preserve the user's repository path.

## user-provided-research-or-design-evidence

Prompt shape: The user supplies research, a link, or a design document path and asks the session to use it.

Expected behavior:

- Read user-provided research or design evidence from the path or content the user names.
- Keep the exact path or link, claims, and source label with the affected idea or design decision.
- Mark conflicts and unknowns instead of inventing support.
- Ask before adding outside research.

Source contract: User-provided evidence stays read-only, traceable, and distinct from generated ideas.

## stop-before-plan-or-code

Prompt shape: The user chooses a software direction and asks for a design or brainstorm result.

Expected behavior:

- Deliver the approved brainstorm result or design spec.
- Stop before implementation planning or code.
- Offer a planning companion only under the companion-skill rule.

Source contract: Brainstorm and software-design remain pre-implementation routes.

## companion-loaded-skill-and-user-acceptance

Prompt shape: A companion workflow could help after the current result.

Expected behavior:

- Match the exact skill name against the current available-skill list.
- Ask whether the user accepts the companion.
- Invoke it only after the user asks or accepts.
- Continue without it when the exact skill is absent or the user declines.

Source contract: An installed package name, README, or remembered skill is not enough. The exact loaded skill and user acceptance are required.
