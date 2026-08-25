# Plan: RAD Plugin Marketplace Review and Repair

**Status:** COMPLETED
**Updated:** 2026-08-22
<!-- rad-plan-contract: 7.1 -->

> **How to read this plan:** The Release map shows where this work fits. Milestones
> are shippable parts of Now. Each task gives an agent the exact outcome, files,
> dependencies, proof, and recovery need. Stop conditions require owner input.

## Objective

Make all seven public RAD plugins lean, accurate, safe, and clear about how they work alone and with another loaded RAD plugin.

**End goal:** Each plugin keeps its full job with less stale or repeated guidance, focused checks prove its important claims, all public copy matches the package, and shared packages match their private copies.

## Release map

- **Now - Marketplace repair (this plan):** Complete the nine approved repair items, review each package, and prepare one local release candidate.
- **Next - Runtime evaluation:** Run selected skills in supported clients and record trigger, behavior, and live-service evidence.
  - Test the companion suggestions in a client that has the named plugins loaded.
  - Test Coolify read and write paths against a disposable instance.
  - Recheck whether a shared plugin-evaluation harness has enough reuse to become a package.
- **Later - New plugins only after proof:** Add a package only when current plugins cannot solve a repeated user problem.
  - Review private candidates before creating a public replacement.
  - Keep optional services and accounts out of the core marketplace.

## Scope

**In scope:**

- `rad-brainstorm`, `rad-coolify`, `rad-para`, `rad-plan`, `rad-plugin-converter`, `rad-repo`, and `rad-writer`.
- All skill instructions, linked references, scripts, focused tests, package READMEs, portable manifests, Codex cards, and marketplace copy touched by the approved repairs.
- Equivalent updates to packages that already exist in both `R:\Dev\skills\codex` and `R:\Dev\skills\codex.public`.
- The existing uncommitted RAD Repo 3.3.0 work, preserved and finished in place.

**Out of scope / non-goals:**

- Publishing, installing, committing, pushing, or changing a live Coolify or PARA system.
- Adding a public or private plugin to the other marketplace when it does not already exist there.
- Adding a required account, database, background service, or broad process.
- Rewriting unrelated user changes or hiding unverified runtime behavior.

## Key assumptions

- 2026-08-22: Agent Plugins 1.0.0 is the current published release. Version 1.1.0 is a working draft.
- 2026-08-22: The marketplace has seven public plugins. The published branch has 39 skills; the current RAD Repo 3.3.0 work raises the working-tree total to 40.
- 2026-08-22: The public audience values low setup cost, clear limits, local evidence, and human control.
- 2026-08-22: A skill can suggest another plugin only when the exact companion skill appears in the current available-skill list and the user accepts the handoff.
- 2026-08-22: Stable plugin procedures belong in skill files. Facts that change with a product release require a live check or a dated primary source.
- 2026-08-22: Shared package changes must be equivalent across both repositories while marketplace-specific metadata stays local.

## Global constraints

- Preserve unrelated work and the existing RAD Repo 3.3.0 changes.
- Use `apply_patch` for edits. Do not commit, push, publish, install, or mutate an external service.
- Keep each skill below 500 lines. Prefer a short router plus references over copied vendor documentation.
- Never print a suspected secret value. Never place a destructive host command in a quick-fix path.
- Run only the focused checks named by the changed task. A green targeted check ends that package pass.
- Run the shared marketplace comparison before and after a shared-package task. Stop on unrelated drift that cannot be reconciled.
- Keep plugin ownership clear. One plugin can offer a loaded companion, but cannot silently invoke it or transfer authority.

## Outcome coverage

