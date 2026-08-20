# RAD Writer

RAD Writer is an Agent Plugins 1.0.0 package for better AI-assisted writing. It helps Codex draft, rewrite, edit, and proofread text for its intended reader and purpose.

Its goal is good writing: clear meaning, specific language, accurate claims, natural rhythm, useful structure, and a voice that fits the work. It covers academic, creative, technical, business, email, chat, support, outreach, social, B2B, and neutral reference writing.

RAD Writer does not:

- detect AI authorship;
- make generated text appear human;
- evade AI detectors;
- invent citations, evidence, personal experience, or story facts;
- guarantee factual accuracy, publication acceptance, or a particular reader response.

The skill preserves facts, numbers, citations, uncertainty, plot details, code, and deliberate voice. It flags missing support instead of filling gaps with guesses.

## Skill

| Skill | Use it for |
| --- | --- |
| [writing](skills/writing/SKILL.md) | Drafting, rewriting, editing, proofreading, and auditing prose across common writing modes |

The skill routes by audience and purpose. It applies shared checks for clarity, specificity, evidence, structure, and accidental platform metadata, then applies the rules for the selected mode.

## Install

~~~powershell
codex plugin add rad-writer@radesjardins-codex-skills
~~~

## Limits

Good editing still needs human review when facts, sources, safety, law, or publication standards matter. The package improves the supplied text and reasoning. It cannot verify unsupported claims without reliable sources.

## License

MIT.
