---
name: writing
description: Draft, rewrite, copyedit, proofread, or review academic, creative, technical, business, email, social, marketing, and reference prose.
---

# Writing

Improve prose for its reader, purpose, channel, and voice. Preserve the user's facts, meaning, and deliberate style. This skill does not detect authorship, hide AI use, or replace fact-checking and human review.

## PARA handoff

PARA Express owns gathering and outlining source notes, while Writer owns the accepted draft, rewrite, copyedit, proofread, or review operation.

Offer `rad-para:express-workflow` only when that exact skill appears in the current available-skill list. Ask whether the user accepts the handoff and wait for acceptance before invoking it. Do not treat a package name, README, or memory as proof that the skill is loaded. After acceptance, hand off gathering or outlining and resume this skill with the accepted material and selected operation. If the exact skill is absent or the user declines, continue the current writing operation standalone.

## Choose the operation

- **Draft:** Create new text from the supplied brief, facts, and sources.
- **Rewrite:** Change wording and structure while preserving meaning, facts, uncertainty, citations, and required format.
- **Copyedit:** Improve clarity, flow, consistency, and usage without changing the argument or adding information.
- **Proofread:** Correct spelling, grammar, punctuation, and obvious formatting errors only.
- **Review:** Report material issues and suggested actions. Do not rewrite unless the user asks.

## Apply

1. Follow the user's explicit instructions first, then supplied sources and citations, then a named house or publication style, then this skill's defaults.
2. Identify the operation, document type, audience, purpose, channel, voice, locale, format, and hard limits. Ask only when missing information could materially change the result.
3. Read [writing-standards.md](references/writing-standards.md). Use the primary writing mode and the shared checks. Apply another mode only when the document needs it.
4. Preserve facts, numbers, citations, uncertainty, terminology, plot facts, code, and requested format. Never invent evidence, sources, personal experience, customer details, metrics, or story events.
5. Stay within the selected operation. Editing does not verify a claim. When verification is requested and reliable sources are available, check the claim and cite those sources. Otherwise, mark missing support.
6. For drafting, rewriting, copyediting, or proofreading, return the requested text first. For a review, return findings with precise examples. Add a short note only when a missing fact, source, policy, or choice affects safe use of the result.

## Shared review

- Cut throat-clearing, empty praise, vague attributions, inflated claims, stock metaphors, and generic assistant remarks.
- Prefer exact nouns and active verbs. Use simple forms such as `is`, `has`, and `shows` when they are correct.
- Vary sentence length and paragraph shape naturally. Do not force short-sentence quotas, fragments, flashbacks, or word substitutions that harm meaning.
- Keep formatting useful and accessible. Follow requested heading style, list structure, link format, and text alternatives. Use decorative emojis only when requested.
- Remove accidental platform markers such as `contentReference`, `oai_citation`, `[cite: ...]`, or `turn0search...`. Keep legitimate citations, links, code, and quoted text.
