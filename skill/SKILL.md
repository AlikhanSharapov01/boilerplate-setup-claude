---
name: boilerplate-setup
description: Installs and applies the user's universal Claude Code boilerplate — global rules in ~/.claude (CLAUDE.md with discuss-first and Karpathy coding guidelines, settings.json without AI attribution, a git hook that protects main) plus a project CLAUDE.md filled in from the repository. Use whenever the user asks to set up, init, bootstrap, update or check CLAUDE.md, Claude Code settings, "the boilerplate" or "базу" for a machine or a project, even if they do not name this skill.
---

# Claude Code boilerplate

This skill puts the user's standing Claude Code setup in place. It has two layers:

| Layer | Files | Where |
|---|---|---|
| Global (once per machine) | `CLAUDE.md`, `docs/handoff.md`, `docs/multi-agent.md`, `hooks/guard-git.py`, `settings.json` | `~/.claude/` |
| Project (once per repo) | `CLAUDE.md` with project facts only; optionally `.claude/hooks/guard-git.py` + `.claude/settings.json` | repo root |

The global rules are generic on purpose; the project file holds only facts about this repo (stack,
commands, layout, things not to touch). Keeping them apart means the rules are edited in one
place and every project picks them up.

The exact file contents are at the end of this skill. They are the source of truth: write them
byte-for-byte as given. Do not retype them from memory, "improve" them, or translate them.

## How to run it

The user works discuss-first: nothing is written until they give an explicit go-ahead ("go
ahead", "implement it", "давай", "делай"...). "Ok" or "sounds good" is not a go-ahead. So this
skill is inspect → propose → wait → write → verify.

### 1. Check the global layer

Global files belong in the user's own home directory. If this session is not on the user's
machine (a cloud container, a remote VM), say so: installing into this machine's `~/.claude`
would not reach them. Offer the project-level guard (step 3) instead, and skip to step 2.

Otherwise compare each global file with the embedded version and classify it:
- **missing** → will be created;
- **identical** → nothing to do;
- **differs** → show a short summary of the difference. It may contain the user's own edits, so
  ask whether to replace it (with a backup) or keep it.

`settings.json` is never replaced wholesale, because it usually holds other settings. Merge into
the existing file: set the `attribution` keys, add the `deny` rules that are missing, and add the
`PreToolUse` hook group if no hook already runs `guard-git.py`. Show the merged JSON in the
proposal.

### 2. Inspect the project

Read what describes how the project is built and run: README, manifests (`package.json`,
`pyproject.toml`, `Cargo.toml`, `go.mod`, `Package.swift` / `*.xcodeproj`, `CMakeLists.txt`,
`Makefile`, FuseSoC `*.core`, Verilator/simulator scripts, `*.sv`/`*.v` layout), CI config
(`.github/workflows/`), `.gitignore`, existing `CLAUDE.md` / `AGENTS.md`, and the top-level
directories. For a large repository, delegate this survey to a subagent that returns conclusions,
so the main context stays small.

Fill in the project template:
- Use only facts you found. Take commands from scripts, Makefiles, and CI, not from guesses.
  Where something is unknown, write `<TODO: ...>` and list it as a question for the user.
- Delete sections that do not apply. Aim for under ~40 lines.
- Do not repeat global rules in the project file; it would drift from the global copy.

If the project already has a `CLAUDE.md`, do not replace it. Propose a merge: keep its project
facts in the template's structure, and point out lines that duplicate the global rules (those can
go) or contradict them (keep them only as deliberate overrides, in "Overrides of global rules").

### 3. Ask about project-level options

- **Guard in the repo.** Cloud sessions and teammates do not read `~/.claude`. If the user wants
  the git guard to travel with this repo, add `.claude/hooks/guard-git.py` and merge
  `.claude/settings.json` (project version below). Default: no.
- **Extra protected branches** (e.g. `staging`) go one per line in `.claude/protected-branches`;
  the hook reads that file.

### 4. Propose and wait

Present one proposal: what you found, each file to create/change with its status (new, merge,
replace with backup, unchanged), the filled project `CLAUDE.md`, the open `<TODO>` questions, and
how you will verify. Then stop and wait for an explicit go-ahead.

### 5. Write and verify

1. Back up every existing file you change: `cp <file> <file>.bak-$(date +%Y%m%d-%H%M%S)`.
2. Write the files. Make the hook executable: `chmod +x <path>/guard-git.py`.
3. Verify, and report the actual output:
   - `python3 -c "import json,sys; json.load(open(sys.argv[1]))" <settings.json>` for each
     settings file you touched;
   - the hook blocks a push to main (expect exit code 2 and a "Blocked by guard-git" message):
     `echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main"},"cwd":"'"$PWD"'"}' | python3 <hook path>; echo "exit=$?"`
   - and lets a harmless command through (expect exit 0):
     `echo '{"tool_name":"Bash","tool_input":{"command":"git status"},"cwd":"'"$PWD"'"}' | python3 <hook path>; echo "exit=$?"`
