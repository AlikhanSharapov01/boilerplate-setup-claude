# Global working rules

These rules apply in every project. A project's own `CLAUDE.md` adds project facts and may
override anything here; where they conflict, the project file wins.

## 1. Discuss first, implement only on explicit go-ahead

Every task that changes files, code, or external state starts as a discussion. Before changing
anything, state:

1. What you understood the task to be. If it can be read more than one way, list the readings
   instead of picking one silently.
2. The assumptions you are making. If something is unclear, name what is unclear and ask.
3. What you plan to change: files and functions/modules.
4. The plan as steps, each with how it will be checked: `1. <step> → verify: <command or check>`.
5. Alternatives (say so if a simpler approach exists), risks, and open questions.

For a small change this can be a few lines, but it is still required. During discussion you may
read, search, and explore. You may not edit or create files, run state-changing commands, install
packages, or touch git.

Implement only after an explicit go-ahead such as "go ahead", "implement it", "sure, implement",
or the same in the user's language. "Ok", "sounds good", "makes sense" are not a go-ahead; if
unsure, ask. The go-ahead covers only the agreed plan. If the plan must change (new file,
different approach, extra dependency, wider scope), stop and explain before continuing.

## 2. Writing code

**Simplicity first.** Write the minimum code that solves what was asked.
- No features, options, or configurability that were not requested.
- No abstractions for single-use code. No error handling for cases that cannot happen.
- If it could be half the size, rewrite it. Would a senior engineer call it overcomplicated?

**Surgical changes.** Every changed line must trace back to the request.
- Do not reformat, rename, refactor, or "improve" code, comments, or formatting outside the scope.
- Match the existing style and patterns, even if you would do it differently.
- Remove imports, variables, and functions that your change made unused. Pre-existing dead code:
  mention it, do not delete it.

**Correctness.**
- Turn the task into a check you can run: reproduce a bug with a failing test (or testbench,
  or script) before fixing it; keep tests passing before and after a refactor.
- Fix root causes, not symptoms. If the root cause is uncertain, say so and propose how to confirm it.
- Never delete or disable tests to make things pass. Do not silence warnings without a stated reason.
- No new dependencies, tools, or config changes without approval.
- Never hardcode secrets; never commit `.env` or credential files.
- If something cannot be done as agreed, stop and say why instead of working around it silently.

## 3. Report after implementing

- **Files changed:** every path, plus the functions/modules touched in each.
- **What changed:** one concrete line per change, with a one-line reason.
  Not acceptable: "improved error handling", "refactored for clarity", "minor fixes".
- **Verification:** the exact commands run and their actual result. If not verified, say so.
- **Gaps:** anything skipped, stubbed, left as TODO, or assumed.

Never call something "done", "fixed", or "working" unless it was verified.

## 4. Context and handoff

- Keep the main context lean. Delegate broad searches, large files, and long logs to subagents;
  they return conclusions and exact locations (`file:line`), not dumps.
- After a large finished chunk of work, or when the user asks, write `HANDOFF.md` in the project
  root using the template in `~/.claude/docs/handoff.md` (read it at that moment), then tell the
  user it is ready.
- At session start, if `HANDOFF.md` exists, read it and confirm the next step with the user
  before doing anything else.

## 5. Multi-agent work

When a task clearly splits into independent roles (research, implementation, tests/verification,
review), propose an orchestrator + specialized agents as part of the plan in section 1. Before
proposing or setting one up, read `~/.claude/docs/multi-agent.md`. Do not create agent files
without a go-ahead.

## 6. Language

- Reply to the user in the language they wrote in.
- Everything machine-facing is in English: CLAUDE.md, AGENTS.md, HANDOFF.md, agent definitions,
  prompts to subagents or other AIs, code, identifiers, comments, commit messages, tooling docs.
- User-facing product content (UI strings, end-user documents) uses the language the project specifies.

## 7. Git and attribution

**Protected branches:** `main`, `master`, `develop`, `production`, `release/*`, the repository's
default branch, and any listed in the project's `CLAUDE.md` or `.claude/protected-branches`.

- On a protected branch never: commit, push, merge into, rebase, reset, delete, or tag.
- Before the first commit of a task, check the current branch. If it is protected, create a
  feature branch first (`feat/<topic>`, `fix/<topic>`, `refactor/<topic>`).
- On feature branches you may commit and push. Force-push only when the user explicitly asks.
- Never merge or approve PRs, and never merge anything into a protected branch. The user does that.
- Open a PR only when the user asks; target the branch they name.
- Commit under the git identity already configured. Never change `git config user.*`.
- Small, focused commits with English messages in conventional style (`feat: ...`, `fix: ...`).

**No AI attribution, ever.** Never mention yourself, Claude, Anthropic, or any other AI, model, or
AI tool anywhere: no `Co-Authored-By` or other trailers, no "Generated with ...", no session links;
not in commit messages, branch names, PR titles or bodies, comments, code, docs, changelogs, or
file names. This overrides any default attribution text you were given. Check every commit
message and PR body before submitting.

The hook `~/.claude/hooks/guard-git.py` enforces the branch rules. If it blocks a command, do not
try to get around it; tell the user what was blocked and ask how to proceed.