| Outcome | Covered by | Final proof |
|---|---|---|
| O1 - Coolify guidance and tools do not leak secrets, use false routes, or offer unsafe shortcuts | T1, T2 | Coolify redaction and validator tests pass; reviewed docs match current primary sources |
| O2 - PARA and Converter changes fail safely and leave clear recovery evidence | T4, T5 | Disposable failure fixtures pass and no write escapes the approved root |
| O3 - Plugin claims, schemas, and behavior cases match their real contracts | T3, T6, T7, T8 | Focused metadata, semantic, behavior, and RAD Repo checks pass |
| O4 - All seven packages are lean, honest, synchronized where shared, and clear about companions | T9 | Seven package audits pass, shared drift is zero, README links resolve, and reviewed counts and versions agree |

## Milestones

| # | Milestone | Ships | Key artifacts |
|---|---|---|---|
| M1 | Remove unsafe and false guidance | Secret-safe Coolify, current contracts, and bounded PARA operations | Coolify tests and skills, Agent Plugins copy, PARA helper and tests |
| M2 | Strengthen package proof | Safer conversion, semantic plan checks, Brainstorm evidence, and finished RAD Repo 3.3.0 | Converter, Plan, Brainstorm, Writer, and Repo checks |
| M3 | Prepare one release candidate | Accurate READMEs, cards, companion rules, versions, and marketplace totals | Seven packages and marketplace metadata |

## Tasks

### M1 - Remove unsafe and false guidance

*After this ships: The highest-risk guidance and public contract errors are gone.*

- **T1 - Redact Coolify findings and remove unsafe shortcuts**
  - **Objective:** Ensure validators never echo suspected secret values and replace destructive or unpinned host commands with checked procedures.
  - **Files:** [existing] `plugins/rad-coolify/scripts/lint-dockerfile.py`; [existing] `plugins/rad-coolify/skills/coolify-security/SKILL.md`; [existing] `plugins/rad-coolify/skills/coolify-infrastructure/SKILL.md`; [existing] `plugins/rad-coolify/skills/coolify-observability/SKILL.md`; [new] `plugins/rad-coolify/tests/test_lint_dockerfile.py`
  - **Depends on:** none
  - **Done when:** Text and JSON findings identify only the key, file, and line; no reviewed quick path runs a mutable remote script as root, recursively deletes Coolify data, prunes volumes, or uses an unpinned production image.
  - **Validate:** `python plugins\rad-coolify\tests\test_lint_dockerfile.py` plus a bounded search for the removed command forms in changed Coolify files.
  - **Rollback:** Use a forward documentation correction. Never restore secret output or an unsafe shortcut.

- **T2 - Correct and trim Coolify API, CLI, Railpack, and action guidance**
  - **Objective:** Keep stable procedures, verify changing facts from current official sources, correct deploy routes and CLI commands, and make every live write show the exact target and need user acceptance.
  - **Files:** [existing] `plugins/rad-coolify/README.md`; [existing] `plugins/rad-coolify/skills/coolify-actions/SKILL.md`; [existing] `plugins/rad-coolify/skills/coolify-status/SKILL.md`; [existing] `plugins/rad-coolify/skills/coolify-deploy/SKILL.md`; [existing] `plugins/rad-coolify/skills/coolify-cicd/SKILL.md`; [existing] `plugins/rad-coolify/skills/coolify-databases/SKILL.md`; [existing] `plugins/rad-coolify/skills/coolify-security/SKILL.md`; [new] `plugins/rad-coolify/tests/test_plugin_contract.py`
  - **Depends on:** T1
  - **Done when:** Deploy examples use the documented `/api/v1/deploy` contract; CLI examples use current syntax; Railpack is described as a Git-only beta; changing inventories are checked at use time; live mutations require the exact instance, resource, action, and user acceptance; public and private copies match.
  - **Validate:** Check only the current Coolify pages at `/docs/api-reference/api/deployments/deploy-by-tag-or-uuid`, `/docs/cli/deploy-applications`, `/docs/applications/builds/railpack`, `/docs/applications/builds/overview`, `/docs/api-reference/api/applications/update-application-by-uuid`, `/docs/knowledge-base/server/build-server`, and `/docs/integrations/mcp`; record each title, URL, and the 2026-08-22 check date in task evidence; run `python plugins\rad-coolify\tests\test_plugin_contract.py` and one read-only shared marketplace comparison. Stop on a conflict between current primary sources and newer intentional private work.
  - **Rollback:** Use a forward correction for an upstream fact error. Stop before any MCP identity, transport, credential, or external-resource change.

