---
name: coolify-actions
description: >
  This skill should be used when performing operational actions against a Coolify instance using
  MCP tools — deploying applications, checking deployment status, viewing logs, diagnosing errors,
  managing environment variables, restarting services, checking server health, or performing any
  hands-on Coolify management task. Trigger when: "deploy my app", "check Coolify status",
  "show me Coolify logs", "what's running on Coolify", "restart my app on Coolify",
  "check server health", "why is my deploy failing", "list my Coolify apps",
  "add env var to Coolify", "Coolify deployment status", "roll back my deploy",
  "check my databases", "what resources are on my server".
---

# Coolify Actions

Operational playbooks for managing a Coolify instance using MCP tools. Each workflow maps a user intent to a specific sequence of `coolify_*` tool calls.

> **Requires**: The `coolify` MCP server (bundled with this plugin via `@radoriginllc/coolify-mcp`). Set `COOLIFY_URL` to the instance base URL and set `COOLIFY_API_TOKEN` to a team-scoped API token. Never supply a Coolify Private Key as the token. If MCP tools are not available, fall back to the equivalent `curl` commands from the coolify-cicd skill.

## Pre-Flight: Verify Connection

Before any workflow, confirm the MCP connection is live:

1. Call `coolify_healthcheck` and expect a "connected" response. It uses root-level `/api/health`, outside `/api/v1`.
2. If it fails, the MCP server is misconfigured or the Coolify instance is unreachable

## Workflow 1: Discover What's Running

**Intent**: "What's on my Coolify?", "list my apps", "what resources do I have?"

```
coolify_list_all_resources
```

For more detail on a specific category:
- `coolify_list_applications` — all apps with status
- `coolify_list_databases` — all databases
- `coolify_list_services` — one-click services
- `coolify_list_servers` — all managed servers
- `coolify_list_projects` — project organization

Present results as a summary table: name, status, type, domain.

## Workflow 2: Deploy an Application

**Intent**: "deploy my app", "trigger a deployment", "push to production"

```
Step 1: coolify_list_applications          → find the app UUID
Step 2: coolify_deploy(uuid: "<APP_UUID>") → trigger deploy, capture deployment_uuid
Step 3: coolify_get_deployment(uuid: "<DEPLOYMENT_UUID>")  → poll status
```

**Polling pattern**: After triggering deploy, wait 10-15 seconds, then poll `coolify_get_deployment`. Repeat until `status` is `finished`, `failed`, or `cancelled`. Report the result.

**Force rebuild** (skip cache): `coolify_deploy(uuid: "<APP_UUID>", force: true)`

**Batch deploy by tag**: `coolify_deploy(tag: "backend")` — deploys all resources with that tag.

## Workflow 3: Check Why a Deployment Failed

**Intent**: "why did my deploy fail?", "deployment error", "build failed"

```
Step 1: coolify_list_applications              → find app UUID
Step 2: coolify_list_deployments(uuid: "<APP_UUID>", take: 5) → get recent deployments
Step 3: coolify_get_deployment(uuid: "<FAILED_DEPLOYMENT_UUID>")  → get full logs
```

Read the `logs` field in the deployment response. Look for:
- Build errors (npm, pip, cargo failures) — 5-10 lines before "Build failed"
- Missing env vars — `undefined`, `ENOENT`, `KeyError`
- Port mismatches — app listening on wrong port
- OOM during build — `ENOMEM`, `Killed`

If the build succeeded but the app isn't serving, continue to Workflow 5 (diagnose HTTP errors).

## Workflow 4: View Application Logs

**Intent**: "show me logs", "what's in the logs?", "check logs for errors"

```
Step 1: coolify_list_applications                         → find app UUID
Step 2: coolify_get_application_logs(uuid: "<APP_UUID>", lines: 200)
```

Scan for error patterns: `ERROR`, `Error`, `FATAL`, `Unhandled`, stack traces, exit codes. Summarize findings for the user.

## Workflow 5: Diagnose HTTP Errors (502/503/504)

**Intent**: "getting a 502", "bad gateway", "site is down", "504 timeout"

This is a multi-step diagnostic. Follow the decision tree:

```
Step 1: coolify_list_applications              → find app UUID and check status
Step 2: coolify_get_application(uuid: "<APP_UUID>")  → check config (port, domain, health check)
Step 3: coolify_get_application_logs(uuid: "<APP_UUID>", lines: 100) → check for crashes
Step 4: coolify_list_deployments(uuid: "<APP_UUID>", take: 3) → check recent deploy status
```

