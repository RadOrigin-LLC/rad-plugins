#!/usr/bin/env python3
"""
Writing Style Master Orchestrator & AI Tell Linter
A programmatic utility to audit text for common LLM writing tells,
compute metrics (sentence length distribution, overrepresented vocabulary),
and route the document to the correct writing clean-up skill.
"""

import re
import sys
import argparse
from typing import Dict, List, Any

# 2026 Word Blacklist grouped by tier & category
TIER_1_KILLS = {
    "delve", "delves", "delving", "tapestry", "underscores", "underscored",
    "underscoring", "testament", "pivotal", "intricate", "intricacies",
    "meticulous", "meticulously", "foster", "fostering", "elevate", "elevating",
    "shaping", "seamless", "seamlessly", "robust", "vibrant", "landscape",
    "realm", "mosaic", "symphony", "odyssey", "beacon", "cornerstone", "bedrock"
}

TIER_2_SUSPICIOUS = {
    "leverage", "utilize", "utilization", "synchronize", "optimize", "optimization",
    "foster", "ignite", "transform", "transformative", "revolutionary", "disruptive",
    "cutting-edge", "future-ready", "unlock", "empower", "empowerment", "unwavering",
    "commendable", "compelling", "paramount", "resonate", "resonates", "pave the way",
    "to the best of our knowledge", "in today's fast-paced world", "ever-evolving"
}

PLATFORM_LEAKS = {
    "contentReference": "ChatGPT citation index",
    "oai_citation": "OpenAI citation annotation",
    r"\[cite:\s*\d+\]": "Gemini citation span",
    r"【\d+†L\d+】": "DeepSeek lenticular citation",
    r"【\d+†source】": "ChatGPT citation bracket",
    r"<span[^>]*class=\"cite\"[^>]*>": "Gemini span metadata",
    r"utm_source=copilot": "Microsoft Copilot web query parameter"
}