4. Report in the user's format: every path changed and what changed in it (one line each), the
   verification commands with their real results, and anything skipped or left as `<TODO>`.
   Settings and hooks are reloaded automatically; a new session picks up the new `CLAUDE.md`.

Do not commit anything. If the user wants the project files committed, that happens on a feature
branch, with no AI attribution, after they ask.

## Embedded files

### `~/.claude/CLAUDE.md`

````markdown
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
````

### `~/.claude/docs/handoff.md`

````markdown
# HANDOFF.md template

Write `HANDOFF.md` in the project root so a fresh session can continue without this conversation.
Be specific: paths, function names, exact commands, exact error messages. Overwrite the previous
handoff rather than appending to it.

```markdown
# Handoff — <YYYY-MM-DD>

## Goal
<what the user wants, in one or two sentences>

## Decisions (and why)
- <decision> — <reason>

## Current state
- Works and verified: <what, and how it was verified>
- Done but not verified: <what>
- Broken / not started: <what>

## Exact next steps
1. <step> → verify: <command or check>

## Key files
- `<path>` — <role>

## Open questions
- <question for the user>
```

After writing it, tell the user it is ready so they can clear or compact the context.
````

### `~/.claude/docs/multi-agent.md`

````markdown
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
````

### `~/.claude/settings.json`

````json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "attribution": {
    "commit": "",
    "pr": "",
    "sessionUrl": false
  },
  "permissions": {
    "deny": [
      "Bash(git push origin main *)",
      "Bash(git push origin master *)",
      "Bash(gh pr merge *)",
      "Bash(gh pr review --approve *)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$HOME/.claude/hooks/guard-git.py\""
          }
        ]
      }
    ]
  }
}
````

### `~/.claude/hooks/guard-git.py` (also `<repo>/.claude/hooks/guard-git.py` for the project guard)

````python
#!/usr/bin/env python3
"""PreToolUse hook for Claude Code: blocks git/gh commands that touch protected branches.

Reads the hook payload (JSON) on stdin. Exit 2 with a message on stderr blocks the command;
exit 0 lets the normal permission flow continue.

Blocked:
  - commit, merge, rebase, reset (moving the branch), cherry-pick, revert, am, tag creation
    while the current branch is protected
  - push whose target is a protected branch (explicit refspec, upstream, or current branch),
    push --all / --mirror
  - deleting or renaming a protected branch
  - gh pr merge, gh pr review --approve
Allowed: anything on feature branches, including force-push and merging main into a feature branch.

Protected: main, master, develop, production, release/*, the remote default branch, and patterns
listed one per line in <repo>/.claude/protected-branches.
"""
import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

BASE_PROTECTED = ["main", "master", "develop", "production", "release/*"]
SEPARATORS = {"&&", "||", ";", "|", "&", "|&", "(", ")", ";;"}
WRAPPERS = {"sudo", "env", "command", "time", "nohup", "exec", "builtin"}
BRANCH_LOCKING = {"commit", "merge", "rebase", "cherry-pick", "revert", "am"}


def git(cwd, *args):
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args], capture_output=True, text=True, timeout=3
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