**Decision logic**:
- App status is "stopped" or "exited" → offer to restart: `coolify_restart_application`
- Port Exposes doesn't match what the app listens on → advise fixing port config
- Health check failing → check if health check path returns 200
- Container is OOM-killed → check resource limits in app config
- Deploy succeeded but 502 persists → check proxy logs (advise SSH + `docker logs coolify-proxy`)

See **coolify-troubleshoot** skill for the full diagnostic decision tree with all edge cases.

## Workflow 6: Manage Environment Variables

**Intent**: "add an env var", "update environment variable", "check what env vars are set"

**List env vars**:
```
Step 1: coolify_list_applications               → find app UUID
Step 2: coolify_list_env_vars(uuid: "<APP_UUID>")
```

**Add a new env var**:
```
coolify_create_env_var(
  uuid: "<APP_UUID>",
  key: "DATABASE_URL",
  value: "postgresql://..."
)
```

**Update an existing env var** (matched by key):
```
coolify_update_env_var(uuid: "<APP_UUID>", key: "DATABASE_URL", value: "postgresql://new-host...")
```

**Delete an env var** (needs the env var's own UUID, from the list call):
```
Step 1: coolify_list_env_vars(uuid: "<APP_UUID>")   → find the env var UUID
Step 2: coolify_delete_env_var(uuid: "<APP_UUID>", env_uuid: "<ENV_UUID>")
```

**Important**: Env var changes take effect on the next **deploy**, not on restart — a restart reuses the existing container with the old values:
```
coolify_deploy(uuid: "<APP_UUID>")
```

**Security reminder**: Never set secrets as build-time variables unless using Docker Build Secrets. See **coolify-security** skill for the decision tree.

## Workflow 7: Check Server Health

**Intent**: "how's my server?", "check server health", "is my server okay?"

```
Step 1: coolify_list_servers                        → list all servers with status
Step 2: coolify_get_server(uuid: "<SERVER_UUID>")   → detailed server info
Step 3: coolify_get_server_resources(uuid: "<SERVER_UUID>") → all resources on server
```

Report: server reachability, number of running resources, any resource in error/stopped state.

For CPU/memory/disk metrics, the Coolify API does not expose Sentinel data — advise checking the dashboard UI at **Servers → Metrics**, or see **coolify-observability** for Grafana/Prometheus setup.

## Workflow 8: Start / Stop / Restart Resources

**Intent**: "restart my app", "stop the database", "start the service"

**Applications**: `coolify_start_application`, `coolify_stop_application`, `coolify_restart_application`
**Databases**: `coolify_start_database`, `coolify_stop_database`, `coolify_restart_database`
**Services**: `coolify_start_service`, `coolify_stop_service`, `coolify_restart_service`

Always confirm with the user before stopping production resources.

## Workflow 9: Rollback a Deployment

**Intent**: "roll back", "revert to previous version", "undo the deploy"

```
Step 1: coolify_list_deployments(uuid: "<APP_UUID>", take: 10)  → find last successful deploy
Step 2: Identify the commit SHA or image tag from the last "finished" deployment
Step 3: coolify_update_application(uuid: "<APP_UUID>", settings: {"docker_registry_image_tag": "<PREVIOUS_TAG>"})
Step 4: coolify_deploy(uuid: "<APP_UUID>")
```

**Limitation**: Rollback only works if the previous Docker image still exists locally on the server. Automated Docker cleanup may have pruned it.

For git-based apps, rollback by updating the branch or commit reference rather than the image tag.

**Cancel a bad deploy in progress**: if a broken deployment is still building, cancel it instead of waiting it out:
```
Step 1: coolify_list_running_deployments         → find the in-progress deployment UUID
Step 2: coolify_cancel_deployment(uuid: "<DEPLOYMENT_UUID>")
```

## Workflow 10: Database Status and Backups

**Intent**: "check my databases", "are backups running?", "database status"

```
Step 1: coolify_list_databases         → list all databases with status
Step 2: coolify_get_database(uuid: "<DB_UUID>") → detailed config and backup info
Step 3: coolify_list_database_backups(uuid: "<DB_UUID>")  → scheduled backup configs
Step 4: coolify_list_backup_executions(uuid: "<DB_UUID>", scheduled_backup_uuid: "<BACKUP_UUID>") → run history
```

Check the execution history for failed runs and the timestamp of the last successful backup. **Note**: the API manages *scheduled* backups (`POST /databases/{uuid}/backups` creates a schedule, not a one-off run) — triggering an immediate manual backup still requires the Coolify dashboard.

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
