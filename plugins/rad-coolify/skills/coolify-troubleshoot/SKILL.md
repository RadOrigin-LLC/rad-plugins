---
name: coolify-troubleshoot
description: Diagnose Coolify build, container, routing, certificate, or instance failures from current state and logs.
---

# Coolify Troubleshooting

Diagnostic flows for HTTP errors, container issues, build failures, SSL problems, and Coolify self-repair for v4 self-hosted.

> **Self-Hosted Only**: All diagnostic commands assume self-hosted Coolify v4.x with SSH access to the server. Coolify Cloud users have limited access to container-level debugging.

## Select the needed operation

Read only the matching section below. Examples are guidance, not a command queue. Resolve the current instance, resource, and installed CLI or MCP schema before using version-sensitive examples. A related skill is useful only when its workflow is needed and available.

Keep diagnosis read-only. Apply existing approval gates to live changes, including restarts, restores, deployments, notifications, and configuration writes. Once an exact action is authorized, complete it and verify its result within the requested scope; do not repeat successful checks without new evidence.

- [Master Diagnostic Decision Tree](references/operations.md#master-diagnostic-decision-tree)
- [502 Bad Gateway — Diagnostic Flow](references/operations.md#502-bad-gateway--diagnostic-flow)
- [504 Gateway Timeout — Diagnostic Flow](references/operations.md#504-gateway-timeout--diagnostic-flow)
- [Container Lifecycle Issues](references/operations.md#container-lifecycle-issues)
- [Build Failure Diagnosis](references/operations.md#build-failure-diagnosis)
- [SSL Certificate Issues](references/operations.md#ssl-certificate-issues)
- [Coolify Self-Repair](references/operations.md#coolify-self-repair)

## Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| Restarting Coolify as first troubleshooting step | Wastes time; doesn't fix app-level issues |
| Deleting and recreating the app instead of debugging | Loses deployment history, env vars, and volume data |
| Ignoring exit codes and only reading the last log line | Misses the actual root cause |
| Not setting health checks, then wondering why 502s occur during deploys | No health check = no zero-downtime deploys |
| Force-rebuilding every time instead of investigating cache issues | 3-10x slower builds; masks the real problem |
| Exposing debug ports (9229, 5005) in production | Security risk; remote code execution possible |
| Running `docker system prune -a` without checking | Removes all cached images; next build will be very slow |
| Deleting ACME storage to "fix" SSL | Forces renewal of ALL certs; may hit rate limits |

## Related Skills

- **coolify-deploy** — Deployment configuration, build pack selection
- **coolify-security** — Resource limits, OOM prevention
- **coolify-observability** — Monitoring, log drains, alerting
- **coolify-databases** — Database connection issues, OOM

## Additional Resources

### Reference Files

- **`references/traefik-debugging.md`** — Traefik v3 routing diagnosis, label inspection, dynamic config
- **`references/common-errors.md`** — Expanded error pattern table with fixes for 50+ common issues
