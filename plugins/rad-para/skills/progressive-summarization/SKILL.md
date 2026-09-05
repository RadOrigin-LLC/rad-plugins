---
name: progressive-summarization
description: Distill notes using Progressive Summarization layers while preserving source text and attribution.
---

# Progressive Summarization

Apply Tiago Forte's Progressive Summarization technique to transform raw captures into
scannable, layered notes. This skill takes raw input and produces distilled output ready
for a Second Brain.

## The Four Layers

### Layer 1: Original Excerpts
The raw text the user provides -- quotes, highlights, passages from source material.
This layer already exists when the user pastes content.

### Layer 2: Bold the Main Points
Read through the excerpts and **bold** the key sentences, phrases, and keywords that
capture the core ideas. Target roughly 10-20% of the original text.

**What to bold:**
- Sentences that capture a complete, standalone insight
- Surprising claims or counterintuitive findings
- Specific data points, statistics, or examples
- Actionable advice or concrete recommendations
- Definitions of key concepts

**What NOT to bold:**
- Context-setting sentences ("In this article, we explore...")
- Redundant explanations of the same point
- Transitional phrases
- General statements everyone already knows

### Layer 3: Highlight the Best of the Bold
Look ONLY at the bolded text and ==highlight== (or mark with a different format) the
absolute best, most insightful sentences. This creates an ultra-scannable summary.
Target roughly 10-20% of the bolded text.

**Selection criteria:**
- If the user could only read 3 sentences, which would give the most value?
- Which bolded passages would be useful across multiple projects?
- Which statements are most surprising or counterintuitive?

### Layer 4: Executive Summary
Write a brief summary in the user's own voice at the very top using bullet points.
This is the "TL;DR" -- 2-5 bullet points that capture the essence.

**Executive summary rules:**
- Write in first person or neutral instructional voice
- Use the user's vocabulary, not academic jargon
- Each bullet should be a complete, actionable insight
- Include the "so what" -- why this matters

## Process

### Step 1: Receive Input

Accept any of these input types:
- Raw article or blog post text
- Meeting transcript or voice memo transcription
- Book highlights or Kindle exports
- Research paper excerpts
- Brain dump or freeform notes
- Multiple related notes for synthesis

Ask for the input if not provided:
> "Paste the text to distill. This can be an article, transcript, highlights, or any
> raw notes. I'll apply Progressive Summarization layers to make it scannable."

### Step 2: Ask for Context

Use the project or purpose already supplied. Ask only when choosing the important passages depends on missing context; otherwise treat the note as general reference.

### Step 3: Apply Layers

Apply all requested layers in a single output. Default to applying Layers 2-4 unless
the user requests specific layers.

### Step 4: Format Output

Use the requested format or the note's existing format. Default to Markdown when neither is known:

| Format | Output Style |
|--------|-------------|
| **Markdown** (default) | `**bold**` for L2, `==highlight==` for L3, bullet summary for L4 |
| **Notion** | Bold for L2, highlight color for L3, callout block for L4 |
| **Obsidian** | `**bold**` for L2, `==highlight==` for L3, admonition for L4 |
| **Plain text** | `[KEY]` prefix for L2, `[!!!]` prefix for L3, summary block for L4 |

### Output Template

```markdown
## Executive Summary (Layer 4)
- [Insight 1 -- actionable takeaway]
- [Insight 2 -- actionable takeaway]
- [Insight 3 -- actionable takeaway]

---

## Distilled Note

[Original text with **Layer 2 bolding** applied throughout
and ==Layer 3 highlights== on the most critical passages]
```

## Multi-Note Synthesis

When the user provides multiple notes on the same topic:

1. Read all notes and identify common themes
2. Produce a single synthesized note that:
   - Merges overlapping insights (don't repeat the same point from different sources)
   - Preserves unique perspectives from each source
   - Notes areas of agreement and contradiction
   - Attributes key claims to their sources
3. Apply Layers 2-4 to the synthesized result
4. Add a "Sources" section at the bottom

## Key Principles

- **Distill opportunistically.** Don't batch-summarize everything upfront. Add layers
  when the user is actually reviewing a note for a specific purpose.
- **Context matters.** The same article distills differently depending on the active project.
- **Preserve the original.** Never delete source text -- only add formatting layers on top.
- **Favor the user's own words** at Layer 4. Their phrasing is faster to process.
- **AI augments, not replaces.** The act of distilling is itself valuable for learning.
  Explain what was prioritized and why so the user builds their own judgment.

## Reference Files

- **`references/layer-examples.md`** -- Concrete before/after examples of all 4 layers
  applied to articles and meeting transcripts, plus format variations for Obsidian/Notion/plain text
- **`../para-organize/references/code_framework.md`** -- Full CODE framework including distillation principles
