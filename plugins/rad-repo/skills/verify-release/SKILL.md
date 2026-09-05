---
name: verify-release
description: Verify a release on explicit request by following its exact deployment and proving the pushed revision is live.
---

# Verify a Release

Run a separate, read-only release check after a push. Prove the deployment identity and the public revision without running the `ship` workflow.

## Bound the check

Record the repository, branch, pushed full SHA, deploy target, production environment, canonical public URL, provider, and maximum wait. Read `deploy:` from repository instructions when present.

Start one 10-minute clock at the first provider query. Use it for deployment discovery, execution, and public propagation, with a 30-second status interval, unless the user or provider sets a safer limit. Send a short progress update at least once per minute. A longer wait requires user direction.

This skill authorizes read-only Git, provider, HTTP, browser, log, and status checks. It does not authorize a deployment, retry, restart, rollback, promotion, cancellation, configuration change, migration, commit, tag, or release edit.

## Verify the pushed revision

1. Record `git rev-parse HEAD`, branch, working-tree state, and a credential-redacted remote URL.
2. Query the remote directly. Prefer branch-tip equality from `git ls-remote`. When the pushed SHA is intentionally behind the tip, use a read-only provider commit or compare API. Do not fetch only to prove remote identity. Stop with `UNVERIFIED` when remote identity cannot be proven.
3. Identify the exact production project and environment from repository instructions or explicit user context. Stop with `UNVERIFIED` before querying an ambiguous or missing target.

## Follow one deployment

1. Find the deployment whose provider record contains the full pushed SHA. Poll for its appearance within the same wait limit. Record its immutable deployment ID, project, environment, creation time, and state. Return `UNVERIFIED` when no matching record appears.
2. If several production deployments match the SHA, require the provider's push, webhook, build, or commit linkage to identify the deployment started for this release. Use production-domain mapping only to prove which completed deployment is live. If the release deployment is not unique, return `UNVERIFIED`.
3. Follow that same deployment ID. Do not substitute a nearby deployment by time or message.
4. Treat provider-documented success, failure, cancellation, and superseded states as terminal. Cancellation and supersession produce `FAILED` for the target release.
5. Stop at the first terminal state. Stop with `RUNNING` at the wait limit. Stop with `UNVERIFIED` if the deployment disappears, changes revision, or cannot be tied to the SHA.
6. On failure, collect at most 20 lines or 4,000 characters of read-only error evidence with secrets removed. Do not retry the deployment.

## Prove production

After deployment success, check the canonical public URL and record the UTC time, final URL, status, and one safe runtime route. Continue checking public revision evidence every 30 seconds within the original 10-minute limit when the production alias or CDN is still moving.

Require strong revision evidence for `LIVE`:

- The production domain maps to the immutable successful deployment tied to the SHA; or
- A public version endpoint, response header, build marker, or immutable asset identifies the SHA.

An HTTP 200 response, visible feature, timestamp, page title, or successful provider status alone does not prove the production revision. Report `UNVERIFIED` when the site responds but strong revision evidence is absent.

Keep runtime checks read-only. Do not log in, submit forms, create data, send messages, upload files, or call mutating APIs without separate approval.

The safe runtime route passes when it meets the repository's declared health contract. Without one, require a final same-origin URL, HTTP 2xx, and a stable page marker declared by repository instructions or the user. If no marker is declared, report the runtime check as `UNVERIFIED`. A proven revision with a failed declared runtime check produces `FAILED`.

## Report

```text
Release: LIVE | FAILED | RUNNING | UNVERIFIED
Commit: <full SHA and remote proof>
Deployment: <provider, project, ID, revision, terminal or current state>
Public URL: <URL, status, checked UTC>
Revision proof: <strong evidence or exact gap>
Runtime check: <result>
Wait: <elapsed and limit>
Actions taken: read-only
Next action: <none or one exact owner action>
```

`LIVE` means the public production target is proven to run the pushed revision. Use no softer evidence to reach that result.