- **T3 - Correct the Agent Plugins release status**
  - **Objective:** State that 1.0.0 is published and 1.1.0 is a working draft everywhere the marketplace or Converter describes the standard.
  - **Files:** [existing] `README.md`; [existing] `plugins/rad-plugin-converter/README.md`; [existing] `plugins/rad-plugin-converter/plugin.json`; [existing] `plugins/rad-plugin-converter/.codex-plugin/plugin.json`; [existing] `plugins/rad-plugin-converter/references/agent-plugins-v1.md`
  - **Depends on:** none
  - **Done when:** No active marketplace or Converter copy calls 1.0.0 a draft, and each status statement links or points to the current specification.
  - **Validate:** Check the 2026-08-22 status against `https://github.com/agentplugins/agent-plugins-spec`; run a bounded case-insensitive search for `working draft|pre-release|prerelease|draft` and inspect every remaining marketplace or Converter match.
  - **Rollback:** Use a forward copy correction if the upstream status changes again.

- **T4 - Make PARA scans, classifications, and moves safe and consistent**
  - **Objective:** Use one approved root, one plan-first move contract, consistent folder variants, and advisory project-count guidance.
  - **Files:** [existing] `plugins/rad-para/README.md`; [existing] `plugins/rad-para/scripts/audit-para-structure.py`; [existing] `plugins/rad-para/skills/audit/SKILL.md`; [existing] `plugins/rad-para/skills/weekly-review/SKILL.md`; [existing] `plugins/rad-para/skills/para-organize/SKILL.md`; [new] `plugins/rad-para/scripts/para_move.py`; [new] `plugins/rad-para/tests/test_move_contract.py`; [new] `plugins/rad-para/tests/test_audit_para_structure.py`
  - **Depends on:** none
  - **Done when:** Scans stay inside the approved root and report incomplete reads; the scanner accepts documented folder variants; move apply requires an approved dry-run ledger and rejects escapes, collisions, links, and partial silent success; inflated claims and conflicting project counts are removed; public and private copies match.
  - **Validate:** `python -m unittest discover -s plugins\rad-para\tests -p "test_*.py"`; the tests must use a temporary fixture root and cover a successful dry run and apply, an unapproved apply, an escape, a collision, a link, an injected failure after one move, restored original paths, a retained ledger, and the manual-recovery stop when restoration is incomplete. On Windows, create a real link only when the process has permission; otherwise use a capability check with explicit skip evidence plus a mocked link-boundary check. No test may use a real PARA root. Then run one read-only shared marketplace comparison.
  - **Rollback:** Revert only the package changes through a reviewed patch. Retain any move ledger when recovery is incomplete and stop for manual repair.

### M2 - Strengthen package proof

*After this ships: Core package behavior has direct checks without adding a service or large framework.*

- **T5 - Make Converter writes transactional and YAML handling conforming**
  - **Objective:** Prevent partial create or conversion output, add a true dry run, and accept valid Agent Skills YAML metadata.
  - **Files:** [existing] `plugins/rad-plugin-converter/scripts/convert.py`; [existing] `plugins/rad-plugin-converter/scripts/frontmatter.py`; [existing] `plugins/rad-plugin-converter/scripts/rad_plugin_converter.py`; [existing] `plugins/rad-plugin-converter/scripts/tests/test_convert.py`; [existing] `plugins/rad-plugin-converter/scripts/tests/test_create.py`; [existing] `plugins/rad-plugin-converter/scripts/tests/test_frontmatter.py`
  - **Depends on:** T3
  - **Done when:** Pre-write failures change nothing; an injected mid-write failure restores original bytes and removes only transaction-created files; dry run lists planned writes without changing hashes; quoted or dotted metadata keys, comments, and normal YAML quoting pass; public and private copies match.
  - **Validate:** `python -m unittest discover -s plugins\rad-plugin-converter\scripts\tests -p "test_*.py"` and one read-only shared marketplace comparison.
  - **Rollback:** Stop later writes on recovery failure and retain exact recovery evidence. Do not traverse or replace a link.

