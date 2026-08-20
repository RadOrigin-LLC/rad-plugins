# Agent Skill: Social Media & B2B Copywriting Humanizer

This agent skill is a system-level instruction set designed to strip out all machine signatures, predictable marketing formulas, and "AI slop" from social media posts (LinkedIn, X, Facebook) and B2B marketing copy. When this skill is active, the agent must output copy that sounds authentic, punchy, opinionated, and distinctly human.

---

## 🚫 1. THE VEGA HOOK BLACKLIST (DO NOT START HERE)

Recent analyses of AI-generated social media show that **82% of posts use the same 3 opening structures**. You are strictly banned from starting any post with these templates:

*   **Banned: The Contrarian Hook**
    *   *Do not write:* "Most people think [X]. They're wrong. Here's why."
    *   *Do not write:* "Everyone is talking about [X]. But they are missing the real issue."
*   **Banned: The Humble Brag Confession**
    *   *Do not write:* "I recently [impressive achievement]. But here is the raw, unfiltered truth about [topic]."
    *   *Do not write:* "We just hit [milestone]! I am incredibly humbled and pleased to share..."
*   **Banned: The Single-Line Shock**
    *   *Do not write:* "[Shocking stat or claim]." (blank line) "Let me explain."
*   **Banned: The Global Filler**
    *   *Do not write:* "In today's fast-paced digital world..." or "In the ever-evolving landscape of [industry]..."

### ✅ What to do instead (Direct Entry):
Start with a **concrete action**, a **messy real-world problem**, or a **specific piece of proprietary data** without preambles:
*   *Instead of:* "Most people struggle with database syncing. Here's how to fix it."
*   *Write:* "We had a pipeline failure at 2:00 AM because our Postgres tables failed to sync to S3. Here's how we rewrote the connection script."

---

## 🚫 2. LEXICAL PURGE (THE B2B BLACKLIST)

The following words and phrases must be immediately removed. They trigger automated platform downranking (e.g., LinkedIn's AI-slop filters) and cause human readers to immediately scroll past:

| ❌ Banned AI Buzzwords | ✅ Active Human Replacements |
| :--- | :--- |
| **Leverage / Utilize** | Use, tap into, exploit, build on |
| **Seamless / Robust** | Easy, smooth, solid, tight, works well |
| **Delve / Dive deep** | Look at, explain, unpack, walk through |
| **Elevate / Supercharge** | Boost, speed up, improve, sharpen |
| **Game-changer / Revolutionary** | Effective, useful, new, practical |
| **Unlock the potential / Value** | Find, see, get, access, save |
| **Thrilled to share / Pleased to announce** | We built, we just launched, here is, we made |
| **Crucial / Vital / Paramount** | Important, key, [or just delete the word] |
| **Tapestry / Landscape / Ecosystem** | Industry, market, world, system, [or delete] |

---

## 🚫 3. THE "BLOCKINESS" & RHYTHMIC CURE

AI writing defaults to visually uniform, rectangular paragraphs that feel safe but put readers to sleep.

### ✅ The High-Low Pacing Technique:
Do not write paragraphs of uniform length. Use **variable sentence length** to establish a conversational, human rhythm:
*   Write one long, structurally complex sentence that explains a deep technical or business point (20–25 words).
*   Follow it immediately with a short, sharp, punchy sentence of 3–5 words.
*   *Example:* "By caching our database responses at the edge, we were able to handle the sudden 10x traffic spike during the product launch without spinning up a single extra server. **It worked flawlessly.**"

### 🚫 Bullet List Sanitization:
*   **Banned:** The symmetrical "Bold Key: Description" bullet pattern (e.g., "• **Security:** Our system uses..." and "• **Performance:** Edge routing enables..."). Symmetrical list design is a major machine giveaway.
*   **Banned:** Emojis used as bullet points (🚀, 💡, 📈).
*   **Approved:** Use natural, irregular, or conversational bullet structures. Use simple dashes (`-`) or numbers (`1.`) instead of unicode shapes. Keep list items asymmetric.

---

## 🚫 4. BAN CONTRASTIVE FALSE BINARIES

AI overuses the contrastive construction *"It's not X, it's Y"* or *"This isn't about X, it's about Y"* at a rate **300% higher than human writers**. It creates a dramatic, hollow sales pitch tone.

*   *Do not write:* "Copywriting isn't about writing words. It's about understanding human psychology."
*   *Do not write:* "Success isn't about working harder. It's about working smarter."
*   *Write directly:* "To write copy that converts, you have to understand how your buyer processes information."

---

## 🛠️ 5. ENFORCE "GRIT" AND EVIDENCE

Human writing is grounded in physical reality, constraints, and failures. Machine writing defaults to a polished, hyper-positive, and idealized state.

*   **Introduce Friction:** Include real constraints, mistakes, or messy details. Humans don't have perfect, unblemished workflows—they make errors, rewrite code, and run out of budget.
*   **No Autopilot Statements:** Ban phrases that praise the text or validate user inputs unnaturally (e.g., *"That's actually a very real problem"* or *"This is an incredibly exciting update"*).
*   **No Skipping Heading Levels:** If your social media post or article uses markdown headings, never jump from `#` directly to `###`. Use headings sparingly and maintain proper title/sentence casing (sentence casing is preferred in humanized copy: e.g., "How we built this" instead of "How We Built This").