class WritingLinter:
    def __init__(self, text: str):
        self.text = text
        self.sentences = self._split_sentences()
        self.words = self._tokenize_words()

    def _split_sentences(self) -> List[str]:
        # Simple regex for sentence splitting that respects abbreviations
        sentence_end = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
        return [s.strip() for s in sentence_end.split(self.text) if s.strip()]

    def _tokenize_words(self) -> List[str]:
        # Normalize and strip punctuation for pure token analysis
        return re.findall(r'\b[a-zA-Z-]+\b', self.text.lower())

    def analyze_sentence_lengths(self) -> Dict[str, Any]:
        """
        Analyzes the distribution of sentence lengths.
        In human writing, >25% of sentences are short (<= 5 words).
        In AI writing, fewer than 4% are short, with ~40% clustered in 21-35 words.
        """
        total = len(self.sentences)
        if total == 0:
            return {"short_pct": 0.0, "medium_large_pct": 0.0, "avg_length": 0.0, "verdict": "No Text"}

        short_sentences = [s for s in self.sentences if len(s.split()) <= 5]
        med_large_sentences = [s for s in self.sentences if 21 <= len(s.split()) <= 35]
        avg_len = sum(len(s.split()) for s in self.sentences) / total

        short_pct = (len(short_sentences) / total) * 100
        med_large_pct = (len(med_large_sentences) / total) * 100

        # Run heuristic check based on Forbes / Leadership IQ data
        is_monotonous = short_pct < 8.0 and med_large_pct > 30.0

        return {
            "total_sentences": total,
            "avg_length": round(avg_len, 2),
            "short_pct": round(short_pct, 2),
            "med_large_pct": round(med_large_pct, 2),
            "is_monotonous": is_monotonous,
            "verdict": "FAIL (Monotonous AI Rhythm)" if is_monotonous else "PASS"
        }

    def scan_vocabulary(self) -> Dict[str, Any]:
        """Checks for overused style terms and Tier 1 / Tier 2 blacklisted items."""
        found_t1 = {}
        found_t2 = {}

        # Look for literal phrase/word matches
        for word in self.words:
            if word in TIER_1_KILLS:
                found_t1[word] = found_t1.get(word, 0) + 1
            elif word in TIER_2_SUSPICIOUS:
                found_t2[word] = found_t2.get(word, 0) + 1

        # Direct string matches for multi-word phrases
        lowercased_text = self.text.lower()
        for phrase in TIER_2_SUSPICIOUS:
            if len(phrase.split()) > 1 and phrase in lowercased_text:
                found_t2[phrase] = found_t2.get(phrase, 0) + lowercased_text.count(phrase)

        total_violations = sum(found_t1.values()) + sum(found_t2.values())
        density = (total_violations / len(self.words)) * 100 if self.words else 0.0

        return {
            "tier_1_violations": found_t1,
            "tier_2_violations": found_t2,
            "total_violations": total_violations,
            "density_pct": round(density, 2),
            "verdict": "FAIL (High AI Word Density)" if density > 1.5 else "PASS"
        }

    def scan_syntactic_patterns(self) -> List[Dict[str, Any]]:
        """Scans for structural templates like negative parallelisms or prompt bleed."""
        issues = []

        # 1. Negative parallelism ("not only X, but Y", "not X, it's Y")
        neg_parallel_pattern = r"(?i)\bis not\s+[^,.]+\bbut\s+[^,.]+\b|\bisn't\s+[^,.]+\bit's\s+[^,.]+\b"
        matches = re.findall(neg_parallel_pattern, self.text)
        if matches:
            issues.append({
                "type": "Negative Parallelism",
                "description": "Repetitive contrastive structures (e.g., 'not X, it's Y'). AI uses this 300% more than humans.",
                "matches": matches
            })

        # 2. Em dash overuse
        em_dashes = len(re.findall(r'—|--', self.text))
        if em_dashes > (len(self.sentences) * 0.4): # If em-dashes exceed 40% of sentence count
            issues.append({
                "type": "Em-Dash Overuse",
                "description": "Over-reliance on em-dashes to create faux complexity or conversational pacing.",
                "matches": [f"Found {em_dashes} em-dashes across {len(self.sentences)} sentences."]
            })

        # 3. Bold Header bullet structures
        bold_bullet_lists = re.findall(r'^\s*[\-\*]\s+\*\*[^*]+\*\*:', self.text, re.MULTILINE)
        if len(bold_bullet_lists) >= 3:
            issues.append({
                "type": "Symmetrical Bold-Header Lists",
                "description": "Uniform bold-keyword-colon list items. Typical AI layout tell.",
                "matches": bold_bullet_lists
            })

        return issues

    def scan_platform_metadata(self) -> List[Dict[str, Any]]:
        """Checks for accidental platform markers, system prompt leakage, or weird citation formatting."""
        leaks = []
        for pattern, source in PLATFORM_LEAKS.items():
            matches = re.findall(pattern, self.text)
            if matches:
                leaks.append({
                    "pattern": pattern,
                    "platform": source,
                    "occurrences": len(matches)
                })
        return leaks

    def detect_best_route(self) -> str:
        """Determines the correct humanizing sub-skill module to route this text to."""
        # Classify based on structural cues
        text_lower = self.text.lower()

        # 1. Academic Checks (citation templates, formal preambles)
        if re.search(r'\(\w+ et al\., \d{4}\)|\[\d+\]', self.text) or "abstract" in text_lower:
            return "academic-writing-cleaner-skill.md"

        # 2. Technical / STE checks (code blocks, command line syntax, markdown tables)
        if "```" in self.text or "config" in text_lower or "api" in text_lower:
            return "technical-writing-cleaner-skill.md"

        # 3. Email & Messaging (standard greetings/closings, outreach signals)
        email_signatures = ["best regards", "sincerely", "hope this email finds you", "reach out", "best,"]
        if any(sig in text_lower for sig in email_signatures):
            return "email-messaging-cleaner-skill.md"

        # 4. Social Media / B2B Copy (short lines, emojis, high linebreaks, CTA)
        if self.text.count("\n\n") > (len(self.sentences) * 0.8) or "linkedin" in text_lower:
            return "social-media-b2b-writing-cleaner-skill.md"

        # 5. Creative Writing (high narrative character reference, dialogue structures)
        dialogue_markers = len(re.findall(r'"[^"\n]+"', self.text))
        if dialogue_markers >= 3 or "chapter" in text_lower:
            return "creative-writing-cleaner-skill.md"

        # 6. Wikipedia / Neutral Informational (heavy usage of passive or factual statements)
        if "wikipedia" in text_lower or "category:" in text_lower:
            return "wikipedia-neutral-writing-cleaner-skill.md"

        # Default fallback
        return "ai-writing-cleaner-skill.md"

    def run_full_audit(self) -> Dict[str, Any]:
        sentence_metrics = self.analyze_sentence_lengths()
        vocab_metrics = self.scan_vocabulary()
        syntactic_issues = self.scan_syntactic_patterns()
        metadata_leaks = self.scan_platform_metadata()
        routed_skill = self.detect_best_route()

        score = 100
        # Simple scoring deduction logic
        if sentence_metrics["is_monotonous"]:
            score -= 25
        score -= int(vocab_metrics["density_pct"] * 15)
        score -= (len(syntactic_issues) * 15)
        score -= (len(metadata_leaks) * 20)

        final_score = max(0, score)

        return {
            "human_score": final_score,
            "sentence_length": sentence_metrics,
            "vocabulary": vocab_metrics,
            "syntax": syntactic_issues,
            "platform_leaks": metadata_leaks,
            "recommended_route": routed_skill
        }

