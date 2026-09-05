---
name: create-plugin
description: Create a new Agent Plugins 1.0.0 package with Codex metadata and an optional starter skill.
---

# Create an Agent Plugin

Create a new package only after the user chooses its destination. Do not register it in a marketplace unless the user separately asks for that action.

## Procedure

1. Collect a plugin name, target directory, purpose description, and author. Use version `0.1.0` and license `MIT` unless the user specifies other values.
2. If the package needs a starter skill, collect its name and trigger-focused description. Supply both values together.
3. Confirm that the target is absent or empty.
4. Run from this skill directory:

```powershell
python ../../scripts/rad_plugin_converter.py create <plugin-name> `
  --target <new-plugin-directory> `
  --description "<purpose>" `
  --author "<publisher>" `
  --version 0.1.0 `
  --license MIT `
  --skill <skill-name> `
  --skill-description "<trigger and purpose>" `
  --json
```

Omit both skill options when no starter skill is needed.

5. Review every changed file and finding. The portable root `plugin.json` must contain only Agent Plugins fields. Codex interface data stays in `.codex-plugin/plugin.json`.
6. Run `audit-plugin` against the new package. Resolve all errors before publishing or installation.

The create command refuses a nonempty target. Do not bypass that safeguard, add the package to a marketplace, or copy it into another repository without explicit user approval.