- **T6 - Reject contradictory RAD Plan review results**
  - **Objective:** Add semantic validation for risk counts, verdicts, blocking severities, and stack verification sources.
  - **Files:** [existing] `plugins/rad-plan/scripts/validate-json.py`; [existing] `plugins/rad-plan/references/subagent-prompts/risk-assessment.schema.json`; [existing] `plugins/rad-plan/references/subagent-prompts/stack-eval.schema.json`; [existing] `plugins/rad-plan/tests/test_validate_json.py`
  - **Depends on:** none
  - **Done when:** APPROVE cannot include critical or high issues, blocking issues cannot use medium or low severity, summary counts match arrays, and compatibility cannot be verified without sources; public and private copies match.
  - **Validate:** `python plugins\rad-plan\tests\test_validate_json.py` and one read-only shared marketplace comparison.
  - **Rollback:** Keep semantic rules outside JSON Schema when the offline validator cannot express them safely.

- **T7 - Add Brainstorm behavior evidence and Writer companion guidance**
  - **Objective:** Prove Brainstorm's user-first and stop-before-build claims, and define the PARA-to-Writer handoff without changing Writer's focused job.
  - **Files:** [existing] `plugins/rad-brainstorm/README.md`; [existing] `plugins/rad-brainstorm/skills/brainstorm-session/SKILL.md`; [existing] `plugins/rad-brainstorm/skills/software-design/SKILL.md`; [existing] `plugins/rad-brainstorm/tests/test_plugin_contract.py`; [new] `plugins/rad-brainstorm/tests/behavior-cases.md`; [existing] `plugins/rad-writer/README.md`; [existing] `plugins/rad-writer/skills/writing/SKILL.md`
  - **Depends on:** none
  - **Done when:** Focused cases cover user input before suggestions, stable idea IDs, source labels, saved evidence, and stop before plan or code; Writer states that PARA owns gathering and outlining while Writer owns the accepted writing operation; suggestions require the exact loaded skill and user acceptance.
  - **Validate:** `python -m unittest discover -s plugins\rad-brainstorm\tests -p "test_*.py"`; the contract test must assert each behavior case and the exact loaded-skill plus user-acceptance rule. Parse `plugins\rad-writer\tests\writing-cases.json` as JSON and inspect the Writer handoff text against the stated PARA and Writer ownership boundary.
  - **Rollback:** Remove a behavior case that cannot produce a stable pass or fail signal after one bounded correction.

