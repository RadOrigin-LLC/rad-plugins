---
name: coolify-observability
description: Set up monitoring, alerts, notifications, or log drains for Coolify-managed applications.
---

# Coolify Observability

Covers Sentinel monitoring, notification channels, log drains, external monitoring integration, and resource observability for Coolify v4 self-hosted.

> **Self-Hosted Only**: All content assumes self-hosted Coolify v4.x. Monitoring and log drain features may differ on Coolify Cloud.

## Live-change gate

Before deploying monitoring resources or changing notifications, log drains, or alert settings, confirm the exact instance and resource, state the action and expected effect, and require user acceptance. For CI, use a protected environment or manual approval. Stop if approval is missing.

## Select the needed operation

Read only the matching section below. Examples are guidance, not a command queue. Resolve the current instance, resource, and installed CLI or MCP schema before using version-sensitive examples. A related skill is useful only when its workflow is needed and available.

Keep diagnosis read-only. Apply existing approval gates to live changes, including restarts, restores, deployments, notifications, and configuration writes. Once an exact action is authorized, complete it and verify its result within the requested scope; do not repeat successful checks without new evidence.

- [Observability Architecture](references/operations.md#observability-architecture)
- [Coolify Sentinel](references/operations.md#coolify-sentinel)
- [Notification Channels](references/operations.md#notification-channels)
- [Log Drains](references/operations.md#log-drains)
- [Uptime Kuma Integration](references/operations.md#uptime-kuma-integration)
- [External Monitoring Integration](references/operations.md#external-monitoring-integration)

## Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| No notification channel configured | Deployments fail silently; containers crash without anyone knowing |
| Setting disk alert threshold to 95% | Too late — Docker and Coolify may malfunction before you can act |
| Not deploying Uptime Kuma or external monitoring | Rely solely on Coolify dashboard; miss issues when Coolify itself is down |
| Sending all container logs to a paid SaaS without filtering | Expensive log ingestion bills for debug/verbose logs |
| Not testing notification delivery after setup | Discover broken notifications during an actual incident |
| Monitoring only HTTP status, not response time | Miss gradual performance degradation |
| Running Prometheus + Grafana on the same server as production apps | Monitoring stack competes for resources with production |
| Not setting up a status page for end users | Users don't know about outages; support tickets spike |

## Related Skills

- **coolify-troubleshoot** — Diagnostic flows that use monitoring data
- **coolify-security** — Resource limit alerting, access control
- **coolify-infrastructure** — Multi-server monitoring considerations
- **coolify-databases** — Database-specific monitoring and OOM detection
- **coolify-cicd** — Deployment notifications and status webhooks

## Additional Resources

### Reference Files

- **`references/log-drain-configs.md`** — Detailed configuration for each log drain destination
- **`references/grafana-prometheus-setup.md`** — Step-by-step Grafana + Prometheus + cAdvisor setup for Coolify
