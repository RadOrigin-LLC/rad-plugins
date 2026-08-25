---
name: hemingway-bridge
description: >
  This skill should be used when the user says "hemingway bridge", "wrap up session",
  "save my progress", "where did I leave off", "session handoff", "end of session",
  "capture what I was working on", "pick up where I left off", "PARA handoff",
  "what should I do next session", or wants to capture session state in a PARA-aware
  format before stopping work. It can use RAD Repo only after checking that the exact
  needed `rad-repo:<skill>` appears in the current available-skill list, the current
  task needs it, and the user accepts.
---

# Hemingway Bridge — PARA-Aware Session Handoffs

Capture session state using the Hemingway Bridge technique: stop work while momentum
is still high, document current status, next steps, and open questions so the next
session starts with zero ramp-up time.

Named after Hemingway's practice of stopping mid-sentence so he always knew where to
pick up the next day.

## When to Use

- End of any work session (before the user is exhausted)
- Pausing or shelving a project
- Before going on vacation or leave
- Handing off work to someone else
- When the user says "I'm done for today"
- Proactively at end of long sessions involving PARA work

## Hemingway Bridge Capture Process

### Step 1: Identify Active Context

Ask one question:
> "What were you working on today? Give me a quick brain dump -- projects touched,
> decisions made, anything unfinished."

If the session context is already clear from conversation history, skip the question
and proceed directly.

### Step 2: Build the Bridge

Capture these four elements:

1. **Current Status** -- What was just completed or accomplished
2. **Next Steps** -- What was planned next (be specific: "write the intro section"
   not "keep working on it")
3. **Open Questions** -- Unresolved decisions, blockers, or unknowns
4. **First Action** -- The single, concrete thing to do when returning
   (this eliminates decision fatigue at session start)

### Step 3: Map to PARA Context

Add PARA-specific context to the bridge:

- **Active Project:** Which project folder this work belongs to
- **Materials Created:** New IPs, notes, or drafts produced this session
- **Materials Needed:** What to gather or read before the next session
- **Capture Inbox:** Anything captured during the session that still needs
  to be sorted into PARA folders

### Step 4: Write the Bridge Note

Generate a bridge note in this format:

```markdown
## Hemingway Bridge — [Project Name]
**Date:** [today's date]
**Session Duration:** [approximate time spent]

### Status
[What was accomplished this session — outcomes only, not narrative]

### Next Steps
1. [Specific next action — the thing to do FIRST when returning]
2. [Second priority]
3. [Third priority]

### Open Questions
- [Decision or unknown that needs resolving]
- [Blocker or dependency]

### PARA Context
- **Project:** [Project folder name]
- **New IPs created:** [List any Intermediate Packets produced]
- **Unsorted captures:** [Items still in inbox needing classification]
- **Related materials:** [Notes/files to review next session]

### Momentum Notes
[Anything to preserve the creative state — a half-formed idea, an intuition
about direction, a connection noticed but not yet explored]
```

### Step 5: File the Bridge

Recommend where to save the bridge note:
- **Inside the project folder** if the work is project-specific
- **In the daily log** if multiple projects were touched
- **In `docs/handoff.md`** only when the exact needed RAD Repo skill is available,
  the task needs its Git handoff, and the user accepts (see below)

## Optional RAD Repo Integration

RAD Repo is optional. Before offering it, check the current available-skill list for
the exact needed skill, such as `rad-repo:wrapup` or `rad-repo:startup`. Offer that
skill only when the current task needs Git-based handoff behavior. Invoke it only
after the user accepts. If the exact skill is absent or the user declines, keep this
bridge standalone and use the note format above.

### docs/handoff.md Integration

When the exact `rad-repo:wrapup` skill is available, the task needs its Git-based
handoff, and the user accepts, pass these bridge elements to that skill for the
`docs/handoff.md` it writes:

- **Status** → the handoff's session summary
- **Next Steps / First Action** → the handoff's next-action snapshot
- **Open Questions** → open work
- **PARA Context** (new IPs, unsorted captures) → noted alongside changed files
- **Momentum Notes** → insights worth preserving

Read the bridge note or `docs/handoff.md` explicitly. Do not assume that another
skill has read the handoff.

### Session Startup Integration

When starting a new session after a Hemingway Bridge was written:

1. Read the bridge note or `docs/handoff.md` explicitly
2. Present the "First Action" to the user immediately
3. Surface any unsorted inbox items for quick PARA classification
4. Resume work with full context -- zero ramp-up time

If the exact `rad-repo:startup` skill appears in the current available-skill list,
the current task needs its Git startup behavior, and the user accepts, offer and
invoke it. If the skill is absent or the user declines, continue with these
standalone startup steps.

## Bonus: Send-Off Technique

Before wrapping up, suggest the user send a draft or work-in-progress for feedback:
> "Consider sharing what you have so far with someone for feedback. When you return,
> you'll have fresh input waiting -- a natural on-ramp back into the work."

This combines the Hemingway Bridge (preserving momentum) with the IP feedback loop
(getting external input while you're away).

## Key Principles

- **Stop before exhaustion.** The bridge works best when written with energy remaining.
- **Be specific, not vague.** "Write the introduction paragraph for the API doc" beats
  "keep working on the docs."
- **Preserve creative state.** Half-formed ideas and intuitions are the most fragile
  context -- capture them even if they feel incomplete.
- **One clear first action.** The next session should start with zero decision-making.

## Reference Files

For the full Hemingway Bridge technique and other creative techniques:
- **`../para-organize/references/creative_techniques.md`** -- Complete technique descriptions
