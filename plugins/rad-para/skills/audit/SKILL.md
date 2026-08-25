---
name: audit
description: >
  Use only when the user asks to audit, validate, diagnose, or health-check an existing
  PARA folder structure or second brain. Performs read-only structural analysis and reports
  anti-patterns, false projects, nesting, staleness, and orphaned files; it does not reorganize files.
---

Run a read-only PARA audit. Autonomously scan the user's authorized PARA folder
structure and produce a detailed structural health report identifying anti-patterns,
violations, and improvement opportunities.

## Discovery Phase

Locate the user's PARA structure. Search for these directory patterns:

- `Projects/`, `Areas/`, `Resources/`, `Archive/` or `Archives/`
- Numbered plain-folder variants such as `1-Projects/`, `2 Areas/`, `3_Resources/`, and `4-Archives/`
- Optional `Inbox/` and `Templates/` folders at the same root
- Prefer a user-specified path. If none is supplied, check likely roots read-only and avoid broad recursive scans.
- Obsidian vaults: `.obsidian/` alongside PARA directories

If not found, report this and ask the user for the correct path.

## Audit Checks

Run all applicable checks and compile results.

### Check 1: Top-Level Structure Validation

**Expected:** One top-level folder for each PARA category: Projects, Areas, Resources, and Archive/Archives. Plain and numbered names are equivalent. Inbox and Templates are optional support folders.

**Flag as violations:**
- Missing categories (e.g., no Archives folder)
- Extra top-level folders that aren't PARA categories or documented optional folders
- Misspelled names (e.g., "Project" instead of "Projects")
- More than one level of PARA (nested PARA inside PARA)

