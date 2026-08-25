---
name: weekly-review
description: >
  Use only when the user asks to run a weekly PARA review or wants a briefing on stale
  projects, inbox load, recent second-brain activity, deadlines, and next review actions.
  Scans an existing authorized PARA structure read-only; it does not reorganize files.
---

Run a read-only PARA weekly review. Autonomously scan the user's authorized PARA folder
structure and produce a structured review briefing that identifies what needs attention.

## Discovery Phase

First, locate the user's PARA structure. Search for these patterns:

1. **Standard PARA folders:** Look for directories named `Projects`, `Areas`, `Resources`,
   `Archive` or `Archives`, or numbered plain-folder variants (`1-Projects`, `2 Areas`, etc.).
   `Inbox` and `Templates` may be present as optional support folders.
2. **Likely locations:** Prefer a path the user specifies. Otherwise check likely roots read-only without broadly recursing through the home directory.
3. **Obsidian vaults:** Look for `.obsidian/` directories alongside PARA folders
4. **Notion exports:** Look for exported Notion workspace structures

If the PARA structure cannot be found, report this clearly and ask the user to specify the path.

**Search commands:** Adapt to the detected OS. On Windows, use PowerShell's `Get-ChildItem`; on Linux use GNU `find`; on macOS use `find` with `stat` or `gstat` for timestamps.
```bash
# Find PARA-like top-level folders
find ~/ -maxdepth 3 -type d -iname "*project*" -o -iname "*area*" -o -iname "*resource*" -o -iname "*archive*" 2>/dev/null | head -20
```

## Analysis Phase

Once the PARA root is located, perform these scans:

### 1. Stale Project Detection

Scan each project folder for modification timestamps:

```bash
# For each project subfolder, find most recent file modification
# GNU/Linux:
find "$PARA_ROOT/Projects" -maxdepth 1 -mindepth 1 -type d -exec sh -c '
  for dir; do
    latest=$(find "$dir" -type f -printf "%T@ %p\n" 2>/dev/null | sort -rn | head -1)
    echo "$latest $dir"
  done
' _ {} +
# macOS alternative: use stat -f "%m %N" or gstat --format="%Y %n"
# Windows (Git Bash): use ls -lt --time-style=+%s or Glob + Read tools
```

Adapt commands to the user's OS. Use Glob and Bash tools to check file modification
times in a cross-platform way when shell commands vary.

**Staleness thresholds:**
- **Active:** Modified within 7 days
- **Cooling:** Modified 7-14 days ago (mention in briefing)
- **Stale:** No modifications in 14+ days (flag prominently)
- **Dormant:** No modifications in 30+ days (recommend archiving or writing Hemingway Bridge)

### 2. Inbox Overflow Check

Look for unsorted capture locations:
- `Inbox/` or `0-Inbox/` folders
- Root-level files not in any PARA category
- `Quick Capture` or `Scratch` notes
- Recently created files outside PARA structure

**Overflow thresholds:**
- **Healthy:** 0-10 items in inbox
- **Accumulating:** 11-25 items (recommend batch-processing)
- **Overflowing:** 25+ items (flag as urgent — inbox is becoming a graveyard)

### 3. Project Count Check

Count active projects (subfolders in Projects/):
- Compare the count with the bounds configured for the local scanner.
- Report a count outside those bounds as advice for review.
- Avoid calling the count a health score or a failure.

### 4. Recent Activity Summary

Identify what was actively worked on in the past 7 days:
- Most recently modified project folders
- New files created this week
- Any project completions (folders moved to Archives recently)

### 5. Calendar/Deadline Awareness

If project folders contain notes with dates or deadlines, scan for:
- Upcoming deadlines in the next 7-14 days
- Overdue items (past deadlines still in active projects)

## Briefing Generation

Produce a structured review briefing in this format:

```markdown
# Weekly PARA Review Briefing
**Date:** [today]
**PARA Root:** [path]

## System Health
- **Active Projects:** [count] (compare with the configured scanner bounds)
- **Inbox Items:** [count] ([healthy/accumulating/overflowing])
- **Stale Projects:** [count] (no activity in 14+ days)

## Needs Attention

### Stale Projects (14+ days inactive)
- **[Project Name]** — Last modified [date] ([N] days ago)
  → Recommend: Archive, revive, or write a Hemingway Bridge?
- ...

### Inbox Overflow ([N] unsorted items)
[List the oldest 10 items needing classification]

### Approaching Deadlines
- **[Project]:** [deadline] ([N] days away)
- ...

## Active This Week
- **[Project 1]** — [recent activity summary]
- **[Project 2]** — [recent activity summary]

## Review Questions
1. Are stale projects still relevant? Should any be archived?
2. Do any Areas need new projects? (Is any standard slipping?)
3. Did anything captured this week relate to your 12 Favorite Problems?
4. What are your top 3 priority projects for next week?
5. Is there anything in Someday/Maybe ready to activate?

## Quick Actions
- [ ] Process inbox items (estimated: [N] minutes)
- [ ] Archive or revive [N] stale projects
- [ ] Classify approved-root captures into PARA folders
- [ ] Choose tasks for next week
```

## Output Guidelines

- Be factual and specific — report what was found, not generic advice
- Include file counts and dates, not vague assessments
- Make every finding actionable — always suggest a specific next step
- Keep the briefing scannable — use headers, bullets, and tables
- If the PARA system is healthy, say so briefly — don't manufacture problems
- Tailor the "Review Questions" based on actual findings (don't include questions
  about stale projects if there are none)

## Edge Cases

- **No PARA structure found:** Report clearly, suggest running the para-organize skill
  to set one up
- **Empty projects folder:** Not necessarily a problem — the user may use a different
  tool. Ask before flagging.
- **Very large folder trees:** Limit scanning depth to 3 levels to avoid timeouts.
  Report if deeper scanning is needed.
- **Permission errors:** Report which directories couldn't be scanned and suggest
  the user check permissions.
