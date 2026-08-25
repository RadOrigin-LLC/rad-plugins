---
name: software-design
description: Use when the user has chosen what software to build and wants a reviewable technical design or design spec before implementation planning. Do not use for open ideation, code implementation, project scaffolding, or brand and visual design.
---

# Software Design

Turn one chosen software approach into a clear design spec. Do not write code, scaffold a project, start implementation planning, or auto-commit. Stop before implementation planning or code.

## Companion-skill rule

Name an exact RAD Plan or RAD Repo skill only when the exact skill appears in the current available-skill list, current evidence needs it, and it would add clear value. Ask whether the user accepts the companion. Never invoke it until the user asks or accepts. If the exact skill is absent or the user declines, continue the current software-design workflow standalone.

## 1. Confirm the chosen approach

Restate the selected approach, goal, primary user, success signal, and hard constraint. Ask one question per turn for missing facts that affect the design.

If the product direction remains open, route to `rad-brainstorm:brainstorm-session`.

## 2. Read project evidence

For an existing repository, inspect relevant docs, code, tests, configuration, and recent Git history. Read `docs/design.md` when it exists and treat it as the brand and interface direction. Read any user-provided research or design evidence from the path or content the user names. Keep the exact path or link and source label with the affected design decision. Mark conflicts and unknowns instead of inventing support. Never overwrite it. Keep this phase read-only.

## 3. Settle design decisions

Cover only decisions that affect the selected design:

- scope and exclusions;
- system boundaries;
- component duties and interfaces;
- data model and flow;
- API behavior when relevant;
- errors and recovery;
- security, privacy, performance, and accessibility when relevant;
- focused tests;
- migration and deployment when relevant.

Follow existing repository patterns unless evidence shows that a pattern blocks the chosen result. Give each unit one clear purpose, a defined interface, known dependencies, and a focused test. Add no abstraction without a current need.

## 4. Approve sections

Present one section at a time:

1. Architecture overview
2. Components and interfaces
3. Data model and flow
4. API behavior when needed
5. Errors and recovery
6. Quality and tests
7. Migration and deployment when needed

Wait for approval or correction before the next section.

Offer a Mermaid diagram only when it makes component, data-flow, or state relationships easier to understand. Keep the written design authoritative.

## 5. Deliver one spec

Ask where to save it. If the user names a repository path, repeat the exact repository path and ask for approval before writing. Write only after approval. Suggest `docs/YYYY-MM-DD-<topic>-spec.md` in a current project or a dated Markdown file in a personal folder before a repository exists. The user may keep it in the conversation.

Include the selected approach, scope, architecture, components, interfaces, data flow, errors, recovery, relevant quality needs, focused tests, migration or deployment details, rejected options, and confirmed deferrals. Use clear deferrals with reasons. Do not use TBD or TODO.

Mark an in-project spec as transient when a planning workflow will consume it. Never write to `docs/design.md`. If `docs/ideas.md` exists, offer to append parked options and wait for approval.

## 6. Review the spec

Run an inline scan for placeholders, contradictions, ambiguity, scope growth, missing recovery behavior, and unneeded complexity. Fix confirmed issues.

Then use `references/subagent-prompts/spec-review.md` for one bounded, read-only review when subagents are available. Require JSON-first output and run schema validation with `scripts/validate-json.py` and `spec-review.schema.json`. When subagents are unavailable, perform the same checks directly. A second review requires the user's request.

## 7. Close

Ask the user to approve the spec. Do not begin implementation planning or coding. Name `rad-plan:plan` only under the companion-skill rule. Otherwise describe the next step without naming a plugin.