def print_report(results: Dict[str, Any]):
    print("=" * 60)
    print("               AI WRITING AUDIT REPORT                      ")
    print("=" * 60)
    print(f"Human-Like Authenticity Score: {results['human_score']}/100")
    print(f"Verdict Profile: {'NATURAL HUMAN' if results['human_score'] >= 80 else 'SUSPECTED MACHINE / AI SLOP'}")
    print("-" * 60)

    # Sentence length
    sl = results["sentence_length"]
    print(f"Sentence Rhythm Metrics:")
    print(f"  - Avg Length: {sl['avg_length']} words")
    print(f"  - Short Sentences (<=5 words): {sl['short_pct']}%  [Target: >25% for high-burst human style]")
    print(f"  - Monotone Clustered Sentences (21-35 words): {sl['med_large_pct']}%  [Target: <15%]")
    print(f"  - Rhythm Verdict: {sl['verdict']}")
    print("-" * 60)

    # Vocabulary
    v = results["vocabulary"]
    print(f"Linguistic Tell Detections:")
    print(f"  - Total Blacklisted Words Found: {v['total_violations']}")
    print(f"  - Tell Density: {v['density_pct']}%  [Suspicion threshold: >1.5%]")
    if v["tier_1_violations"]:
         print(f"  - Tier 1 (Kill-On-Sight): {dict(v['tier_1_violations'])}")
    if v["tier_2_violations"]:
         print(f"  - Tier 2 (Suspicious): {dict(v['tier_2_violations'])}")
    print("-" * 60)

    # Syntax
    if results["syntax"]:
        print("Syntactic Alignment Flaws:")
        for issue in results["syntax"]:
            print(f"  [{issue['type']}]: {issue['description']}")
            print(f"    Occurrences: {issue['matches']}")
        print("-" * 60)

    # Metadata leaks
    if results["platform_leaks"]:
        print("CRITICAL: Platform Formatting Metadata Leakage Detected:")
        for leak in results["platform_leaks"]:
            print(f"  - Pattern: {leak['pattern']} ({leak['platform']}) -> Found {leak['occurrences']} times")
        print("-" * 60)

    # Actionable Routing recommendation
    print(f"Actionable Route Selection:")
    print(f"  Recommended System Prompt: {results['recommended_route']}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit and route writing based on 2026 AI tells.")
    parser.add_argument("file", nargs="?", help="Path to text file to audit.")
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    else:
        # Fallback sample showcasing AI Tells to run by default
        content = """
        Leveraging sqlpipe's robust architecture, users can seamlessly synchronize their Postgres tables to S3.
        It is pivotal to delve deep into the intricacies of your configurations so you can foster better outcomes.
        In today's fast-paced world, this serves as an invaluable testament to engineering excellence.
        It's not about working harder, it's about working smarter — as observers have noted in several industry reports.
        """
        print("No input file provided. Running audit on default demo text...\n")

    linter = WritingLinter(content)
    audit_results = linter.run_full_audit()
    print_report(audit_results)
