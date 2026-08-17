---
name: coolify-status
description: >
  This skill should be used for a quick health/status overview of a Coolify instance — a one-shot
  "is everything up" dashboard. Trigger when: "coolify status", "is everything up", "how's my
  Coolify doing", "status check", "give me a Coolify overview", "anything down?", "morning check",
  "is my server healthy", "what's the state of my deployments". For deep diagnosis of a specific
  problem, use coolify-troubleshoot; for performing actions (deploy, restart, env vars), use
  coolify-actions.
---

# Coolify Status

One-shot status overview of a Coolify instance. Run the checks, present one compact dashboard, flag anything that needs attention. Read-only — this skill never starts, stops, deploys, or modifies anything.

> **Requires**: The `coolify` MCP server (bundled with this plugin). Set `COOLIFY_URL` to the instance base URL and set `COOLIFY_API_TOKEN` to a team-scoped API token with `read`. If MCP tools are unavailable, say so and point to the plugin README setup section. Do not guess.

## Procedure

Run these in order (steps 1-2 ground everything else; 3-5 can be summarized from fewer calls if the instance is small):

```
Step 1: coolify_healthcheck            → root-level /api/health reachable?
Step 2: coolify_version                → instance version (ground any version-specific advice on THIS, not on docs)
Step 3: coolify_list_servers           → server reachability
Step 4: coolify_list_all_resources     → apps/databases/services with status
Step 5: coolify_list_running_deployments → anything deploying right now?
```

If step 1 fails, stop and report: the instance is unreachable or the MCP env vars are wrong. Distinguish the two if possible (a DNS/connection error means unreachable; a 401 means bad token).

## Output format

Present a single compact dashboard:

```markdown
# Coolify Status — <instance URL>

**API**: connected | **Version**: v4.x.x | **Servers**: 2/2 reachable

## Resources
| Name | Type | Status | Notes |
|------|------|--------|-------|
| my-app | application | running:healthy | — |
| my-db | postgresql | running | — |
| umami | service | exited | ⚠ stopped |

## In-flight deployments
None  (or: my-app — in_progress, started 2m ago)

## Needs attention
- umami is stopped — restart with coolify-actions if unintended
```

Rules:
- **Lead with problems.** If anything is stopped, exited, degraded, or unreachable, surface it in the first line of your reply, before the dashboard.
- **All green = one short confirmation** plus the dashboard. Don't pad.
- Statuses like `running:unhealthy` mean the container runs but its healthcheck fails — flag these as problems, not as running.
- Don't speculate on causes here. If something is down, offer the next step: coolify-troubleshoot for diagnosis or coolify-actions to restart.

## Version grounding

Step 2's `coolify_version` result is the source of truth for what this instance supports. Coolify v4 is a rolling beta — features in this plugin's docs may not exist on older instances (shared variable scopes, API token expiration, newer database engines). When advice depends on version, check the instance version first instead of assuming the docs' snapshot.

## Related Skills

- **coolify-actions** — perform the fixes (restart, deploy, env vars)
- **coolify-troubleshoot** — diagnose why something is down
- **coolify-observability** — set up real monitoring so you don't need to ask
