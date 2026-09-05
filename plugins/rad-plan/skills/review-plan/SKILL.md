---
name: review-plan
description: Review an existing implementation plan for execution readiness with mechanical lint and independent risk review.
---

# Review Plan

Audit an existing plan in two layers:

1. Mechanical checks with `scripts/plan-lint.py`.
2. Judgment checks with the risk assessor.

Do not write durable documents. Edit the plan only after the owner accepts specific fixes.

## Resolve paths

Resolve the plugin root as two directories above this skill directory.

Detect the plan in this order unless the user supplied a path:

1. `docs/plan.md`
2. `docs/planning/current-execution.md`
3. `docs/planning/current.md`
4. `PLAN.md`

Read the plan completely. If none exists, explain that a plan is needed and suggest the `plan` skill.

## Harness support

Use the host's available subagent tool for independent reviewers; role names such as `risk_assessor` describe the assignment, not a required model or tool name. If independent review is unavailable, complete the mechanical checks and draft, report the missing review, and leave approval pending. Do not label self-review as independent review.

## 1. Mechanical review

Run against the detected path:

```bash
python <plugin-root>/scripts/plan-lint.py <plan-path> --json
```

The linter checks the implemented contract: sections, six task fields, duplicate sections and IDs, dependencies, outcome links, 7.1 path labels, vague proof, live-task warning, and unsafe rollback command forms.

Do not send deterministic findings to a model for debate.

## 2. Judgment review

Consult `references/anti-patterns.md` for planning weaknesses, `references/failure-state-template.md` for recovery, `references/tdd-constraints.md` for validation, and `references/context-management.md` for work spanning sessions. Load only sections relevant to this plan.

Read relevant approved product or architecture documents when present. Pass them as read-only supporting context.

Dispatch one bounded, read-only `risk_assessor` using `references/subagent-prompts/risk-assessment.md`. Pass the detected plan path, mechanical findings, and supporting context. Require JSON-only output and no file edits.

Validate the response:

```bash
python <plugin-root>/scripts/validate-json.py \
  <plugin-root>/references/subagent-prompts/risk-assessment.schema.json - --extract-from-markdown
```

Re-prompt once on schema failure. Review only live work. `## Shipped` is history.

## 3. Report

Use this shape:

```markdown
# Plan Review Report

**Plan:** [path]
**Mechanical lint:** [PASS or issue count]
**Risk verdict:** [APPROVE, REVISE, or RETHINK]
**Recommendation:** [next action]

## Mechanical findings
[Deterministic findings]

## Blocking risks
[CRITICAL and HIGH judgment findings]

## Improvements
[MEDIUM and LOW findings]

## Strong parts
[Evidence-backed positive observations]
```

Check whether:

- outcomes are observable and each has tasks and final proof;
- task paths match the repository or are marked new;
- the hardest unknown appears early;
- validation proves the outcome and covers risk-based failures;
- rollback restores real state without erasing unrelated work;
- every milestone has a checkpoint;
- a milestone exceeds five tasks or the live plan exceeds 20 tasks;
- the plan conflicts with approved product, architecture, or repository facts.

## 4. Offer fixes

For REVISE, offer the smallest exact plan edits. Explain each change before applying it. Modify only the plan after owner approval, then run the linter once.

For RETHINK, explain the product, scope, or architecture choice that must change. Name a `rad-brainstorm:*` skill only when the exact skill is available, the need is real, and it would add value. Never invoke it without owner acceptance.

## Boundaries

- Do not implement code.
- Do not edit a PRD, design, architecture document, or repository instruction.
- Do not rerun iterative review loops.
- Do not treat coarse Next or Later entries as defects.
