# Multi-agent setup

Use this when a task splits into roles that can work independently, such as
research/exploration, implementation, tests/verification, review, docs. Do not split work that is
small or tightly coupled; one agent with a short plan is cheaper there.

## Proposal (part of the plan, before any go-ahead)

State for each role: what it owns, which files it may modify, which model it runs on, and what it
hands back (format and level of detail). Use the strongest model for the orchestrator and cheaper
models for narrow, well-specified workers.

## Setup (only after a go-ahead)

- `AGENTS.md` in the project root: roles, responsibilities, inputs/outputs, and boundaries
  (which files each agent may modify).
- One definition per role in `.claude/agents/<name>.md` with frontmatter:

  ```markdown
  ---
  name: <name>
  description: <when the orchestrator should use this agent>
  tools: <comma-separated tool list, as narrow as the role allows>
  model: <model>
  ---
  <instructions for the role>
  ```

## Running it

- The orchestrator keeps its own context small: it dispatches, integrates results, and reports to
  the user. Workers do the reading and heavy lifting and return conclusions with `file:line`.
- Verification and review agents must not see the implementation reasoning. They check the result
  against the spec.
- All agent files and inter-agent prompts are in English.
