---
name: recall
description: Use when the user asks what the repository decided, what past lesson applies, why a constraint exists, whether an old choice is still active, or asks to recall project memory for a task or path. Runs bounded, read-only keyword recall over docs/decisions.md and docs/lessons.md, returns at most five source-linked records, and marks stale, unverified, superseded, or conflicting facts. It does not write or promote memory.
---

# Recall

Find the few durable repository records that matter to the current question.

## Procedure

1. Form one short query from the user's subject. Add `--path <repository-path>` when the question concerns a file, package, or component.
2. Run the bundled tool relative to this skill file:

   ```powershell
   python ../../scripts/memory-recall.py . "<query>" --path "<path>" --limit 5 --json
   ```

   Omit `--path` for a repository-wide question. Use `python3` when `python` is unavailable.
3. Report each result with its fact, type, scope, source file and line, verification state, and stale state.
4. Treat stale, unverified, and legacy untyped entries as leads that need source checks. Do not state them as current facts without verification.
5. When active records conflict, show the conflict. Use repository authority rules to identify the right source. Do not choose silently.

## Output

```text
Recall: <query>
- <fact> [<decision|lesson>, <active|stale|unverified>, <path>:<line>]
Conflicts: <none or exact conflict>
Current answer: <one short evidence-based answer>
```

## Boundaries

- Read only `docs/decisions.md` and `docs/lessons.md` through the tool.
- Do not load archives or full chat history.
- Do not edit, append, deprecate, or supersede records.
- Do not add a database, index, or background service.
