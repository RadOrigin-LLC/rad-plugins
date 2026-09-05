---
name: coolify-security
description: Review or configure Coolify secrets, access controls, container isolation, firewall rules, and resource limits.
---

# Coolify Security

Covers secrets management, RBAC, network isolation, resource limits, and access control for Coolify v4 self-hosted.

> **Self-Hosted Responsibility**: Coolify self-hosted means YOU own server security. Coolify manages application-layer orchestration, not OS-level hardening.

## Live-change gate

Before changing secrets, permissions, networks, firewall rules, terminal access, or resource limits, confirm the exact instance, resource or server target, action, and expected effect. Ask for explicit user acceptance before the write. Keep audits and discovery read-only.

## Select the needed operation

Read only the matching section below. Examples are guidance, not a command queue. Resolve the current instance, resource, and installed CLI or MCP schema before using version-sensitive examples. A related skill is useful only when its workflow is needed and available.

Keep diagnosis read-only. Apply existing approval gates to live changes, including restarts, restores, deployments, notifications, and configuration writes. Once an exact action is authorized, complete it and verify its result within the requested scope; do not repeat successful checks without new evidence.

- [Secrets Management](references/operations.md#secrets-management)
- [RBAC (Role-Based Access Control)](references/operations.md#rbac-role-based-access-control)
- [Network Isolation](references/operations.md#network-isolation)
- [UFW and Docker — The Known Conflict](references/operations.md#ufw-and-docker--the-known-conflict)
- [Resource Limits](references/operations.md#resource-limits)
- [Terminal Access and Auditing](references/operations.md#terminal-access-and-auditing)

## Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| Storing secrets as build-time env vars when only needed at runtime | Secrets baked into Docker image layers, extractable via `docker history` |
| Using the same API token for all CI/CD pipelines | Compromising one pipeline compromises everything |
| Not setting memory limits on any container | One runaway process can OOM-kill the entire server |
| Relying on UFW alone to protect Docker-published ports | UFW rules are bypassed by Docker's iptables manipulation |
| Giving Developer role to users who should be Viewers | Developers can access terminal, modify env vars, trigger deployments |
| Running containers as root without `USER` directive | Container escape gives root on host if Docker is not hardened |
| Using `--privileged` flag on any container | Full host access; defeats all container isolation |
| Exposing database ports to 0.0.0.0 | Database accessible from any IP; bots will find it |
| Not rotating API tokens or database credentials | Long-lived credentials increase blast radius of compromise |
| Sharing one team for all projects | No isolation between projects; one compromised member affects everything |

## Related Skills

- **coolify-deploy** — Build secrets configuration, environment variable setup
- **coolify-databases** — Database credential management, SSL configuration
- **coolify-infrastructure** — Server-level security, SSH configuration
- **coolify-troubleshoot** — Diagnosing OOM kills, network issues

## Additional Resources

### Reference Files

- **`references/hardening-checklist.md`** — Step-by-step server and Coolify hardening guide
- **`references/ufw-docker-guide.md`** — Complete UFW + Docker configuration with ufw-docker utility