- **T8 - Finish and verify RAD Repo 3.3.0**
  - **Objective:** Complete the existing snapshot, recall, scoped-validation, handoff, version, documentation, and test work while keeping Git Markdown authoritative.
  - **Files:** [existing] `.rad-repo.json`; [existing] `plugins/rad-repo/plugin.json`; [existing] `plugins/rad-repo/.codex-plugin/plugin.json`; [existing] `plugins/rad-repo/README.md`; [existing] `plugins/rad-repo/references/shelf-spec.md`; [existing] `plugins/rad-repo/scripts/README.md`; [existing] `plugins/rad-repo/scripts/pre_ship.py`; [existing] `plugins/rad-repo/scripts/repo-doctor.py`; [existing] `plugins/rad-repo/scripts/repo-scan.py`; [existing] `plugins/rad-repo/scripts/repo_contract.py`; [new] `plugins/rad-repo/scripts/repo-snapshot.py`; [new] `plugins/rad-repo/scripts/memory-recall.py`; [existing] `plugins/rad-repo/scripts/tests/test_pre_ship.py`; [existing] `plugins/rad-repo/scripts/tests/test_repo_contract.py`; [existing] `plugins/rad-repo/scripts/tests/test_repo_scan.py`; [new] `plugins/rad-repo/scripts/tests/test_repo_snapshot.py`; [new] `plugins/rad-repo/scripts/tests/test_memory_recall.py`; [existing] `plugins/rad-repo/skills/ship/SKILL.md`; [existing] `plugins/rad-repo/skills/startup/SKILL.md`; [existing] `plugins/rad-repo/skills/wrapup/SKILL.md`; [new] `plugins/rad-repo/skills/recall/SKILL.md`; [new] `plugins/rad-repo/skills/recall/agents/openai.yaml`; [existing] `plugins/rad-repo/templates/handoff.md`
  - **Depends on:** none
  - **Done when:** All current 3.3.0 files agree on version and behavior; recall stays read-only and bounded to decisions and lessons; snapshot and scoped validation return clear JSON evidence; `.rad-repo.json` keeps `allow_empty` false and an unmatched changed path cannot pass with no validation; speculative speed claims are removed or measured; public and private copies match. Ryan's approval of this plan authorizes this repository-contract correction.
  - **Validate:** Run `python plugins\rad-repo\scripts\tests\test_pre_ship.py`, `python plugins\rad-repo\scripts\tests\test_repo_contract.py`, `python plugins\rad-repo\scripts\tests\test_repo_scan.py`, `python plugins\rad-repo\scripts\tests\test_repo_snapshot.py`, and `python plugins\rad-repo\scripts\tests\test_memory_recall.py`. Cover scope selection, an unmatched path, empty-scope blocking, recall and snapshot JSON, handoff fields, and timing fields. Do not run `run_all.py`. Then run one read-only shared marketplace comparison.
  - **Rollback:** Preserve the dirty RAD Repo 3.3.0 snapshot as the protected starting state. If a correction touches another path or conflicts with that intent, stop that correction and report the exact conflict.

### M3 - Prepare one release candidate

*After this ships: The local marketplace tells the truth about all seven plugins and their optional handoffs.*

- **T9 - Align all READMEs, cards, manifests, versions, and marketplace copy**
  - **Objective:** Review the integrated tree, remove stale or repeated claims, add conditional companion guidance, update changed-package patch versions and totals, and produce local release evidence.
  - **Files:** [existing] `README.md`; [existing] `marketplace.json`; [existing] `.agents/plugins/marketplace.json`; [existing] `plugins/rad-brainstorm/README.md`; [existing] `plugins/rad-coolify/README.md`; [existing] `plugins/rad-para/README.md`; [existing] `plugins/rad-plan/README.md`; [existing] `plugins/rad-plugin-converter/README.md`; [existing] `plugins/rad-repo/README.md`; [existing] `plugins/rad-writer/README.md`; [existing] `plugins/*/plugin.json`; [existing] `plugins/*/.codex-plugin/plugin.json`
  - **Depends on:** T1, T2, T3, T4, T5, T6, T7, T8
  - **Done when:** Every capability and limit matches current files; the marketplace reports seven plugins and 40 skills; changed package versions agree across both manifests; companion text uses the loaded-skill and user-acceptance rule; README links resolve; all seven package audits pass; every shared package matches.
  - **Validate:** Run `python plugins\rad-plugin-converter\scripts\rad_plugin_converter.py marketplace . --json` and assert exactly seven successful packages with zero errors and warnings; run the shared marketplace comparison and assert every shared package is in sync; parse `marketplace.json`, `.agents/plugins/marketplace.json`, every `plugins/*/plugin.json`, and every `plugins/*/.codex-plugin/plugin.json` with PowerShell `ConvertFrom-Json`; assert seven catalog entries, 40 discovered `SKILL.md` files, and equal versions across each changed package's two manifests; resolve each relative Markdown link in `README.md` and `plugins/*/README.md` with `Test-Path`; search companion text for the exact available-skill and user-acceptance rule; run `git diff --check`; then run `$paths = git ls-files --others --exclude-standard; $bad = foreach ($path in $paths) { Select-String -Path $path -Pattern '[ \t]+$' }; if ($bad) { $bad; exit 1 }` to cover untracked text. Every check must report zero errors and warnings.
  - **Rollback:** Hold the release candidate when evidence is incomplete. Use a new reviewed correction for copy or version mistakes.

