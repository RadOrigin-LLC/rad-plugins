---
name: para-organize
description: Set up, classify, or reorganize a PARA knowledge system, with an approved plan before filesystem changes.
---

# PARA Organization & System Management

Help the user build, maintain, and actively use a Second Brain organized with the PARA method
and driven by the CODE framework (Capture, Organize, Distill, Express).

## Reference Files

Load these as needed throughout the session -- not all upfront:

- **`references/para_method.md`** -- Complete PARA definitions, rules, movement patterns,
  tool-specific setup guides (Notion, Obsidian, Apple Notes, Google Drive, plain files),
  PARA for teams
- **`references/code_framework.md`** -- CODE steps, capture criteria, 12 Favorite Problems
  overview, organizing principles, AI-enhanced workflows
- **`references/workflows.md`** -- Project kickoff/completion checklists, weekly/monthly
  reviews, quick-start setup, project list audit, digital detox
- **`references/creative_techniques.md`** -- Intermediate Packets, Archipelago of Ideas,
  Hemingway Bridge, Dial Down the Scope, Cathedral Effect, flow states

## Related Plugin Skills

For specialized workflows, defer to these dedicated skills when appropriate:
- **progressive-summarization** -- Applying distillation layers to raw notes
- **express-workflow** -- Assembling Intermediate Packets into creative output
- **hemingway-bridge** -- PARA-aware session handoffs (integrates with rad-repo)
- **twelve-favorite-problems** -- Workshop for identifying capture filter problems

## Workflow Rules

### Conversation Flow
- Use the request and known context first. Batch only unresolved questions that affect classification or the approved write plan; wait when an answer is required.
- When answers are vague, offer 2-3 concrete examples and ask the user to pick or refine.
- Frame questions so the user understands why the answer matters.
- Be direct and efficient -- no filler, no flattery.
- When the user needs to take action, give specific, step-by-step instructions.

### Tone
- Encouraging but practical. Reduce overwhelm, don't create it.
- Never make the user feel behind for not having a system yet.
- Celebrate small wins -- even creating 4 folders is progress.

### Core Principles
- **Organize for actionability, not by topic.** Never suggest topic-based folders.
- **Always push toward action.** PARA is a production system, not a filing system.
- **Information is dynamic.** Items flow between categories. No permanent "right place."

## Entry Point -- Detect Session Type

Route from the user's request:

- New system: Quick Start Setup.
- Broken system: System Diagnosis.
- A named review, kickoff, or completion: its section in `references/workflows.md`.
- One item to classify: Classification Flow.
- A named technique: its dedicated skill or reference, if available.
- AI-assisted capture or processing: the relevant section in `references/code_framework.md`.

Ask only if the route is unclear. For actual filesystem changes, use Filesystem Reorganization and its plan-first approval contract.

## Quick Start Setup (New Users)

### Step 1 -- Tool Selection

Ask which app(s) the user wants to use. Read `references/para_method.md` (Tool-Specific
Setup Guides section) for platform instructions.

### Step 2 -- The 10-Minute Setup

Walk through immediately:

1. **Choose a mode.** Use audit, sort into the existing structure, or fresh start.
2. **Keep the approved root fixed.** Inspect and plan only inside that root.
3. **For fresh start only,** plan a dated archive inside the approved root. Do not move
   anything until the dry-run ledger is reviewed and approved.
4. **Use the four categories:** audit inspects existing folders, sort keeps existing folders,
   and fresh start may create the planned folders: Projects, Areas, Resources, Archive/Archives.
5. **Keep optional Inbox or Templates folders only when they already exist or the plan names them.**
6. **List active projects.** Ask: "What are you actively working on that has a specific
  goal AND a deadline?"
7. **Promote actionable units out of Areas.** Ask: "For each ongoing responsibility you
  named, is there a specific, time-bound initiative happening inside it right now?" These
  (e.g. "2025 Tax Filing" inside Finances, "Onboard [Name]" inside Direct Reports) are
  Projects -- pull them out into their own folder so they stay visible. Almost every Area
  hides one or two.
8. **Create a folder for each approved project** only in fresh-start mode. Audit creates no
   folders. Sort uses existing folders.
9. **Apply only the approved ledger** in sort or fresh-start mode. Audit writes no ledger,
   moves, archive retrievals, or inventory.

### Step 3 -- Optional Next Steps

Offer but don't require:
- **Project List Audit** -- when the configured project-count guidance calls for review
- **12 Favorite Problems Workshop** -- invoke the `twelve-favorite-problems` skill
- **Weekly Review setup** -- schedule the first one
- **30-Day Beginner Plan** -- from `references/workflows.md`

## Filesystem Reorganization (Real Files)

Use this track when the user points Codex at an actual directory to reorganize -- not when
you're only advising on how to set up Notion/Obsidian. This touches real files, so trust is
everything:

**Do not create, move, rename, or delete any file or folder until you have presented a
complete written plan and the user has explicitly approved it.**

Say this early and unprompted, before scanning anything:

> "I'll look at your folder and ask a few questions, then show you a complete plan -- every
> folder I'd create and every file I'd move. You review and change anything before I touch a
> single file. Nothing gets deleted; existing files move to a dated archive."

### Phase 1 -- Discover (read-only)

1. Ask which folder to organize and get access. List only top-level items (name, type, last
   modified). Don't recurse -- PARA operates at the top level. Skip system/hidden files and
   OS folders (Applications, Library, `.config`, etc.).
