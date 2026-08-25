# RAD Repo

RAD Repo is an Agent Plugins 1.0.0 package that helps Codex keep a repository understandable between sessions. It uses an opinionated document model, an evidence-based handoff, repository-declared checks, and a guarded Git shipping flow. Its scans can find review targets, but they cannot prove code quality or production health.

It is for one person or a small team that works with coding agents over many sessions. It can also bring an older repository into the model without erasing useful local documents.

## Skills

| Skill | Use it for | Main result |
| --- | --- | --- |
| [rad-repo:startup](skills/startup/SKILL.md) | Starting a work session in a managed repository | A read-only briefing with Git state, document trust, current focus, and one next task |
| [rad-repo:wrapup](skills/wrapup/SKILL.md) | Stopping work without losing the exact resume point | An updated docs/handoff.md and a closure report |
| [rad-repo:ship](skills/ship/SKILL.md) | Reviewing, checking, committing, and pushing the intended work | A pushed commit or a clear blocked result |
| [rad-repo:verify-release](skills/verify-release/SKILL.md) | Checking whether a pushed revision reached production | A bounded, read-only LIVE, FAILED, RUNNING, or UNVERIFIED result |
| [rad-repo:doctor](skills/doctor/SKILL.md) | Explaining missing or untrusted repository validation | A read-only report of command sources, path scopes, approval state, and plugin resources |
| [rad-repo:complexity-audit](skills/complexity-audit/SKILL.md) | Finding code areas that deserve maintenance review | Five to ten ranked hotspots with evidence, risk, and test needs |
| [rad-repo:recall](skills/recall/SKILL.md) | Recalling a past repository decision or lesson for a task | Up to five source-linked records with scope, status, verification, and stale state |
| [rad-repo:repo-init](skills/repo-init/SKILL.md) | Adding the minimum document container to a new repository | AGENTS.md, docs/handoff.md, and docs/archive without invented product content |
| [rad-repo:adopt](skills/adopt/SKILL.md) | Bringing an established repository onto the model | An evidence-led document map, approved moves, verified commands, and a new handoff |
| [rad-repo:repo-align](skills/repo-align/SKILL.md) | Running a deeper, opt-in document and instruction cleanup | Mechanical findings plus owner-approved routing, archive, or wording changes |

## The context model

RAD Repo gives each kind of information a preferred home:

| Level | Main source | Purpose |
| --- | --- | --- |
| L0 | Root and scoped AGENTS.md files | Commands, constraints, and path-specific agent rules |
| L1 | docs/handoff.md | Current state, validation evidence, next action, and watchouts |
| L2 | docs/decisions.md and docs/lessons.md | Settled choices and proven lessons |
| L3 | PRD, plan, design, architecture, API, and active initiative files | Product intent, approved future work, and current system facts |
| L4 | docs/archive | Deliberately retrieved history |

The root instructions provide defaults. A closer AGENTS.md can add rules for its subtree. RAD Repo tries to keep startup context small, then reads deeper documents only when the task or selected profile needs them.

The core profile is the routine default. The full profile adds deeper document review. A first adoption recommends one full pass so the existing document set can be mapped.

## Repository checks and local trust

Validation commands come from labeled commands in the applicable AGENTS.md files and optional .rad-repo.json entries.

RAD Repo doctor shows the exact commands and their sources. The owner approves the command fingerprint once per clone. Approval is stored in local Git settings and expires when a command changes.

The pre-ship gate checks staged Git content for:

- high-confidence secret patterns;
- protected paths;
- unexpected generated output;
- configured file-size limits;
- unreviewed contract changes;
- missing or unapproved validation commands;
- failed validation commands.

Ship stages reviewed paths. It does not use git add -A, and it stops after push. Release verification is a separate opt-in skill, so deployment waiting does not extend the shipping workflow.

## What is specific about it

Many repository tools use instruction files, handoff notes, documentation checks, or pre-commit gates. RAD Repo uses the same basic parts.

Its main difference is the authority and trust model. Each fact has an expected document owner. The current handoff stays short. Commands are discovered by path and approved locally before a shipping workflow runs them.

RAD Repo also keeps code-hotspot review separate from routine work. The complexity audit uses Git churn and file size to choose a few files for human or agent review. It does not add a universal code score or a complexity gate to every session.

Durable recall stays in Git. New decision and lesson lines can carry a stable ID,
scope, source, verification date, stale date, and supersession link. The recall skill
uses bounded keyword search over those Markdown files. There is no required memory
service or generated index.

## Write and Git boundaries

- Startup, recall, doctor, and complexity-audit are read-only.
- Wrapup updates the handoff. Normal wrapup does not commit. Wrapup and commit creates one local documentation commit.
- Adopt and repo-align show document moves and judgment-based edits before applying them.
- Ship authorizes a normal commit and push for the reviewed work. It does not authorize force-push, merge, deployment, deletion, or branch switching.
- Verify-release is read-only. It does not trigger, retry, restart, cancel, promote, or roll back a deployment.
- User-owned instruction text is preserved unless the owner approves a specific rewrite.

## Limits

- The document model is opinionated. A repository with an effective local model may need mapping and links instead of renaming.
- Freshness, contradiction, redundancy, vocabulary, and hotspot reports use mechanical or lexical rules. Review every finding before changing an authority document.
- The complexity audit ranks review value from churn, size, nearby tests, and existing quality signals. It does not measure semantic complexity across every language.
- Clone-local command approval does not make an unsafe command safe. The owner must inspect the command first.
- The pre-ship gate checks the staged state and declared validations. It cannot prove production health.
- RAD Repo does not add a task database, code index, vector store, background service, or generated wiki.

RAD Repo names a RAD Plan skill only when that exact skill is available and repository evidence shows a planning need. It waits for the owner before invoking it.

## Install

~~~powershell
codex plugin add rad-repo@radesjardins-codex-skills
~~~

Example requests:

- "Run RAD Repo startup and show the next task."
- "Run RAD Repo doctor. Explain every validation command before asking me to trust it."
- "Recall what this repo decided about authentication."
- "Audit code complexity. Keep it read-only and rank only the top five files."
- "Adopt this existing repository. Show every document move before making it."
- "Ship the reviewed changes."

## Scripts

The plugin includes standard-library Python tools for contract discovery, command trust, staged checks, document signals, vocabulary, and code hotspots. See [scripts/README.md](scripts/README.md) for the exact checks and exit behavior.

## License

MIT. See [LICENSE](LICENSE).
