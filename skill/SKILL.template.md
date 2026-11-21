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
{{file:global/CLAUDE.md}}
````

### `~/.claude/docs/handoff.md`

````markdown
{{file:global/docs/handoff.md}}
````

### `~/.claude/docs/multi-agent.md`

````markdown
{{file:global/docs/multi-agent.md}}
````

### `~/.claude/settings.json`

````json
{{file:global/settings.json}}
````

### `~/.claude/hooks/guard-git.py` (also `<repo>/.claude/hooks/guard-git.py` for the project guard)

````python
{{file:global/hooks/guard-git.py}}
````

### `<repo>/CLAUDE.md` (template)

````markdown
{{file:project/CLAUDE.md}}
````

### `<repo>/.claude/settings.json` (only for the project-level guard)

````json
{{file:project/settings.project.json}}
````
