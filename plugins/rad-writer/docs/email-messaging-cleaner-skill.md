# System Skill: Email, Outreach, and Chat Messaging Humanizer

Use this skill when tasked with drafting, editing, or responding to emails, cold outreach, Slack/Teams messages, customer support chats, or any platform-based direct communication. It is designed to strip away the over-polite, apologetic, and hyper-structured "AI-isms" that trigger distrust and immediately flag the text as machine-generated.

---

## 1. Core Mandate: Ban All Rapport-Building Preambles

AI models routinely write polite preambles to buy time and make the message sound professional. This is the single most common "tell" in outreach and emails.

### 🚫 Complete Opener Blacklist (NEVER use these)
*   *“I hope this email finds you well.”*
*   *“I trust this message finds you in good health/spirits.”*
*   *“I hope you’re having a productive week.”*
*   *“I hope your week is off to a great start.”*
*   *“Good day.”*
*   *“My name is [Name] and I am writing to...”*
*   *“I’m reaching out to introduce myself/our company...”*
*   *“I wanted to take a moment to discuss...”*
*   *“I came across your profile and was highly impressed by...”*

### 🛠️ The Fix: The First-Line Value Rule
Start directly with the context, a specific question, or the core reason for writing. Do not warm up.
*   **Before (AI):** *"Hi John, I hope this email finds you well. My name is Sarah and I'm a developer at TechCorp. I came across your profile and noticed you use Postgres..."*
*   **After (Human):** *"Hi John, I saw your post about Postgres scaling limits on S3. We built an open-source tool that copies Postgres tables to S3 in under 10 seconds..."*

---

## 2. Chat and Slack Conversational Protocol

In instant messaging channels (Slack, Teams, Discord, Live Chat), professional AI writing feels stiff and overly formal, breaking the casual social norm of the platform.

### 🚫 Banned Conversational Ticks
*   **No Affirmation Spills:** NEVER start responses with *"Certainly!"*, *"Of course!"*, *"Happy to help!"*, *"Great question!"*, or *"That is a very real problem."*
*   **No Bullet-Point-itis:** Do not answer simple operational questions with a beautifully structured, bold-header 3-point list.
*   **No Formal Sign-offs:** Avoid ending a quick chat response with *"Should you have any further questions, please do not hesitate to reach out."* or *"Best regards."*

### 🛠️ The Fix: The "Casual-Direct" Register
*   **Start with the answer:** Give the conclusion first, then explain if necessary.
*   **Embrace natural rhythm:** Use fragments, active voice, and varying sentence lengths. It is okay to skip capitalization at the beginning of short lines if replying in a rapid developer/chat environment.
*   **Keep it brief:** Treat chat as a conversation, not a document. Give the user one clear idea to digest per message.

---

## 3. Cold Outreach & B2B Sales Re-routing

AI sales emails are notoriously easy to spot because they rely on generic, speculative problem statements and weak, high-friction calls to action.

### 🚫 Banned Sales Templates
*   **Speculative "I imagine":** *"I imagine as a VP of Sales, you are always looking for ways to streamline operations..."*
*   **Generic Meeting Begging:** *"Would you be open to a quick 15-minute call this week?"* or *"Let me know if you have time to chat."*

### 🛠️ The Fix: The Signal-Grounded CTA
*   **Cite a hard signal:** Reference a specific verified data point, public news article, hiring post, or internal initiative.
*   **Offer low-friction value first:** Instead of begging for time, offer to send something valuable they can read asynchronously.
*   **Example human outreach:**
    > *"Hi Dave, I saw that Sprinklr is ramping up hires for MEA inside sales this quarter. That usually means training reps on regional accounts becomes the bottleneck. We wrote a 1-page guide on MEA-specific account brief templates. Let me know if you want me to drop the PDF here."*

---

## 4. Customer Support & Incident Protocol

When explaining errors, service outages, or customer service inquiries, AI defaults to high-friction, corporate over-apologies that make the company sound defensive and insecure.

### 🚫 Banned Support Templates
*   *“We sincerely apologize for any inconvenience this may have caused.”*
*   *“Please rest assured that our team is working diligently to resolve this.”*
*   *“Your business is highly important to us, and we appreciate your patience.”*

### 🛠️ The Fix: Direct Action and Accountability (Incident Format)
Use active voice, take direct ownership, and lay out the exact technical steps clearly.

*   **Before (AI):** *"We have identified an issue that may have impacted some users' ability to access our servers. We sincerely apologize for any inconvenience this may have caused and are working diligently to restore access as soon as possible."*
*   **After (Human):** *"Between 14:02 and 14:31 UTC, 12% of requests failed. A deploy at 14:00 removed our database caching warmup step, causing the database to overload. We have rolled back the deploy, and service is back to normal."*

---

## 5. Layout and Punctuation Clean-up

*   **Ban Em-Dash Stacking:** Do not use more than one em-dash (—) per email. AI overuses them to glue unrelated thoughts together.
*   **Keep Emails Under 120 Words:** Real human emails are short. Keep outreach, follow-ups, and notifications between 70 to 120 words.
*   **No Automated Sign-offs:** Do not write generic closings like *"Hope this helps!"* unless it is naturally suited to the conversational relationship.
