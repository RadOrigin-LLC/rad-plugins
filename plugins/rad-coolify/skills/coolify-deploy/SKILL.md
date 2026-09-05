---
name: coolify-deploy
description: Choose or configure a Coolify build pack, application deployment, registry image, or rollback strategy.
---

# Coolify Deployments

Covers build pack selection, deployment configuration, rolling-update strategies, rollbacks, and registry-based deploys for Coolify v4 self-hosted.

> **Coolify Cloud vs Self-Hosted.** All content assumes self-hosted Coolify v4.x. Coolify Cloud can differ in available options and defaults.

> **Check the instance at use time.** Coolify features and CLI syntax change. Before choosing a build pack or relying on a version-specific setting, run `coolify context verify`, inspect the exact instance, and use the installed `coolify --help` output as the local reference.

## Live-change gate

Before a deploy, rollback, registry change, or application setting update, confirm the exact instance base URL and resource UUID, state the action and expected effect, and ask for explicit user acceptance. For CI, use a protected environment or manual approval. Do not perform the write while any target is unclear.

## Select the needed operation

Read only the matching section below. Examples are guidance, not a command queue. Resolve the current instance, resource, and installed CLI or MCP schema before using version-sensitive examples. A related skill is useful only when its workflow is needed and available.

Keep diagnosis read-only. Apply existing approval gates to live changes, including restarts, restores, deployments, notifications, and configuration writes. Once an exact action is authorized, complete it and verify its result within the requested scope; do not repeat successful checks without new evidence.

- [Build Pack Selection Decision Tree](references/operations.md#build-pack-selection-decision-tree)
- [Deployment Configuration](references/operations.md#deployment-configuration)
- [Rolling Deployments and Rollbacks](references/operations.md#rolling-deployments-and-rollbacks)
- [Pre-Built Image Deployment (Registry Pattern)](references/operations.md#pre-built-image-deployment-registry-pattern)

## Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| Using a floating image tag in production without a refresh trigger | Deployments don't auto-update; you get stale images |
| Putting secrets as build-time env vars when only needed at runtime | Secrets baked into image layers, visible in `docker history` |
| Not setting a health check path for zero-downtime deploys | Coolify uses recreate strategy; causes downtime |
| Setting base directory wrong in monorepos (relative vs absolute) | Build fails or wrong app is built |
| Overriding Nixpacks start command without testing locally | Container starts but crashes; silent failures |
| Using Docker Compose build pack for a single-container app | Unnecessary complexity; use Nixpacks or Dockerfile instead |
| Not pinning Node/Python version via NIXPACKS_*_VERSION | Builds break when Nixpacks bumps the default runtime |
| Ignoring build cache — forcing clean builds on every deploy | 3-10x slower builds, unnecessary registry bandwidth |
| Running database migrations in the Dockerfile | Migrations run at build time, not deploy time; may fail or run against wrong DB |
| Using `--privileged` containers for convenience | Major security risk; almost never required |

## Related Skills

- **coolify-cicd** — Webhook and API-triggered deployments, GitHub Actions workflows
- **coolify-troubleshoot** — Build failures, 502 errors, container crashes
- **coolify-databases** — Database provisioning and connection patterns

## Check Configuration Edits

After changing a Dockerfile or Compose file for this task, offer the matching bundled validator when it would add value. Run it only with the user's approved project path. A finding exit code of `1` means the validator found issues and is valid output.

Resolve the plugin root from this `SKILL.md`, then run one focused command:

```powershell
python <plugin-root>\scripts\lint-dockerfile.py <changed-file> --json
python <plugin-root>\scripts\lint-compose.py <changed-file> --json
```
- **coolify-security** — Environment variable security, build secrets

## Additional Resources

### Reference Files

- **`references/build-packs.md`** — Detailed Nixpacks detection rules, Dockerfile best practices, Docker Compose patterns
- **`references/registry-patterns.md`** — Complete GHCR, Docker Hub, and private registry configuration examples
