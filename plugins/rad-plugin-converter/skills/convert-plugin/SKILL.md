---
name: convert-plugin
description: Convert or repair a plugin or standalone skill package for Agent Plugins 1.0.0 while preserving client-specific behavior.
---

# Convert an Agent Plugin

Use the audit result as the change map. Preserve a working client package until its replacement is validated.

## Choose the Write Mode

| Source | Mode | Source result |
| --- | --- | --- |
| Current Codex package | `--in-place` | Keep `.codex-plugin/plugin.json` |
| Existing Agent Plugin | `--in-place` | Repair portable files only when safe |
| Claude Code package | `--target <new-path>` | Leave the Claude source unchanged |
| Standalone Agent Skill | `--in-place` | Repair only safe skill metadata |

## Procedure

1. Run `audit-plugin` first. Read every error and client-only item.
2. For a new target, verify that it is absent or empty. For an in-place change, confirm the user approved writes.
3. Run one command from the skill directory:

```powershell
python ../../scripts/rad_plugin_converter.py convert <source> --in-place --json
python ../../scripts/rad_plugin_converter.py convert <source> --target <new-path> --json
```

4. Review the result.
   - Root `plugin.json` contains only the portable Agent Plugins fields. It does not declare skills, hooks, commands, agents, UI, or marketplace policy.
   - Portable skills are immediate `skills/<name>/SKILL.md` children. The converter repairs a matching safe name only.
   - A `.mcp.json` command server can become portable `mcp.json` with `type: stdio`. A URL server needs an explicit `streamable-http` or `sse` decision.
   - Credentials and secret headers cannot enter portable `mcp.json`.
   - Hooks and other client-only behavior need one recorded outcome: retained compatibility, explicit skill, portable MCP replacement, or an intentional limitation.
5. Run the audit again. Resolve errors before publishing. Warnings and client-only items need a recorded review decision.
6. Report source and target paths, changed files, retained compatibility files, unresolved behavior, and validation output.

Do not delete a Claude source, overwrite a nonempty target, or claim client extension support without client documentation.