class Repo:
    def __init__(self, cwd):
        self.cwd = cwd
        self.sim_branch = None  # set when the command itself switches branches

    def branch(self):
        if self.sim_branch is not None:
            return self.sim_branch
        return git(self.cwd, "symbolic-ref", "--short", "-q", "HEAD") or None

    def patterns(self):
        pats = list(BASE_PROTECTED)
        default = git(self.cwd, "symbolic-ref", "--short", "-q", "refs/remotes/origin/HEAD")
        if default.startswith("origin/"):
            pats.append(default[len("origin/"):])
        top = git(self.cwd, "rev-parse", "--show-toplevel")
        if top:
            try:
                with open(os.path.join(top, ".claude", "protected-branches")) as f:
                    for line in f:
                        line = line.split("#", 1)[0].strip()
                        if line:
                            pats.append(line)
            except OSError:
                pass
        return pats

    def protected(self, name):
        if not name:
            return False
        name = re.sub(r"^refs/heads/", "", name)
        return any(fnmatch.fnmatchcase(name, p) for p in self.patterns())

    def upstream_branch(self):
        up = git(self.cwd, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        return up.split("/", 1)[1] if "/" in up else None

    def is_commit(self, arg):
        return bool(git(self.cwd, "rev-parse", "--verify", "-q", arg + "^{commit}"))


def tokenize(command):
    text = command.replace("\r", "").replace("\n", " ; ")
    try:
        lex = shlex.shlex(text, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        return re.sub(r"([;&|()])", r" \1 ", text).split()


def segments(tokens):
    seg = []
    for tok in tokens:
        if tok in SEPARATORS or set(tok) <= set(";&|()"):
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def strip_prefix(seg):
    i = 0
    while i < len(seg) and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", seg[i]) or seg[i] in WRAPPERS):
        i += 1
    return seg[i:]


def check_push(repo, args):
    positionals, flags = [], []
    takes_value = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a in takes_value:
            skip = True
        (flags if a.startswith("-") else positionals).append(a)
    if any(f in ("--all", "--mirror") for f in flags):
        return "push --all/--mirror would push protected branches"
    refspecs = positionals[1:]
    targets = []
    current = repo.branch()
    if not refspecs:
        targets = [repo.upstream_branch() or current]
        if current:
            targets.append(current)
    for spec in refspecs:
        spec = spec.lstrip("+")
        src, _, dst = spec.partition(":")
        if not dst:
            dst = current if src in ("HEAD", "@") else src
        targets.append(dst)
    for t in targets:
        if repo.protected(t):
            return f"push targets protected branch '{t}'"
    return None


def check_git(repo, seg):
    i = 1
    while i < len(seg) and seg[i].startswith("-"):
        opt = seg[i]
        if opt == "-C" and i + 1 < len(seg):
            repo.cwd = os.path.join(repo.cwd, os.path.expanduser(seg[i + 1]))
            i += 2
        elif opt in ("-c", "--git-dir", "--work-tree", "--namespace") and i + 1 < len(seg):
            i += 2
        else:
            i += 1
    if i >= len(seg):
        return None
    sub, args = seg[i], seg[i + 1:]
    branch = repo.branch()
    on_protected = repo.protected(branch)

    if sub in ("checkout", "switch"):
        names = [a for a in args if not a.startswith("-")]
        if "--" not in args and names:
            for flag in ("-b", "-B", "-c", "-C", "--create", "--force-create"):
                if flag in args and args.index(flag) + 1 < len(args):
                    repo.sim_branch = args[args.index(flag) + 1]
                    return None
            if sub == "switch" or repo.is_commit(names[0]):
                repo.sim_branch = names[0]
        return None
    if sub in BRANCH_LOCKING and on_protected:
        return f"'git {sub}' on protected branch '{branch}'"
    if sub == "reset" and on_protected:
        modes = {"--hard", "--soft", "--mixed", "--keep", "--merge"}
        positional = [a for a in args if not a.startswith("-")]
        looks_like_rev = positional and "--" not in args and (
            re.search(r"[~^@]", positional[0]) or repo.is_commit(positional[0])
        )
        if modes & set(args) or looks_like_rev:
            return f"'git reset' would move protected branch '{branch}'"
    if sub == "tag" and on_protected:
        listing = not args or any(a in ("-l", "--list", "-d", "--delete", "-v", "--verify") for a in args)
        if not listing:
            return f"creating a tag on protected branch '{branch}'"
    if sub == "branch":
        if any(a in ("-d", "-D", "--delete", "-m", "-M", "--move", "-f", "--force") for a in args):
            for name in (a for a in args if not a.startswith("-")):
                if repo.protected(name):
                    return f"deleting/renaming/resetting protected branch '{name}'"
    if sub == "push":
        return check_push(repo, args)
    return None


def check_gh(seg):
    if len(seg) >= 3 and seg[1] == "pr" and seg[2] == "merge":
        return "merging PRs is reserved for the user"
    if len(seg) >= 3 and seg[1] == "pr" and seg[2] == "review" and any(
        a in ("--approve", "-a") for a in seg[3:]
    ):
        return "approving PRs is reserved for the user"
    return None


def evaluate(command, cwd):
    repo = Repo(cwd)
    for seg in segments(tokenize(command)):
        seg = strip_prefix(seg)
        if not seg:
            continue
        prog = os.path.basename(seg[0])
        if prog == "cd":
            target = os.path.expanduser(seg[1]) if len(seg) > 1 else os.path.expanduser("~")
            repo.cwd = os.path.join(repo.cwd, target)
            repo.sim_branch = None
            continue
        reason = check_git(repo, seg) if prog == "git" else check_gh(seg) if prog == "gh" else None
        if reason:
            return reason
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if "git" not in command and "gh" not in command:
        return 0
    try:
        reason = evaluate(command, payload.get("cwd") or os.getcwd())
    except Exception as exc:  # never break the session because of a parser bug
        print(f"guard-git: internal error, not blocking: {exc}", file=sys.stderr)
        return 0
    if reason:
        print(
            f"Blocked by guard-git: {reason}. Protected branches are changed only by the user. "
            "Use a feature branch, or ask the user to do this themselves.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

### `<repo>/CLAUDE.md` (template)

````markdown
# <Project name>

<!-- Global working rules live in ~/.claude/CLAUDE.md. Keep this file to project facts and
     deliberate overrides. Delete any section that does not apply. -->

## What it is
<one or two sentences>

## Stack
<languages, frameworks, toolchain and versions>

## Commands
- Build: `<command>`
- Test: `<command>`
- Lint/format: `<command>`
- Run/simulate: `<command>`

## Layout
- `<dir>/` — <purpose>

## Conventions
<naming, style guide, architecture rules that are not obvious from the code>

## Do not touch
<generated files, vendored code, protected areas>

## Overrides of global rules
<only deliberate deviations, e.g. extra protected branches; otherwise delete this section>
````

### `<repo>/.claude/settings.json` (only for the project-level guard)

````json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "attribution": {
    "commit": "",
    "pr": "",
    "sessionUrl": false
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/guard-git.py\""
          }
        ]
      }
    ]
  }
}
````
