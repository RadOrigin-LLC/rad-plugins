---
name: coolify-actions
description: Operate existing Coolify resources through CLI or MCP, including deployments, lifecycle changes, logs, and environment settings.
---

# Coolify Actions

Operational playbooks for managing a Coolify instance using MCP tools. Each workflow maps a user intent to a specific sequence of `coolify_*` tool calls.

> **Requires**: The `coolify` MCP server (bundled with this plugin via `@radoriginllc/coolify-mcp`). Set `COOLIFY_URL` to the instance base URL and set `COOLIFY_API_TOKEN` to a team-scoped API token. Never supply a Coolify Private Key as the token. If MCP tools are not available, fall back to the equivalent `curl` commands from the coolify-cicd skill.

> **CLI first**: When the Coolify CLI is installed, verify its configured instance and use the installed command's `--help` for syntax. Otherwise use the configured MCP tools or a documented API equivalent. Do not infer CLI commands from MCP tool names.

## Pre-Flight: Verify Connection

For an MCP workflow, confirm the connection below. A CLI or API workflow uses its own read-only connection check and does not require MCP:

1. Call `coolify_healthcheck` and expect a "connected" response. It uses root-level `/api/health`, outside `/api/v1`.
2. If it fails, the MCP server is misconfigured or the Coolify instance is unreachable

## Mutation gate

Before any deploy, start, stop, restart, cancel, rollback, create, update, or delete operation:

1. Confirm the exact instance base URL and team.
2. Resolve the exact resource name and UUID, then read its current state.
3. State the exact action and expected effect.
4. Ask for explicit user acceptance of that exact instance, resource, and action.

Do not call a mutating MCP, CLI, or API operation before user acceptance. If the target or requested action is unclear, remain read-only.

## Companion-skill rule

RAD Repo Ship owns the exact Git commit and push. Coolify Actions owns platform deployment. RAD Repo Verify Release owns read-only commit-to-production proof.

Offer `rad-repo:ship` only when the current task needs a reviewed repository commit and push, and that exact skill appears in the current available-skill list. Offer `rad-repo:verify-release` only when the current deployment needs commit-to-production proof, and that exact skill appears in the current available-skill list. Ask whether the user accepts each handoff and wait for acceptance before invoking it. If a skill is absent or the user declines, continue this workflow and report the missing next step. Never invoke a companion silently.

## Select the needed operation

Read only the matching section below. Examples are guidance, not a command queue. Resolve the current instance, resource, and installed CLI or MCP schema before using version-sensitive examples. A related skill is useful only when its workflow is needed and available.

Keep diagnosis read-only. Apply existing approval gates to live changes, including restarts, restores, deployments, notifications, and configuration writes. Once an exact action is authorized, complete it and verify its result within the requested scope; do not repeat successful checks without new evidence.

- [Workflow 1: Discover What's Running](references/operations.md#workflow-1-discover-whats-running)
- [Workflow 2: Deploy an Application](references/operations.md#workflow-2-deploy-an-application)
- [Workflow 3: Check Why a Deployment Failed](references/operations.md#workflow-3-check-why-a-deployment-failed)
- [Workflow 4: View Application Logs](references/operations.md#workflow-4-view-application-logs)
- [Workflow 5: Diagnose HTTP Errors (502/503/504)](references/operations.md#workflow-5-diagnose-http-errors-502503504)
- [Workflow 6: Manage Environment Variables](references/operations.md#workflow-6-manage-environment-variables)
- [Workflow 7: Check Server Health](references/operations.md#workflow-7-check-server-health)
- [Workflow 8: Start / Stop / Restart Resources](references/operations.md#workflow-8-start--stop--restart-resources)
- [Workflow 9: Rollback a Deployment](references/operations.md#workflow-9-rollback-a-deployment)
- [Workflow 10: Database Status and Backups](references/operations.md#workflow-10-database-status-and-backups)

## Tool Quick Reference

| Intent | Tool | Key Params |
|--------|------|------------|
| List everything | `coolify_list_all_resources` | — |
| Find an app | `coolify_list_applications` | — |
| Deploy | `coolify_deploy` | `uuid`, `tag`, `force` |
| Check deploy status | `coolify_get_deployment` | `uuid` (deployment UUID) |
| Cancel a deploy | `coolify_cancel_deployment` | `uuid` (deployment UUID) |
| What's deploying now | `coolify_list_running_deployments` | — |
| View logs | `coolify_get_application_logs` | `uuid`, `lines` |
| App details | `coolify_get_application` | `uuid` |
| Restart | `coolify_restart_application` | `uuid` |
| Env vars | `coolify_list_env_vars` | `uuid` |
| Add env var | `coolify_create_env_var` | `uuid`, `key`, `value` |
| Update env var | `coolify_update_env_var` | `uuid`, `key`, `value` |
| Delete env var | `coolify_delete_env_var` | `uuid`, `env_uuid` |
| Update app config | `coolify_update_application` | `uuid`, `settings` |
| Service lifecycle | `coolify_start/stop/restart_service` | `uuid` |
| Backup configs | `coolify_list_database_backups` | `uuid` |
| Backup run history | `coolify_list_backup_executions` | `uuid`, `scheduled_backup_uuid` |
| Server health | `coolify_get_server` | `uuid` |
| Server resources | `coolify_get_server_resources` | `uuid` |

## Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| Deploying without checking current status first | May deploy over a running debug session or ongoing rollback |
| Polling deployment status in a tight loop (< 5 seconds) | Overloads Coolify's database; use 10-15 second intervals |
| Restarting apps to "fix" problems without checking logs first | Masks the root cause; problem recurs on next deploy |
| Adding env vars without redeploying | Changes don't take effect until the next deploy — restarting is not enough |
| Stopping a database without checking which apps depend on it | Apps crash with connection errors |
| Using `force: true` on every deploy | Defeats build caching; 3-10x slower builds for no benefit |

## Related Skills

- **coolify-deploy** — Build pack selection, deployment configuration, registry patterns
- **coolify-cicd** — API reference, GitHub Actions, webhook setup
- **coolify-troubleshoot** — Full diagnostic decision trees for HTTP errors, build failures, SSL issues
- **coolify-security** — Environment variable security, build secrets
- **coolify-databases** — Database provisioning, backup configuration
- **coolify-observability** — Monitoring, log drains, alerting setup

## Additional Resources

### Reference Files

- **`references/workflow-recipes.md`** — Extended workflows: bulk operations, multi-app coordination, automated health checks