**Scoring:**
- 4 categories, with no extras → PASS
- 4 categories plus optional folders → PASS
- 4 categories plus other extras → WARN (list the extras)
- Missing folders → FAIL (list what's missing)

### Check 2: Topic-Based Subfolder Detection (Anti-Pattern)

**The problem:** Users often create subject-based folders inside PARA categories
(e.g., `Resources/Psychology/`, `Resources/Business/`, `Resources/Technology/`).
This is the #1 PARA anti-pattern — it recreates the same problem PARA was designed to solve.

**Detection heuristics:**

Scan subfolder names in each PARA category for topic-like patterns:
- Academic subjects: Psychology, Philosophy, Science, History, Math
- Industry terms: Marketing, Engineering, Finance, Legal, Design
- Broad topics: Technology, Health, Productivity, Creativity, Leadership
- Generic collectors: Miscellaneous, General, Other, Stuff, Random, Unsorted

**What IS acceptable:**
- In Projects: subfolders named after specific projects with outcomes ("Launch Website Q2", "Move to New Apartment")
- In Areas: subfolders named after responsibilities ("Direct Reports", "Finances", "Health")
- In Resources: subfolders named after specific interests with bounded scope ("Coffee Brewing", "Obsidian Plugins")
- In Archives: anything — archives are cold storage

**Scoring:**
- No topic-based folders detected → PASS
- 1-3 questionable folders → WARN (list with explanation)
- 4+ topic-based folders → FAIL (recommend restructuring)

### Check 3: Active Project Evaluation

**Count subfolders in Projects/.**

For each project, evaluate:

1. **Has a clear outcome?** Scan for files containing goal-like language, task lists,
   or outcome definitions. Flag vague project names ("Get Healthy", "Learn Things").

2. **Has recent activity?** Check file modification dates.
   - Active: modified within 14 days
   - Stale: no modifications in 14-30 days
   - Dormant: no modifications in 30+ days

3. **Has a deadline?** Scan filenames and content for date references.

**False project detection heuristics:**
- Project name is an Area disguised as a Project ("Health", "Career", "Finances")
- No files with dates, deadlines, or milestones
- No modifications in 30+ days AND no clear outcome in folder name
- Contains only bookmarks or reference material (should be in Resources)

**Project count guidance:**
- Use the scanner's configured lower and upper bounds as advice.
- Report counts below or above those bounds as a review prompt.
- Do not call a project count a failure or a measured health standard.

### Check 4: Nesting Depth Analysis

**The problem:** Over-nesting creates the "basement effect" — too many levels makes
the system feel cramped and discourages use.

**Scan all directories and report maximum depth per PARA category.**

**Thresholds:**
- 1-2 levels deep → PASS (clean, flat structure)
- 3 levels deep → WARN (acceptable but watch for growth)
- 4+ levels deep → FAIL (over-nested — recommend flattening)

List the deepest paths found.

### Check 5: Orphaned Files Detection

**Scan for files at the supplied root outside the PARA categories:**
- Files at the PARA root level (not inside any category)
- Optional Inbox or Templates items that have not been classified
- Stray notes or documents at the approved root

**Scoring:**
- 0-5 orphaned files → PASS
- 6-15 orphaned files → WARN
- 16+ orphaned files → FAIL

### Check 6: Archives Health

**Check that Archives is being used:**
- Empty Archives → WARN ("No completed projects archived — are projects being closed?")
- Archives with recent additions → PASS (system is being maintained)
- Projects in Archives that still have recent modifications → WARN ("Active work in Archives — should this be moved back to Projects?")

### Check 7: Cross-Platform Consistency

If PARA folders exist in multiple locations (notes app export, file system, cloud drive),
check that the same 4 categories exist in each location.

## Audit Report

Produce a structured report:

```markdown
# PARA System Audit Report
**Date:** [today]
**PARA Root:** [path]
**Overall Score:** [HEALTHY / NEEDS ATTENTION / NEEDS RESTRUCTURING]

## Structure Summary
| Category | Subfolders | Deepest Nesting | Last Modified |
|----------|-----------|----------------|---------------|
| Projects | [N] | [N] levels | [date] |
| Areas | [N] | [N] levels | [date] |
| Resources | [N] | [N] levels | [date] |
| Archives | [N] | [N] levels | [date] |

## Check Results

### 1. Top-Level Structure: [PASS/WARN/FAIL]
[Details]

### 2. Topic-Based Folders: [PASS/WARN/FAIL]
[Details — list detected topic folders with recommendations]

### 3. Active Projects: [PASS/WARN/FAIL]
- **Total projects:** [N]
- **Active (14 days):** [N]
- **Stale (14-30 days):** [N]
- **Dormant (30+ days):** [N]
- **Suspected false projects:** [list]

### 4. Nesting Depth: [PASS/WARN/FAIL]
[Details — list deepest paths]

### 5. Orphaned Files: [PASS/WARN/FAIL]
[Details — list orphaned files with suggested PARA placement]

### 6. Archives Health: [PASS/WARN/FAIL]
[Details]

### 7. Cross-Platform Consistency: [PASS/WARN/FAIL/SKIP]
[Details or "Single location detected — skipped"]

## Priority Actions
1. [Most critical issue] — [specific fix]
2. [Second issue] — [specific fix]
3. [Third issue] — [specific fix]

## Recommendations
- [Actionable suggestion based on findings]
- [Reference to relevant skill if restructuring is needed]
```

## Output Guidelines

- Be factual — report what was found, with file counts and paths
- Distinguish between WARN (imperfect but functional) and FAIL (actively harmful)
- Every finding must include a specific, actionable recommendation
- If the system is healthy, say so and keep the report brief
- For FAIL items, reference which plugin skill can help fix the issue
  (e.g., "Run the para-organize skill to restructure" or "Use the twelve-favorite-problems skill to create a capture filter")
- Respect privacy — report folder names and structure, not file contents

## Edge Cases

- **No PARA structure found:** Report clearly and recommend running `para-organize` setup
- **Extremely large trees (1000+ files):** Limit depth, sample rather than exhaustively scan
- **Symlinks or cloud sync placeholders:** Skip and note they were skipped
- **Permission denied or incomplete read:** Report the exact path and stop treating the scan as complete
- **Non-standard PARA variants:** Accept reasonable variations (numbered prefixes, slight naming differences) but flag significant deviations
