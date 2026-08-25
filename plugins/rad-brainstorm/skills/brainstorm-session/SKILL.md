---
name: brainstorm-session
description: Use when the user explicitly wants to brainstorm, generate or expand ideas, explore alternatives, use a named creative method, or work from a blank or vague starting point. Do not use for a direct answer, root-cause interview, idea ranking, technical design, or implementation planning.
---

# Brainstorm Session

Help the user develop and select ideas while keeping ownership visible. Do not write code, scaffold a project, start implementation planning, or commit files.

Resolve the plugin root as the directory two levels above this `SKILL.md`. Read `references/facilitation-principles.md`. Read one other reference only when its step requires it.

## Companion-skill rule

Name an exact RAD Plan, RAD Repo, or RAD Council skill only when the exact skill appears in the current available-skill list, current evidence needs it, and it would add clear value. Ask whether the user accepts the companion. Never invoke it until the user asks or accepts. If the exact skill is absent or the user declines, continue the current Brainstorm workflow standalone. Public namespaces are `rad-plan:*`, `rad-repo:*`, and `rad-council:*`.

## 1. Set the session

When intent is unclear, ask: "Do you want a quick take or a brainstorm session?"

Choose the tier:

- **Quick:** default for a bounded topic. Use one method, aim for three strong options and one recommendation, use no subagents, create no file unless asked, and aim to finish within five user turns.
- **Full:** use for an open, uncertain, or high-stakes topic. It may add research, a focused challenge, and one optional checkpoint.

Choose the working mode when unclear:

- **Facilitator:** the user generates and Codex guides. Default.
- **Partner:** the user starts, then both contribute.
- **Generator:** Codex gives a small first set for the user to reject or change.

State the tier and mode.

## 2. Frame the target

Settle these facts before broad generation:

- goal;
- primary user or affected person;
- success signal;
- hard constraint.

Infer facts already clear from the request. Ask one question per turn for a missing fact that could change the idea set. In quick mode, ask only the highest-value missing question.

For software topics, inspect relevant repository docs, code, tests, and recent Git history before proposing designs. Read any user-provided research or design evidence from the path or content the user names. Keep this phase read-only and preserve the stated paths and source labels.

Route a complete idea set that only needs ranking to `rad-brainstorm:idea-evaluation`.

## 3. Capture the user's starting ideas

In facilitator and partner modes, ask what the user has considered before offering ideas. Include half-formed ideas and rejected directions. Record every idea with a stable ID and source:

- `I1 [user]`
- `I2 [AI]`
- `I3 [research]`

Build from the user's terms and constraints. If the user is stuck, use `references/creative-unblocking.md`. In generator mode, state that AI ideas will set the first anchors and label them `[AI]`.

## 4. Add research with consent

Treat user-provided research or design evidence as supplied evidence. Keep its exact path or link, claims, and source label attached to the related idea or constraint. Offer outside research only when a current market, rule, technology, or unfamiliar fact could change the idea set. State the exact research question and value, then ask permission.

If accepted, use `references/subagent-prompts/domain-research.md`. Use one bounded, read-only subagent when available, or perform the same bounded work directly. Require JSON-first output. Run schema validation with `scripts/validate-json.py` and `domain-research.schema.json`. Re-prompt once on failure. Cite sources and add useful findings as `[research]` ideas or constraints.

## 5. Generate, then check diversity

Announce generation. Keep evaluation out of this phase. Read the selected card in `references/methodology-catalog.md`.

Use one core method first. Add another method in a full session only when it is likely to produce a different mechanism. Keep a running idea list with IDs and source labels.

After generation:

1. Group ideas by the underlying way they create value or solve the problem.
2. Show repeated mechanisms and any missing mechanism.
3. If the set is narrow, run one small pass from distinct ordinary stakeholder views or a different method.
4. For ten or more ideas, or clear duplicates, cluster exact and near duplicates. Preserve the user's wording, original IDs, and source labels. Ask before merging ideas that differ in audience, mechanism, channel, cost, or risk.

## 6. Evaluate separately

Announce the phase change. Read only the selected section in `references/evaluation-frameworks.md`. The user scores or ranks first. Share the AI view after the user's scores, then discuss material differences.

For a high-stakes choice, offer one bounded idea challenge only when it could change the result. If accepted, use `references/subagent-prompts/idea-challenge.md`, then run schema validation with `idea-challenge.schema.json`. Keep the challenge read-only and within the current candidates.

## 7. Deliver one stable result

Use the result contract in `references/session-output.md`. Include:

- recommendation and strong alternative;
- original idea sources and mechanism groups;
- parked or rejected ideas with short reasons;
- riskiest assumption;
- cheapest proof, pass threshold, and stop signal;
- next useful decision or action.

Offer a Mermaid summary only when it makes three or more relationships easier to understand. Keep the text result as the source of truth.

For a chosen software approach that needs technical design, offer `rad-brainstorm:software-design`. Do not start it without acceptance.

## 8. Save or checkpoint only with approval

For a full session at risk of interruption, offer the checkpoint contract in `references/session-output.md`. Get a destination before writing. Quick sessions remain file-free unless the user asks.

For the final result, offer conversation only, one dated Markdown file in a chosen personal folder, or `docs/YYYY-MM-DD-<topic>-spec.md` in the current project. When the user names a repository path, repeat the exact repository path and ask for approval before writing. Write only after approval and do not silently substitute a destination. Mark a project file as transient when a later planning workflow will consume it. Never write to `docs/design.md`. Never auto-commit.

## 9. Close

Ask whether the result meets the user's need. Get clear approval before suggesting another workflow. Name a companion skill only under the companion-skill rule. Stop before implementation planning or code.
