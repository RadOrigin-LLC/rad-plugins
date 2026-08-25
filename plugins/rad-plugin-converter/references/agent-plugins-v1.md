# Agent Plugins 1.0.0

Use this package with the published Agent Plugins 1.0.0 specification. Agent Plugins 1.1.0 is a working draft.

- Portable root manifest: `plugin.json`.
- Portable components: immediate `skills/<name>/SKILL.md` folders and optional root `mcp.json`.
- Root `plugin.json` is closed. It does not declare component paths or client behavior.
- Client-only behavior needs a documented client extension or compatibility package.
- Package paths must remain inside the resolved plugin root.

Primary sources:

- https://github.com/agentplugins/agent-plugins-spec
- https://agent-plugins.org/specification
- https://agent-plugins.org/plugin-authors/manifest
- https://agent-plugins.org/plugin-authors/skills
- https://agentskills.io/specification