## Checkpoints

### After M1

- **Gate:** T1 through T4 pass focused checks, shared Coolify and PARA copies match, and no external resource or real PARA tree was changed.
- **Validate:** Review the test outputs, source links, shared comparison, and changed-file diff.
- **Rollback:** Hold later package work if a safety fixture or shared comparison fails.

### After M2

- **Gate:** T5 through T8 pass focused checks and all four shared packages changed in this milestone match their private copies.
- **Validate:** Review each agent report, focused output, shared comparison, and package diff before marking the task complete.
- **Rollback:** Hold M3 if a semantic, transaction, behavior, or RAD Repo contract remains unproved.

### After M3

- **Gate:** T9 reports seven conforming packages, 40 skills, accurate copy, valid links and JSON, and zero shared drift.
- **Validate:** Review the final audit, sync result, targeted package outputs, and exact changed paths.
- **Rollback:** Keep the changes local and report any failed gate. Publishing, committing, or pushing needs separate owner direction.

## Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Parallel agents edit the same file | Med | High | Give each agent exclusive package paths; root owns shared marketplace files and integrated copy |
| Coolify documentation changes during the work | High | Med | Cite current official sources and keep changing facts out of stable skill instructions |
| Shared public and private packages drift | Med | High | Compare before and after each shared package change and review the exact differing files |
| Converter or PARA recovery touches unrelated files | Low | High | Use disposable fixtures, exact roots, transaction ledgers, and stop on links or unknown state |
| Existing RAD Repo work is overwritten | Low | High | Treat the current dirty files as the starting implementation and preserve their intent and diff |
| Added checks make a plugin heavier | Med | Med | Add only direct checks for observed defects and keep routing skills short |

## Validation

- Each task's focused command proves its changed behavior.
- `python plugins\rad-plugin-converter\scripts\rad_plugin_converter.py marketplace . --json` reports seven successful packages with zero errors and warnings.
- `python R:\Dev\skills\codex\plugins\rad-marketplace-sync\scripts\rad_marketplace_sync.py R:\Dev\skills\codex R:\Dev\skills\codex.public --json` reports every shared package in sync.
- All local README links resolve and all JSON files parse.
- `git diff --check` reports no whitespace errors in reviewed changes.

## Stop conditions

- A task would delete real data, change a live service, expose a credential, publish, install, commit, push, or rewrite history.
- Shared drift contains newer unrelated work that cannot be reconciled without an owner choice.
- A transaction or move would cross the selected root, traverse a link, overwrite an unknown file, or cannot restore prior state.
- A RAD Repo correction conflicts with the preserved user-owned 3.3.0 implementation and no safe narrow merge exists.
- A current client or upstream contract cannot be verified from a primary source or local evidence.

## Durable follow-ups

- A later runtime-evaluation pass should test conditional companion suggestions in an installed client. This plan proves source contracts only.

## Shipped

- 2026-08-10: The first six-plugin marketplace audit completed. All six packages passed structural audits, and the draft identified the main Converter, Coolify, PARA, Plan, Brainstorm, and Repo gaps.
- 2026-08-20: RAD Writer 0.2.0 joined the public marketplace with nine focused writing behavior cases.
