---
name: audit-plugin
description: Audit plugin or standalone skill conformance to Agent Plugins 1.0.0 without modifying the package.
---

# Audit an Agent Plugin

Audit first. Do not edit, move, install, remove, commit, or publish files in this skill.

## Procedure

1. Identify the package root. Read its manifests, skills, MCP files, license, and client-only directories.
2. Run the bundled audit from the skill directory:

```powershell
python ../../scripts/rad_plugin_converter.py audit <package-root> --json
```

3. Check the report before making a recommendation.
   - Root `plugin.json` is the portable Agent Plugins manifest. It has only portable fields.
   - `skills/<name>/SKILL.md` and root `mcp.json` are the portable components.
   - `.codex-plugin`, `.claude-plugin`, hooks, agents, commands, UI, and marketplace data are client-specific. Report them. Do not call them portable components.
   - A `SKILL.md` over 500 lines is a warning. It does not fail conformance by itself.
4. Report each error with its path, reason, and smallest safe fix. Separate warnings and client-only items.
5. If the user wants changes, use `convert-plugin`. A Claude source stays unchanged when the converter writes to a separate target.

## Report Format

```text
Format: <detected package types>
Portable status: conforming | errors found
Errors: <path, rule, smallest fix>
Warnings: <path, reason>
Client-only items: <path, retain or review>
Next action: audit only | convert in place | convert to a new target
```

Do not claim that a client will load an extension unless its owner documents that behavior.
