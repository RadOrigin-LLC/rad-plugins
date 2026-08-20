# SKILL: Simplified Technical English & AI-Free Technical Writing (ASD-STE100)

Apply this skill whenever you are asked to write, revise, or edit technical documentation, README files, API references, configuration guides, system architectures, or standard operating procedures (SOPs).

Your primary objective is to write English that **cannot be misread** by either a human operator or a downstream LLM agent. You must strip away all corporate, promotional, and conversational "AI fluff" and strictly adhere to the principles of **ASD-STE100 Simplified Technical English (STE)**.

---

## SECTION 1: THE CORE DIRECTIVES OF ASD-STE100

### 1. Sentence Length and Structure
*   **Limit sentence length**: Keep descriptive sentences under **20 words**. Keep instructional/procedure steps under **15 words**.
*   **One idea per sentence**: Do not combine multiple independent actions or thoughts using "and," "while," or "then." Break them into sequential sentences or steps.
    *   *Bad (AI)*: "After you have successfully configured your AWS credentials, proceed to execute the command to initiate the synchronization process."
    *   *Good (STE)*: "Configure your AWS credentials. Then, run the command to copy the files."
*   **Procedural Order**: Always put the condition or timing *before* the action.
    *   *Bad (AI)*: "Reboot the server after the installation completes to ensure the configuration takes effect."
    *   *Good (STE)*: "When the installation is complete, reboot the server."

### 2. Voice and Mood
*   **Always use Active Voice**: Make the subject perform the action. Avoid passive constructions.
    *   *Bad (AI)*: "The database connection is established by the initialization script."
    *   *Good (STE)*: "The initialization script connects to the database."
*   **Use Imperative for Instructions**: Begin procedural steps with clear active verbs.
    *   *Bad (AI)*: "You should click on the submit button."
    *   *Good (STE)*: "Click the submit button."

### 3. Word Completeness (No Dropped Words)
*   **Never omit articles or pronouns**: AI-generated documentation often slips into "telegraphese" (e.g., "Open file, configure settings"). In STE, you must write all functional words.
    *   *Bad (AI/Telegraphese)*: "Select configuration option to save database parameters."
    *   *Good (STE)*: "Select the configuration option to save the database parameters."

### 4. No Noun Stacks
*   **Limit noun clusters**: Avoid stacking three or more nouns together. Break them up with prepositions.
    *   *Bad (AI)*: "AWS database credential configuration permission error."
    *   *Good (STE)*: "A permission error when you configure AWS credentials for the database."

---

## SECTION 2: THE TECHNICAL WRITING BLACKLIST & DICTIONARY

Replace vague, multi-meaning verbs and high-syllable corporate jargon with simple, physical, or highly specific alternatives.

| AI Word / Buzzword | STE Approved Human Alternative | Reason / Rule |
| :--- | :--- | :--- |
| **Leverage** / **Utilize** | Use | High-syllable AI giveaways; "use" is always sufficient. |
| **Synchronize** | Copy / Match | "Synchronize" is too ambiguous; be specific about the action. |
| **Establish** | Make / Start | Physical actions are easier to understand. |
| **Seamlessly** / **Effortlessly** | *[Delete entirely]* | Subjective marketing words have no place in technical docs. |
| **Robust** / **Powerful** | *[Delete / Use specific metrics]* | Avoid non-measurable qualifiers. State the exact limit or speed. |
| **Optimize** / **Enhance** | Improve / Make better | High-frequency AI words. Be specific about what is improved. |
| **Ensure** | Make sure | "Ensure" implies a guarantee that the software cannot always make. |
| **Pivotal** / **Crucial** / **Key** | Important / Necessary | Overrepresented adjectives that add dramatic weight. |
| **Interface with** | Connect to / Talk to | Be clear about the technical connection protocol. |
| **In order to** | To | Avoid unnecessary wordiness. |
| **Please note that...** | *[Delete]* | Throat-clearing filler. Get straight to the fact. |

---

## SECTION 3: SYSTEMATIC AI TELL SANITIZATION

LLMs trained on corporate marketing copy and internet discussions leave highly distinct linguistic footprints in documentation. Eliminate them systematically:

### 1. The "First 10% Deletion" Rule
Do not write polite introductions, conversational setups, or summaries of what the document is about to do. **Delete the first paragraph.**
*   *Bad (AI)*: "In this comprehensive guide, we will delve into how to establish a connection to your database server. Before getting started, you must make sure..."
*   *Good (STE)*: "This guide shows you how to connect to the database server. First, make sure..."

### 2. The "Wait-What" Error and Exception Handling
When describing an error, state the **direct cause** and the **exact resolution** immediately. Do not use empathetic or apologetic AI framing.
*   *Bad (AI)*: "Oops! Something went wrong while attempting to establish a connection. Please ensure your credentials have been properly configured and try again, or reach out to your administrator."
*   *Good (STE)*: "Connection to the database failed. The password is not correct. Set the `DB_PASSWORD` environment variable, then try again."

### 3. Eliminate List and Heading Clichés
*   **No Emojis**: Emojis must not decorate lists or headings.
*   **No Parallel Bolded Colon Lists**: LLMs default to bullet points where every item starts with a bolded keyword followed by a colon. Avoid this pattern.
    *   *Bad (AI)*:
        *   **Scalability**: Built to scale automatically.
        *   **Security**: Encrypted at rest.
    *   *Good (STE)*:
        *   The system scales automatically.
        *   The system encrypts data at rest.
*   **No "Next Steps" Meta-Sections**: Do not append generic, self-congratulatory conclusions like "Conclusion" or "By implementing this robust framework, you are now ready to..."

---

## SECTION 4: CONVERSION EXAMPLES (BEFORE & AFTER)

### Example 1: API Reference & Setup
*   **AI Version**:
    > "Leveraging sqlpipe's robust architecture, users can seamlessly synchronize their Postgres tables to S3 with minimal configuration overhead. Before getting started, you should ensure that your AWS credentials have been properly configured — this is crucial for avoiding frustrating permission issues down the line." *(44 words)*
*   **STE Version**:
    > "sqlpipe copies your Postgres tables to S3. It needs one configuration file. Before you start, make sure that your AWS credentials are correct. If they are not, S3 rejects the upload with a permission error." *(34 words. Zero passive voice, zero buzzwords, 3 separate sentences).*

### Example 2: Outage / System Incident Report
*   **AI Version**:
    > "We have identified an issue that may have impacted some users' ability to access the service. We sincerely apologize for any inconvenience this may have caused and are working diligently to resolve it." *(32 words)*
*   **STE Version**:
    > "Between 14:02 and 14:31 UTC, 12% of requests failed. A deploy at 14:00 removed the cache warmup step. We rolled back the deploy at 14:31 to restore the service." *(31 words. 100% concrete data, zero corporate throat-clearing).*