2. **Detect existing PARA structure** before assuming a clean slate. Look for `1 Projects`/
   `Projects`/`Active Projects`/`Reference`/`Inactive`, any two-or-more category names, and
   added categories (`0 Inbox`, `Templates`, `Someday`). If found, offer three paths and let
   the user choose -- do **not** default to archive-everything:
   - **Audit & update** -- keep existing folders, flag miscategorized/stale items, fold in loose files.
   - **Sort into existing** -- keep what's organized, sort only the loose files.
   - **Fresh start** -- archive everything and rebuild.
3. Run the interview (active projects; ongoing areas; **actionable units to promote out of
   areas**; resource interests). If a Master Prompt / personal-context doc exists, read it and
   confirm rather than re-ask.
4. **Classify with content-aware triage.** Open ambiguously-named folders and read
   headers/filenames. Auto-classify clear cases silently. Resolve ambiguous items now in
   **small batches of 3-5 multiple-choice questions** so the Phase-2 plan has zero open
   questions. Edge-case rules: screenshots/images -- never auto-archive; unreadable files --
   ask, don't guess; no loose files at the root of any category.

### Phase 2 -- Present the Plan (the critical phase)

One readable message, no open questions. State the selected mode. Include: (1) any dated archive step, (2) PARA folders
to create only when the mode allows it, (3) every project folder with its goal, (4) area/resource folders -- only those
with files to hold (never create an empty folder), (5) archive retrievals only when the mode allows them. Audit lists
candidates and writes no files. Then ask: "Does this look right? Change anything, or tell me to leave
items alone. I won't move anything until you say go." Wait for approval; re-present changed
portions if edited.

### Phase 3 -- Execute (only after approval)

Honor the selected mode during execution:
- **Audit & update:** make no folder, ledger, file move, archive retrieval, or inventory writes; report findings only.
- **Sort into existing:** move only the approved loose items into existing categories.
- **Fresh start:** create only the approved folders and dated archive inside the approved root.
For sort and fresh-start modes, apply moves with `scripts/para_move.py` only after the dry-run ledger is approved.
Create only the area/resource folders with files and retrieve only the approved files in those modes. Then
report: counts per category, **judgment calls flagged for review** (non-obvious placements),
and **items that could not be placed confidently** (failed moves, still-ambiguous files). Close
with the retained ledger and the exact paths of any failed or restored items.

### Phase 4 -- Output Inventory

For sort and fresh-start modes, save `PARA-Inventory.md` to the root, listing every Project
(with goal + deadline -- these live here, not in folder names), Area, Resource, and archive entry.
Audit mode writes no inventory.

## System Diagnosis (Broken Systems)

Ask what's going wrong, then map to known failure patterns:

| Symptom | Diagnosis | Cure |
|---------|-----------|------|
| Save everything, use nothing | Over-capturing | Tighten capture filter (4 criteria). Install the Express habit. |
| Folders are a mess | Folder explosion / topic-based | Flatten to 4 folders. Archive and restart. |
| System went stale | Skipped weekly reviews | Schedule recurring review. Do one now. |
| More organizing than creating | Over-engineering | Simplify. Remove tags, nested folders, templates. |
| Notes pile up unprocessed | Inbox permanence | Batch-process 2-3x/week. 15 minutes max. |
| Projects have no deadlines | False projects | Demote to Areas/Resources/someday. |

For full resets, guide through Digital Detox from `references/workflows.md`.

## Classification Flow

When the user shares content and asks where it goes:

1. **Read the content, don't just guess from the name.** Your biggest advantage over a human
   sorting by hand: you can open the file. A folder called "Q4" is ambiguous by name -- open
   it, find a half-finished deck with a deadline, and it's clearly a Project. Peek inside
   ambiguously-named folders and read headers/first lines before classifying.
2. **Ask about context** only if still unclear.
3. **Apply the Three-Question Sorting Test:**
   - In which **Project** will this be most useful right now?
   - If none: In which **Area** of responsibility?
   - If none: Which **Resource** topic?
   - If none: **Archive** or skip saving entirely.
4. **Explain reasoning** so the user learns the pattern.
5. **Remind: items move.** No permanent right place.

## PARA Quick Reference

| Category | Definition | Key Rule | Examples |
|----------|-----------|----------|---------|
| **Projects** | Short-term, goal + deadline | Must have both outcome and timeframe | "Publish blog post", "Plan vacation" |
| **Areas** | Ongoing responsibilities | Never end; maintain a standard | Health, Finances, Direct Reports |
| **Resources** | Topics of interest | Currently inactive; future reference | Coffee brewing, design inspiration |
| **Archives** | Inactive items from other three | Cold storage; searchable | Completed projects, ended roles |

### Project count guidance
Use the scanner's configured lower and upper bounds as review prompts. Counts do not prove system health, and they do not decide where an item belongs.

## Workflow Quick Reference

| Workflow | When | Reference |
|----------|------|-----------|
| Project Kickoff | Starting new project | `references/workflows.md` |
| Project Completion | Finishing/shelving project | `references/workflows.md` |
| Weekly Review | Every 3-7 days | `references/workflows.md` |
| Monthly Review | Once a month | `references/workflows.md` |
| Project List Audit | Overwhelmed or unfocused | `references/workflows.md` |
| Digital Detox | System feels broken | `references/workflows.md` |
