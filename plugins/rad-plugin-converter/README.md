# RAD Plugin Converter

RAD Plugin Converter is itself an Agent Plugins 1.0.0 package. It creates, audits, and converts other plugin packages for that standard. Its publish skill guides reviewed marketplace, Git, client, and agent-visible release work. Local conformance checks cannot prove that every client-specific feature will run.

It is for plugin authors who need to move a Claude Code, Codex, mixed, legacy, or standalone Agent Skill package toward the portable format. It does not convert an ordinary application repository into a plugin.

The Agent Plugins 1.0.0 specification is published. Agent Plugins 1.1.0 is a working draft. This package pins its checks to version 1.0.0.

## Skills

| Skill | Use it for | Result |
| --- | --- | --- |
| `create-plugin` | A new standards-based plugin | Portable and Codex manifests plus an optional starter skill |
| `audit-plugin` | A read-only conformance check | Detected formats, errors, warnings, client-only files, and smallest safe fixes |
| `convert-plugin` | A requested migration | An additive portable manifest, safe Agent Skill fixes, and a validation report |
| `publish-plugin` | A reviewed marketplace release | Package, Git, client, and agent-visible publish gates |

## What it checks

- Root Agent Plugins `plugin.json` fields and name rules.
- Immediate `skills/<name>/SKILL.md` discovery and Agent Skills frontmatter.
- Local skill links and package paths that escape the package root.
- Portable `mcp.json` fields, transports, URLs, paths, and embedded credential headers.
- Client-only files such as `.codex-plugin`, `.claude-plugin`, hooks, agents, commands, LSP, and UI folders.

## How conversion works

For a Codex package, the converter adds root `plugin.json` and keeps `.codex-plugin/plugin.json` for current Codex compatibility.

For a Claude Code package, use a separate target. The source stays unchanged. Hooks have no portable Agent Plugins v1 equivalent. The conversion report records whether each hook remains client-only, becomes an on-demand skill, has a portable replacement, or is an intentional limitation.

The converter can infer `stdio` for a legacy MCP entry with an executable command. It will not guess whether a URL uses Streamable HTTP or SSE. It stops and asks for that choice.

## Local commands

```powershell
python .\scripts\rad_plugin_converter.py create <plugin-name> --target <new-package-root> --description "<purpose>" --author "<publisher>" --json
python .\scripts\rad_plugin_converter.py audit <package-root> --json
python .\scripts\rad_plugin_converter.py convert <package-root> --in-place --json
python .\scripts\rad_plugin_converter.py convert <claude-source> --target <new-package-root> --json
python .\scripts\rad_plugin_converter.py marketplace <marketplace-root> --json
python .\scripts\rad_plugin_converter.py marketplace <marketplace-root> --apply --json
```

Add `--dry-run` to `create`, `convert`, or `marketplace` to list planned paths without writing files. Human-readable output labels these paths as `Planned`.

`marketplace` is read-only unless `--apply` is present. The tool does not make network calls.

## Limits

- The checks are local package checks. They do not prove every supported client will run each client-specific feature.
- The converter preserves documented client compatibility files. It does not invent a client extension namespace.
- It repairs a skill name only when the directory name is valid and the repair is safe. Missing or misleading descriptions need an author review.
- Publishing, installing, removing old marketplace entries, committing, and pushing follow the exact authorization gates in `publish-plugin`.

## Install

```powershell
codex plugin add rad-plugin-converter@radesjardins-codex-skills
```

## License

MIT. See [LICENSE](LICENSE).
