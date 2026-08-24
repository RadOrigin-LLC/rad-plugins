# RAD Writer

RAD Writer is an Agent Plugins 1.0.0 package for AI-assisted writing. It helps Codex draft, rewrite, copyedit, proofread, and review text for its intended reader and purpose.

Its goal is clear meaning, specific language, supported claims, useful structure, and a voice that fits the work. It covers academic, creative, technical, business, email, chat, support, outreach, social, marketing, and neutral reference writing.

RAD Writer does not:

- detect AI authorship;
- make generated text appear human;
- evade AI detectors;
- invent citations, evidence, personal experience, or story facts;
- guarantee factual accuracy, publication acceptance, or a particular reader response.

The skill sets different boundaries for drafting, rewriting, copyediting, proofreading, and review. It preserves facts, numbers, citations, uncertainty, plot details, code, and deliberate voice. It flags missing support instead of filling gaps with guesses.

## PARA handoff

PARA Express owns gathering and outlining source notes, while RAD Writer owns the accepted draft, rewrite, copyedit, proofread, or review operation.

RAD Writer may offer `rad-para:express-workflow` only when that exact skill appears in the current available-skill list. It asks whether the user accepts the handoff and waits for acceptance before invoking it. Once accepted, PARA Express returns the gathered notes or outline and RAD Writer handles the accepted operation. If the exact skill is absent or the user declines, RAD Writer continues the current operation standalone.

## Skill

| Skill | Use it for |
| --- | --- |
| [writing](skills/writing/SKILL.md) | Drafting, rewriting, copyediting, proofreading, and reviewing common forms of prose |

The skill selects an operation and a primary writing mode. It applies shared checks for clarity, evidence, voice, structure, accessibility, and accidental platform metadata, then uses the rules for the selected mode.

The package includes [behavior cases](tests/writing-cases.json) for manual or automated forward testing. They define required outcomes and preservation checks. They do not prove writing quality across every model or prompt.

## Install

~~~powershell
codex plugin add rad-writer@radesjardins-codex-skills
~~~

## Limits

Good editing still needs human review when facts, sources, privacy, safety, law, academic integrity, or publication rules matter. Editing alone does not verify claims. The skill can check claims only when the user requests verification and reliable sources are available.

Wikipedia and other governed projects can restrict AI-assisted text. The skill tells the agent to check current project rules before preparing text for publication.

RAD Writer has no hosted service, MCP server, background process, authorship detector, or automatic publishing action.

## License

MIT.
