# RAD Brainstorm

RAD Brainstorm is an Agent Plugins 1.0.0 package for one-person, text-based idea work with Codex. It helps the user frame a question, create or compare ideas, and choose a small way to test the leading option. It cannot guarantee useful ideas or correct conclusions.

It is a good fit when normal chat feels too loose and a full product discovery process would be too much.

## Skills

| Skill | Use it for | Main result |
| --- | --- | --- |
| [rad-brainstorm:brainstorm-session](skills/brainstorm-session/SKILL.md) | A quick or full idea session for software, business, content, travel, creative work, or a personal choice | A recommendation, strong alternative, idea-source record, risky assumption, proof step, threshold, and stop signal |
| [rad-brainstorm:idea-evaluation](skills/idea-evaluation/SKILL.md) | Comparing two or more ideas that already exist | A user-led ranking with trade-offs and a test for the leader |
| [rad-brainstorm:five-whys](skills/five-whys/SKILL.md) | Framing the likely cause of a repeated problem | An evidence-labeled cause chain with uncertainty and untested branches |
| [rad-brainstorm:software-design](skills/software-design/SKILL.md) | Turning one chosen software direction into a reviewable technical design | An approved design spec with scope, interfaces, data flow, recovery, and focused test needs |

## How a brainstorm works

The normal flow is:

1. Choose quick or full depth and a facilitator, partner, or generator role.
2. Set the goal, affected person, success signal, and hard constraint.
3. Ask for the user's starting ideas before Codex adds ideas in facilitator or partner mode.
4. Label each idea as user, AI, or research.
5. Use one familiar idea method, such as SCAMPER, How Might We, reverse brainstorming, or Six Thinking Hats.
6. Group ideas by the way they work and check whether the set is truly varied.
7. Move into a separate evaluation phase. The user scores first.
8. End with a choice and a cheap proof that has a pass threshold and stop signal.

Quick mode uses one method, no subagents, and aims to finish within five user turns. Full mode can add consent-based research, one focused challenge, and one optional checkpoint.

## What is specific about it

Many brainstorming prompts use the same named methods. RAD Brainstorm's main difference is its control of AI timing and idea ownership.

The user contributes first when possible. Source labels keep the user's ideas visible. Generation and judgment have separate steps. Large idea sets keep their original IDs during grouping, and distinct ideas are not merged without approval.

The close also goes past a ranked list. The leading choice must name its weakest assumption, a low-cost proof, an observable pass point, and a reason to stop.

## Research and review

Current research is optional. The skill states the question and expected value, then asks before searching. User-provided research or design evidence keeps its exact path or link, claims, and source label. Any research or challenge stays bounded and read-only. JSON schemas check the shape of those optional results.

Schema validation proves that required fields and basic value rules are present. It does not prove that the sources, reasoning, or recommendation are correct.

## Output and file rules

Results can stay in chat or go to one approved Markdown file. When the user names a repository path, the skill repeats the exact repository path and asks for approval before writing. Quick sessions write no file unless asked. RAD Brainstorm does not commit files.

A software spec can be saved to a dated project file. The plugin does not write to docs/design.md because that path may already hold visual or brand direction.

## Limits

- This is a solo, text-first workflow. It has no shared canvas, live voting, workshop timer, or group facilitation service.
- Named methods guide the conversation. They do not ensure original or useful ideas.
- Five Whys produces a likely causal model. Evidence outside the conversation may still disprove it.
- Idea scores depend on the chosen criteria and the information supplied.
- Software design stops before implementation planning and coding.
- The plugin does not track projects or monitor deployment.

RAD Brainstorm works alone. It names a RAD Plan, RAD Repo, or RAD Council skill only when the exact skill appears in the current available-skill list, the current work needs it, and using it would add clear value. It asks whether the user accepts before invoking a companion. If the exact skill is absent or the user declines, the current session continues standalone. These source cases do not prove runtime behavior across models or prompts.

## Install

~~~powershell
codex plugin add rad-brainstorm@radesjardins-codex-skills
~~~

Example requests:

- "Run a quick brainstorm. Ask for my ideas before giving yours."
- "Compare these four ideas and help me define the cheapest useful test."
- "Use Five Whys, and mark which answers are evidence or assumptions."
- "Turn this chosen software idea into a design spec. Do not implement it."

## License

MIT. See [LICENSE](LICENSE).
