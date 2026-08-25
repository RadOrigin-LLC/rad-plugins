---
name: publish-plugin
description: Use when a reviewed plugin must be added to or updated in a marketplace, published to Git, refreshed in a client, installed, or proven available to an agent.
---

# Publish a Plugin

Publish a reviewed package through explicit local, Git, client, and agent-visible gates. Keep the source usable until the installed result is proven.

## Set the authorized scope

Map the user's words to these actions. Do not ask again for an action already covered.

| Request | Authorized action |
| --- | --- |
| Check or prepare | Read-only dry run |
| Add or update in a local marketplace | Package and catalog writes |
| Commit | Commit reviewed publish paths |
| Push the approved marketplace change | Commit reviewed publish paths when needed, then push the one clear upstream |
| Refresh and prove agent visibility | Refresh, install or update, and enable the selected plugin when required for proof |
| Install, enable, or load | The named client action |
| Remove or replace an old package | Only the exact named removal |

Identify the package root, target marketplace root, client, destination, version, category, install or authentication policy, Git remote, and branch. Read the registered marketplace name from the client instead of assuming it from repository text. Use the current upstream when it is clear. Ask only when a missing or competing value would change the result.

## Companion-skill rule

RAD Plugin Converter owns package and client release gates. RAD Repo Ship can supply an approved repository Git contract.

Offer `rad-repo:ship` only when the current publish task needs that repository commit and push gate, that exact skill appears in the current available-skill list, and the user accepts the handoff. Wait for acceptance before invoking it. If the exact skill is absent or the user declines, continue the package and client work and report the Git gate as unhandled. Never invoke a companion silently.

## Run the dry run

1. Read repository instructions and inspect Git status. Stop for conflicting or unrelated changes that overlap the publish paths.
2. Audit the package:

   ```powershell
   python ../../scripts/rad_plugin_converter.py audit <package-root> --json
   ```

3. Review scripts, MCP commands, dependencies, license terms, and secret handling. Conformance does not prove package safety.
4. Inspect an existing destination before replacement. Stop when it contains unreviewed differences or a version conflict. A changed published package needs a higher version under that repository's version policy.
5. Find the canonical marketplace manifest and any required mirrors. Plan identical entries with the repository's existing schema and policy fields.
Show the target files and actions before writes when the original request did not already approve them.

## Publish

1. Copy or update only the reviewed package files. Do not merge into an unknown destination.
2. Update the canonical catalog and required mirrors. Update repository listings only when that repository requires them.
3. Re-run the package audit and a read-only marketplace audit.
4. Run the repository's targeted checks and `git diff --check`.
5. Review and stage only publish paths. Commit and push only when authorized.
6. Refresh and install through the selected client only when authorized.
   - For a Git marketplace, push first, refresh the registered marketplace, then add the requested version.
   - For a filesystem marketplace, refresh or reinstall from its configured local source without inventing a Git step.
   - When an add command does not replace the installed version, stop and report it. Do not remove the working version without explicit approval.
7. Prove three states when available:
   - Catalog state points to the intended package and version.
   - Client state shows it installed and enabled.
   - Agent state shows every expected skill in a fresh prompt or process.

Stop on a failed audit, rejected push, wrong marketplace source, missing installed version, or absent expected skill. After a successful push and failed client refresh, preserve the pushed commit and working installed version, then report the exact recovery command. Do not remove a working prior package to hide a failed replacement.

## Report

```text
Package: <name and version>
Marketplace: <root and registered name>
Audit: <pass or exact failure>
Git: <not requested, commit, and remote branch>
Client: <not requested or installed version>
Agent visibility: <not requested, proven, or unverified>
Remaining: <none or exact next action>
```
