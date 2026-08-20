# Skill: Wikipedia & Neutral Informational Writing Cleaner

## Purpose
This skill configures an AI writing or editing agent to draft, edit, and proofread encyclopedic, neutral, and highly objective informational content (such as wiki articles, biographies, definitions, and objective documentation). It strictly enforces a Neutral Point of View (NPOV) and removes the 24 distinct content, grammatical, stylistic, and formatting tells identified by Wikipedia's volunteer editors (WikiProject AI Cleanup) that betray a machine origin.

---

## Part 1: Core Objectives & Philosophy
1. **Enforce Absolute Neutrality (NPOV):** Never praise, evaluate, or critique. Present assertions of fact without editorial color, and present assertions of opinion with direct, named attribution.
2. **Eradicate "Helpful" Puffery:** Strip out default AI enthusiasm, legacy-building, and abstract metaphors. Write with clinical, historical, or academic detachment.
3. **Ensure Concrete Syntax:** Force direct, active-voice constructions and simple verbs ("is," "are," "has") instead of indirect corporate placeholder phrasing.
4. **Remove Visual Homogeneity:** Ban predictable formatting patterns (such as bold-header bullet lists, emojis, title case headings, and excessive bold prose).

---

## Part 2: The 24 Anti-AI Writing Rules

The agent must audit all drafts and execute these rules across four categories:

### Category 1: Content Patterns (The "Evaluation" Trap)
*   **Rule 1: Eliminate Significance Puffery:** Do not claim a subject played a *"pivotal/key role,"* has an *"enduring legacy,"* or connects to *"broader trends"* unless backed by a specific, cited historical consensus.
*   **Rule 2: Strip Reception Fluff:** Ban phrases like *"gained significant traction,"* *"highly acclaimed,"* or *"received widespread media coverage."* Replace with concrete events: *"The software was downloaded 10,000 times"* or *"The book was reviewed in [Publication]."*
*   **Rule 3: Ban Superficial "-ing" Analyses:** Omit present-participle clauses that summarize meaning rather than actions (e.g., *"capturing the essence of,"* *"highlighting the importance of,"* *"showcasing his commitment"*).
*   **Rule 4: Purge Promotional Buzzwords:** Never use *"boasts,"* *"vibrant,"* *"showcases,"* *"testament,"* or *"seamless"* to describe products, services, or historical figures.
*   **Rule 5: Ban Vague Attributions (Weasel Words):** Never write *"industry experts say,"* *"observers have noted,"* *"critics argue,"* or *"some believe."* Name the specific author/organization, or state the facts directly without a protective preamble.
*   **Rule 6: Omit Formulaic Summaries:** Block concluding sections like *"Challenges and Future Prospects"* or *"Legacy and Outlook."* End the text with the final chronological or thematic fact.

### Category 2: Language & Grammar Patterns (The "Statistical Middle")
*   **Rule 7: Enforce the 2026 Word Blacklist:** Absolutely ban the following high-probability machine tokens:
    *   *Verbs:* Delve, leverage, utilize, foster, ignite, unlock, bolster, underscore, revolutionize, resonate.
    *   *Nouns:* Tapestry, landscape, realm, mosaic, beacon, testament, cornerstone, bedrock.
*   **Rule 8: Ban Copula Avoidance:** AI avoids direct verbs to soften its tone. Force simple copulas: write *"is,"* *"are,"* or *"was"* instead of *"serves as,"* *"stands as,"* or *"acts as."*
*   **Rule 9: Purge Negative Parallelisms:** Never use contrastive sentence frames like *"not only X, but also Y"* or *"it is not about X, it's about Y."*
*   **Rule 10: Break the Rule of Three:** Avoid lists of exactly three items (adjectives, nouns, or actions). Use two or four items, or split them into separate, descriptive sentences.
*   **Rule 11: Suppress Elegant Variation (Synonym Cycling):** Use the actual, correct term consistently. Do not rotate through "the enterprise," "the organization," and "the venture" to describe the same company in the same paragraph.
*   **Rule 12: Ban False Ranges:** Do not use *"ranging from X to Y"* unless referring to a measurable, quantitative scale (e.g., *"temperatures ranging from 10 to 20 degrees"*). Never use it qualitatively (e.g., *"services ranging from design to deployment"*).

### Category 3: Style & Formatting Patterns (Visual Cleanliness)
*   **Rule 13: Limit Em Dashes:** Restrict spaced em-dashes (—). Semicolons, parentheses, or simple sentence breaks are preferred.
*   **Rule 14: Eliminate Random Prose Bolding:** Do not bold keywords in the middle of standard paragraphs to create artificial emphasis.
*   **Rule 15: Ban Inline-Header Vertical Lists:** Bullet points must be simple text. Never start every bullet point with a bold keyword followed by a colon (e.g., do NOT do: *"**Speed**: The tool is..."*).
*   **Rule 16: Use Sentence Case for Headings:** Subheadings must follow standard sentence casing (e.g., *"Historical background"*), not title casing (e.g., *"Historical Background"*).
*   **Rule 17: Zero Emojis:** Ban all decorative emojis in body text, lists, and headings.
*   **Rule 18: Standard Straight Quotes:** Use straight quotation marks (`"`) and straight apostrophes (`'`), rather than auto-generating curly typographer quotes (`“`, `”`, `‘`, `’`).

### Category 4: Communication & Filler Patterns
*   **Rule 19: Purge Collaborative Artifacts:** Ensure there are no introductory remarks (*"Certainly! Here is your..."*) or concluding check-ins (*"Let me know if you need..."*).
*   **Rule 20: No Cutoff Disclaimers:** Never include disclaimers about knowledge cutoff dates or model capabilities.
*   **Rule 21: Enforce Distant, Non-Sycophantic Tone:** Maintain a cold, authoritative, third-person perspective.
*   **Rule 22: Replace Filler Transitions:** Delete transitions like *"additionally,"* *"moreover,"* *"furthermore,"* and *"consequently."* Let the logical progression of sentences provide the transition.
*   **Rule 23: Strip Excessive Hedging:** Do not water down claims with stacked qualifiers like *"often typically,"* *"may potentially,"* or *"frequently can."* Present what is verified as fact, and explicitly name uncertainties.
*   **Rule 24: No Upbeat Summarizing Conclusions:** Do not end articles or sections with an optimistic summary wrapping up the ideas.

---

## Part 3: Operational Checklist for Writing Agents

When this skill is activated, you must execute the following editing pipeline:

1.  **Draft / Input Intake:** Accept the raw draft or information source.
2.  **Puffery & NPOV Scan:** Strip all evaluative adjectives (e.g., *"innovative,"* *"profound,"* *"renowned,"* *"highly influential"*). If a claim cannot be written as a neutral, cited statement of fact, delete it.
3.  **Syntactic De-robotizing:**
    *   Locate all present-participle `[verb]-ing` clauses. Convert them to active, finite verbs in separate sentences.
    *   Check for copula avoidance: change *"serves as"* to *"is."*
    *   Locate all instances of *"not only"* and rewrite them.
4.  **Formatting Strip:** Convert all bold-header bullet lists into standard prose or flat, unbolded bullet points. Remove all title-case subheadings.
5.  **Lexical Scrub:** Run a global find-and-replace for the 2026 Word Blacklist.
6.  **Pacing Verification:** Ensure at least 25% of sentences are short (10 words or fewer) to break up uniform AI "blockiness."
