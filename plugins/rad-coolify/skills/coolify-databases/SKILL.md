---
name: coolify-databases
description: Configure Coolify databases, connections, backups, restores, migrations, and credentials.
---

# Coolify Databases

Covers provisioning, backups, SSL, credential management, and operational patterns for Coolify v4 self-hosted database management.

> **Self-Hosted Only**: All content assumes self-hosted Coolify v4.x. Database management differs on Coolify Cloud.

## Live-change gate

Before creating, restoring, exposing, rotating, dropping, or changing a database, confirm the exact instance, database resource UUID, action, and expected effect. Ask for explicit user acceptance before the write. Keep discovery and backup-status checks read-only.

## Select the needed operation

Read only the matching section below. Examples are guidance, not a command queue. Resolve the current instance, resource, and installed CLI or MCP schema before using version-sensitive examples. A related skill is useful only when its workflow is needed and available.

Keep diagnosis read-only. Apply existing approval gates to live changes, including restarts, restores, deployments, notifications, and configuration writes. Once an exact action is authorized, complete it and verify its result within the requested scope; do not repeat successful checks without new evidence.

- [Supported Database Engines](references/operations.md#supported-database-engines)
- [Provisioning Decision Tree](references/operations.md#provisioning-decision-tree)
- [Networking and Access Patterns](references/operations.md#networking-and-access-patterns)
- [Backups](references/operations.md#backups)
- [SSL/TLS Configuration](references/operations.md#ssltls-configuration)
- [Operational Patterns](references/operations.md#operational-patterns)

## Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| Exposing database port to 0.0.0.0 without firewall rules | Database accessible to the entire internet |
| No backup schedule configured | Data loss on disk failure or corruption |
| Storing backups on the same server as the database | Single point of failure; backup lost with the server |
| Using default credentials (postgres/postgres) | Trivially compromised |
| Not setting memory limits on database containers | OOM kills the database AND other containers on the server |
| Running migrations in Dockerfile build phase | Migrations run against wrong database or fail in CI |
| Sharing a small Redis between cache and queue workloads | Cache evictions delete queued jobs |
| Not testing backup restoration | Discover corrupt backups only during an emergency |
| Exposing ports and forgetting to close them | Permanent attack surface |
| Using `sslmode=disable` for cross-server connections | Credentials sent in plaintext |

## Related Skills

- **coolify-deploy** — Pre-deployment scripts for running migrations
- **coolify-security** — Database credential management, network isolation
- **coolify-troubleshoot** — Database OOM diagnosis, connection issues
- **coolify-observability** — Database monitoring and alerting

## Additional Resources

### Reference Files

- **`references/backup-restore.md`** — Detailed backup configuration, restore procedures per engine, point-in-time recovery
- **`references/connection-patterns.md`** — Connection string formats, pooling, SSL configuration per database engine
