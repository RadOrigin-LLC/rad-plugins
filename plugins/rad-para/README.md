# RAD PARA

RAD PARA is an Agent Plugins 1.0.0 package that helps one person set up, review, and use a PARA-based note system with Codex. It can make suggestions and apply approved local file moves through a dry-run ledger. Sparse context can still lead to a wrong classification.

It is best suited to folders and Markdown notes that Codex can read. It can also give instructions for tools such as Notion, Obsidian, Apple Notes, or Google Drive, but this plugin does not connect to those services or change their data through an API.

## Method credit

PARA, CODE, Progressive Summarization, Intermediate Packets, and related second-brain methods in this plugin come from the work of Tiago Forte and Forte Labs. The 12 Favorite Problems exercise is inspired by Richard Feynman.

This plugin packages guided Codex workflows around those methods. It does not claim ownership of the original methods.

## Skills

| Skill | Use it for | Main result |
| --- | --- | --- |
| [rad-para:para-organize](skills/para-organize/SKILL.md) | Setting up PARA, classifying notes, diagnosing a broken system, or planning a real folder reorganization | Advice, a classification, or an approved file-move plan |
| [rad-para:audit](skills/audit/SKILL.md) | Checking an existing authorized PARA folder without changing it | A structural report with counts, dates, suspected issues, and suggested actions |
| [rad-para:weekly-review](skills/weekly-review/SKILL.md) | Reviewing stale projects, inbox load, recent activity, and visible deadlines | A read-only weekly briefing |
| [rad-para:progressive-summarization](skills/progressive-summarization/SKILL.md) | Distilling a note, article, transcript, or set of notes | Layered emphasis and a short summary shaped by the user's goal |
| [rad-para:express-workflow](skills/express-workflow/SKILL.md) | Turning existing notes and research into an article, report, presentation, email, or other output | An outline, a draft, or a smaller first version |
| [rad-para:hemingway-bridge](skills/hemingway-bridge/SKILL.md) | Preserving the state of a notes or creative project between sessions | A handoff note with status, first action, open questions, and related material |
| [rad-para:twelve-favorite-problems](skills/twelve-favorite-problems/SKILL.md) | Creating or revising a personal capture filter | A user-owned list of open questions and a capture rule |

## How it works

The skills combine conversation with read-only folder inspection. The user supplies the PARA location or content, and Codex asks focused questions before giving a classification or report.

The filesystem reorganization path has a stricter rule:

1. Inspect the authorized root without changing it.
2. Detect any current PARA structure.
3. Read only enough content to classify unclear items.
4. Show every folder to create and every file to move.
5. Wait for explicit approval.
6. Run the approved dry-run ledger through `scripts/para_move.py`.
7. Keep the ledger and report any failed or restored paths.

The audit and weekly-review skills stay read-only.

## Local folder scanner

The plugin includes a narrow structural scanner:

~~~powershell
python .\scripts\audit-para-structure.py <para-root>
python .\scripts\audit-para-structure.py <para-root> --strict --json
~~~

It checks the four top-level categories, plain or numbered names, root-level orphan files, project names that look like topics, optional outcome markers, and configurable project-count advice. `Archive` and `Archives` are equivalent. `Inbox` and `Templates` are optional. The scan stays inside the supplied root, skips links, and reports incomplete reads.

The script does less than the conversational audit skill. It does not inspect full note meaning, staleness, deadlines, archive health, or cross-platform copies.

## Safe file moves

`scripts/para_move.py` accepts one approved root and a list of source and target paths. The dry run writes an unapproved JSON ledger. A separate approval step is required before apply. Apply rejects escapes, collisions, and links, stops on the first failure, and records restoration results in the retained ledger.

~~~powershell
python .\scripts\para_move.py --root <para-root> --move <source> <target> --dry-run --ledger <ledger>
python .\scripts\para_move.py --root <para-root> --ledger <ledger> --approve
python .\scripts\para_move.py --root <para-root> --ledger <ledger> --apply
~~~

## What is specific about it

Many PARA guides explain where Projects, Areas, Resources, and Archive fit. Other note tools focus on search, links, or capture.

RAD PARA's specific contribution is the range of guided work in one small package:

- safe setup and classification;
- a read-only structural audit and weekly review;
- layered note distillation;
- assembly of existing notes into an output;
- a notes-focused session handoff;
- a personal question list used as a capture filter.

The real-file workflow also requires one complete move plan before any reorganization. That gives the user a review point when folder names alone do not tell the full story.

## Limits

- Folder names, file dates, and keyword scans are incomplete evidence. A stale timestamp may describe a finished or intentionally quiet project.
- Project-count and staleness thresholds are working rules used by the skills. They are prompts for review, not measured health standards.
- The audit can misclassify a topic, responsibility, or project when the available context is thin.
- Progressive Summarization changes emphasis. It can omit a point the user considers important.
- Express can draft from supplied notes, but it cannot verify claims that lack sources.
- The plugin has no sync engine, scheduler, reminders, search index, live Notion connection, or Obsidian extension.
- Cross-platform consistency can be checked only when the user gives access to each copy.
- The user remains responsible for backups and final file placement.

When a Git-based handoff could help, RAD Repo is optional. Offer the exact needed `rad-repo:<skill>` only when that skill appears in the current available-skill list and the current task needs it. Invoke it only after the user accepts. If the exact skill is absent or the user declines, keep the bridge standalone and follow this plugin's handoff instructions.

## Install

~~~powershell
codex plugin add rad-para@radesjardins-codex-skills
~~~

Example requests:

- "Help me classify these notes. Explain each uncertain choice."
- "Audit this PARA folder. Keep the scan read-only."
- "Show me the full file-move plan and wait for approval."
- "Apply Progressive Summarization to these notes for my current project."
- "Use my saved notes to build a short report outline."

## License

MIT. See [LICENSE](LICENSE).
