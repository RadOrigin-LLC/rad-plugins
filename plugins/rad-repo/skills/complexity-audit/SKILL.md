---
name: complexity-audit
description: Review code maintenance hotspots read-only when the user requests a complexity or technical-debt audit.
---

# Complexity Audit

Find the few code areas that deserve maintenance review now.

## 1. Run the common scan

Resolve the script relative to this skill file.

```powershell
python ../../scripts/code-hotspots.py . --months 12 --limit 10 --json
```

Use `python3` when `python` is unavailable. Change the time window only when repository history or the user's request gives a clear reason.

The priority index combines recent change count and file size. It ranks review value. A human decides code quality.

## 2. Inspect the highest-ranked areas

Read the top files in small batches. For each file:

- Find the functions or classes that contain most of the branching, nesting, or repeated logic.
- Check nearby tests and callers.
- Separate generated code, migrations, stable parsers, and other justified complexity.
- State when symbol-level evidence is unavailable.

Do not read the full repository. Start with the top five. Expand to ten only when the next findings add useful evidence.

## 3. Use existing quality signals

The scan reports tools and quality files that are already present. Show any extra read-only command before running it. Use existing Sonar, Code Climate, Qlty, Lizard, Radon, ESLint, Ruff, Clippy, Go lint, .NET analyzer, or coverage output when available.

Do not install a tool unless the user asks. Do not create a custom language parser.

## 4. Report

For each supported finding, up to ten, give:

1. File and symbol, when known.
2. Churn, size, and quality evidence.
3. Why review is useful now.
4. One small simplification option.
5. Change risk.
6. Tests needed before a change.
7. Confidence: high, medium, or low.

Prioritize the strongest review targets. Do not invent findings to fill a quota. Keep raw scan output out of repository docs unless the user asks to save it.

## Boundaries

- Read-only by default.
- No automatic refactor.
- No repository-wide quality score.
- No baseline file unless the user asks.
- No complexity gate in startup, wrapup, ship, or normal CI.
