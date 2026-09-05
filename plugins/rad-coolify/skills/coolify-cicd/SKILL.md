---
name: coolify-cicd
description: Configure Coolify deployment pipelines, API or webhook triggers, registry builds, and preview environments.
---

# Coolify CI/CD

Covers the Coolify REST API, GitHub Actions integration, GHCR workflows, webhooks, and PR preview environments for Coolify v4 self-hosted.

> **Self-Hosted Only**: All content assumes self-hosted Coolify v4.x. API endpoints and webhook behavior may differ on Coolify Cloud.

## Live-change gate

For every API, webhook, or CLI write, confirm the exact instance base URL and resource UUID, state the action and expected effect, and require user acceptance. For unattended CI, put production deploys behind the CI system's protected environment or manual approval. A secret or UUID alone is not approval.

## Select the needed operation

Read only the matching section below. Examples are guidance, not a command queue. Resolve the current instance, resource, and installed CLI or MCP schema before using version-sensitive examples. A related skill is useful only when its workflow is needed and available.

Keep diagnosis read-only. Apply existing approval gates to live changes, including restarts, restores, deployments, notifications, and configuration writes. Once an exact action is authorized, complete it and verify its result within the requested scope; do not repeat successful checks without new evidence.

- [Deployment Trigger Methods](references/operations.md#deployment-trigger-methods)
- [REST API](references/operations.md#rest-api)
- [Deploy Webhook URL](references/operations.md#deploy-webhook-url)
- [GitHub Actions Integration](references/operations.md#github-actions-integration)
- [GHCR Pattern (Full Pipeline)](references/operations.md#ghcr-pattern-full-pipeline)
- [Webhooks and Auto-Deploy](references/operations.md#webhooks-and-auto-deploy)

## Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| Using the same API token for all environments | Staging pipeline can accidentally deploy to production |
| Not using `--fail` flag in curl deploy commands | CI/CD pipeline reports success even when deploy fails |
| Hardcoding Coolify URL or UUID in workflow files | Breaks when migrating Coolify or recreating apps |
| Polling deployment status in a tight loop | Wastes API rate limits; use reasonable intervals (10-15s) |
| Deploying without running tests first | Broken code reaches production |
| Using webhook URL in public repos | Anyone can trigger your deployments |
| Not pinning image tags in production | Floating tags mean non-deterministic deployments |
| Skipping the PATCH step in GHCR workflows | Coolify deploys the old image tag, not the new one |

## Related Skills

- **coolify-deploy** — Build pack selection, deployment configuration, rollbacks
- **coolify-security** — API token management, webhook security
- **coolify-troubleshoot** — Debugging failed deployments

## Additional Resources

### Reference Files

- **`references/api-reference.md`** — Full Coolify API v1 endpoint reference with request/response shapes
- **`references/gitlab-ci-pattern.md`** — GitLab CI integration pattern for Coolify
