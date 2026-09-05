---
name: coolify-infrastructure
description: Configure Coolify servers, build hosts, multi-server deployments, instance backups, or migrations.
---

# Coolify Infrastructure

Covers multi-server deployment, Docker Swarm (experimental), build servers, Coolify instance management, and scaling patterns for Coolify v4 self-hosted.

> **Stability Warning**: Multi-server and Swarm features are evolving. Some configurations may change between Coolify releases. Always test in staging first.

## Live-change gate

Before a migration, backup restore, server change, or self-update, confirm the exact instance and server, state the action and expected effect, and require user acceptance. For CI, use a protected environment or manual approval. Stop if approval is missing.

## Select the needed operation

Read only the matching section below. Examples are guidance, not a command queue. Resolve the current instance, resource, and installed CLI or MCP schema before using version-sensitive examples. A related skill is useful only when its workflow is needed and available.

Keep diagnosis read-only. Apply existing approval gates to live changes, including restarts, restores, deployments, notifications, and configuration writes. Once an exact action is authorized, complete it and verify its result within the requested scope; do not repeat successful checks without new evidence.

- [Multi-Server Architecture](references/operations.md#multi-server-architecture)
- [Docker Swarm (Experimental)](references/operations.md#docker-swarm-experimental)
- [Build Server Configuration](references/operations.md#build-server-configuration)
- [Coolify Instance Management](references/operations.md#coolify-instance-management)

## Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| Using Swarm for production-critical workloads | Experimental support means unexpected failures |
| No Docker Registry configured for multi-server | Builds fail to propagate to remote servers |
| Not backing up `/data/coolify/` | Lose all Coolify configuration, SSH keys, and ACME certificates |
| Running builds on the same server as production apps | Build process consumes all CPU/RAM; production apps become unresponsive |
| Using DNS round-robin as the sole load balancing strategy | No health checking; dead servers still receive traffic |
| Exposing Swarm management ports (2377) to the internet | Anyone can join your Swarm cluster |
| Not testing Coolify backups by restoring | Discover corrupt or incomplete backups during an emergency |
| Updating Coolify in production without reading release notes | Breaking changes in database schema or API |
| Running all Coolify infrastructure on a single server | Single point of failure for everything |
| Not securing SSH keys between Coolify main and remote servers | Compromised main server gives access to all remote servers |

## Related Skills

- **coolify-deploy** — Deployment configuration, registry patterns
- **coolify-security** — Server hardening, UFW configuration, SSH security
- **coolify-observability** — Multi-server monitoring setup
- **coolify-databases** — Database management on remote servers
- **coolify-cicd** — Multi-environment CI/CD pipelines

## Additional Resources

### Reference Files

- **`references/multi-server-setup.md`** — Step-by-step multi-server configuration with registry
- **`references/swarm-guide.md`** — Docker Swarm initialization and management in Coolify
