# Ryan's Codex Skills

A small public marketplace for solo developers and vibe coders who want clearer work from Codex without adding a project-management system.

The plugins add written procedures, templates, and local checks. They can make agent work more consistent, but they do not make Codex infallible or replace review, tests, backups, or product judgment. Installing this marketplace does not add a hosted service, database, account system, or background worker.

The current catalog has 7 plugins and 39 skills. Each plugin targets the Agent Plugins 1.0.0 working draft and includes Codex compatibility metadata. Agent Plugins standardizes the portable package layout for skills and MCP servers. It does not standardize marketplace installation, permissions, secrets, or client-specific user interfaces. All packages use the MIT License.

## Choose a plugin

| Plugin | Version | Best fit | What it adds |
| --- | ---: | --- | --- |
| [RAD Plugin Converter](plugins/rad-plugin-converter/) | 1.2.3 | Authors creating, auditing, or converting plugin packages | Local Agent Plugins 1.0.0 checks, safe conversions, and a reviewed publishing workflow; author review is still required |
| [RAD Brainstorm](plugins/rad-brainstorm/) | 4.1.1 | One person who wants guided idea work before planning | Text-first ideation, separate evaluation, source labels, and a small proof step; no shared canvas or guarantee of good ideas |
| [RAD Plan](plugins/rad-plan/) | 7.1.1 | Solo builders and small teams planning one bounded release | Repository-backed planning, rescue, replan, and plan review; it writes plans and does not implement code |
| [RAD Repo](plugins/rad-repo/) | 3.2.1 | Repositories used across many coding-agent sessions | An opinionated document model, handoffs, approved checks, and guarded Git shipping; checks cannot prove production health |
| [RAD PARA](plugins/rad-para/) | 1.1.2 | People who keep local notes and projects in a PARA system | PARA guidance, read-only audits, layered summaries, output help, and approved file moves; no sync service or app connector |
| [RAD Coolify](plugins/rad-coolify/) | 2.1.3 | Developers who manage self-hosted Coolify v4 deployments | Deployment guidance and local validators, plus optional client-specific MCP actions that need separate setup and credentials |
| [RAD Writer](plugins/rad-writer/) | 0.2.0 | People drafting or editing prose with an AI agent | Operation-specific writing guidance for academic, creative, technical, business, email, social, and reference text; facts and publication rules still need human review |

## What is familiar and what is specific

These plugins use known practices. They do not claim to invent PARA, Five Whys, SCAMPER, implementation plans, handoff notes, or pre-ship checks.

Their value comes from how those practices are joined and limited:

- RAD Plugin Converter creates new dual-format packages and uses a standard migration inventory for existing packages. It keeps portable metadata separate from client files and checks skill and MCP configuration before writing changes. Its local checks catch format errors, not every runtime or client issue.
- RAD Brainstorm uses familiar idea methods. Its specific focus is idea ownership: the user starts, each contribution has a source label, judgment happens later, and the result ends with a test threshold and stop signal.
- RAD Plan resembles other planning assistants and spec templates. It adds bounded repository reading, one maintained plan, outcome coverage, safe recovery fields, rescue and replan paths, plus separate mechanical and judgment checks.
- RAD Repo uses common repository instructions, handoffs, and Git checks. Its main difference is a small authority model and clone-local approval for repository validation commands.
- RAD PARA applies established second-brain methods. It puts setup, review, distillation, output assembly, and session continuity in one plugin, with approval required before a real folder reorganization.
- RAD Coolify combines familiar deployment guidance with four file-based validators. Its review path runs those checks before it judges health endpoints, service relationships, and deployment intent. Live actions depend on a separate npm MCP package and client-managed credentials.
- RAD Writer uses familiar editing practices. It separates drafting, rewriting, copyediting, proofreading, and review so the agent does not make broader changes than the request permits. It preserves supplied facts and flags missing support, but editing alone does not verify a claim.

## Important limits

Skills are instructions for an AI agent. They can improve consistency, but they cannot guarantee a correct plan, diagnosis, design, file placement, or release.

Agent Plugins 1.0.0 is still a working draft. These packages follow its current layout, but portable packaging does not mean that every client supports every skill, MCP server, or Codex-specific feature.

The bundled scanners use rules and heuristics. Their findings are evidence to review. They are not proof of code quality, document meaning, or personal productivity.

Some workflows can edit files. RAD Repo can commit and push when the user invokes its ship workflow. RAD PARA can move files after a full move plan receives approval. Each plugin README states its write boundary.

The local Python scripts have no required third-party packages. The JSON validators can use the optional jsonschema package when it is already installed.

## Add the marketplace

Use a Codex CLI build that provides the plugin commands:

~~~powershell
codex plugin marketplace add radesjardins/codex.skills
~~~

The marketplace name is radesjardins-codex-skills.

## Install plugins

Install only the plugins you want:

~~~powershell
codex plugin add rad-plugin-converter@radesjardins-codex-skills
codex plugin add rad-brainstorm@radesjardins-codex-skills
codex plugin add rad-plan@radesjardins-codex-skills
codex plugin add rad-repo@radesjardins-codex-skills
codex plugin add rad-para@radesjardins-codex-skills
codex plugin add rad-coolify@radesjardins-codex-skills
codex plugin add rad-writer@radesjardins-codex-skills
~~~

The plugins do not require each other. RAD Brainstorm, RAD Plan, and RAD Repo mention a companion only when its exact skill is available and the current work needs it. RAD PARA can share a handoff with RAD Repo when both apply.

## Example requests

- "Audit this Codex plugin for Agent Plugins 1.0.0, then convert it in place."
- "Create a new Agent Plugins 1.0.0 package with one starter skill."
- "Run a quick brainstorm and let me give my ideas first."
- "Create a full implementation plan from this repository."
- "Run RAD Repo startup and show the next task."
- "Audit this PARA folder without changing anything."
- "Review this project for Coolify deployment risks."
- "Proofread this report without changing its meaning or voice."

The plugin pages list every skill, its output, and its limits.

## Source and contributions

Everything that installs is visible under [plugins](plugins/). Issues and pull requests should include the plugin name, the request that triggered the problem, what happened, and what the user expected.

## License

MIT. See [LICENSE](LICENSE).
