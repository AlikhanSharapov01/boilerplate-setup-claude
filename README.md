# claude-boilerplate

My base setup for Claude Code:
- general working rules: discuss first, Karpathy's coding guidelines, a report after the work;
- AI attribution turned off in commits and PRs;
- a hook that stops Claude from committing and pushing to `main`.

## 1. Install (once per computer)

```bash
git clone https://github.com/AlikhanSharapov01/boilerplate-setup-claude.git && cd boilerplate-setup-claude && ./setup.sh
# preview what will change first (writes nothing): python3 scripts/install.py --global --dry-run
```

The script puts `CLAUDE.md`, `settings.json`, `hooks/guard-git.py` and `docs/` into `~/.claude`.
Before anything is changed, every existing file is copied to `<file>.bak-<date>`. Your
`settings.json` is not overwritten: the new settings are merged into it.

Check: the command should print `Blocked by guard-git ...` followed by `2`.

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main"},"cwd":"'$PWD'"}' \
  | python3 ~/.claude/hooks/guard-git.py; echo $?
```

## 2. New project

**With Claude (easier).** Open Claude Code in the project folder and write "set up the boilerplate
in this project". The `boilerplate-setup` skill looks at the repo, fills `CLAUDE.md` with the real
commands (build/test/lint/sim) and shows a plan. It starts writing files only after you say "go ahead".

**By hand.**

```bash
python3 scripts/install.py --project ~/path/to/repo
```

This puts an empty `CLAUDE.md` template into the project; you fill it in yourself.

If you open the project in Claude Code in the browser (claude.ai/code), add `--guard` to the command.
Your `~/.claude` is not visible there, so the hook has to live in the repo itself.

## 3. What the hook blocks

| Blocks | Does not block |
|---|---|
| commit / merge / rebase / reset / tag on `main`, `master`, `develop`, `production`, `release/*` | anything on feature branches, including force-push |
| any push to those branches, `push --all` | merging `main` into your branch |
| deleting or renaming those branches | `git pull` on `main` |
| `gh pr merge`, `gh pr review --approve` | `gh pr create` |

To protect more branches in a project, create a `.claude/protected-branches` file and
list one branch per line, for example `staging`.

## 4. Changing the boilerplate

| What you want to change | Where | Then |
|---|---|---|
| General rules | `global/CLAUDE.md` | `python3 scripts/install.py --global` |
| Rules for one project | `CLAUDE.md` in that project | nothing |
| The hook | `global/hooks/guard-git.py` | `python3 scripts/test_guard.py`, then `install.py --global` |

After any change in `global/` or `project/`, run `python3 scripts/build_skill.py` and
ask Claude to update the `boilerplate-setup` skill. Otherwise the skill keeps installing the old version.

## What lives where

```
global/      what gets installed into ~/.claude
project/     the project CLAUDE.md template and settings.project.json (for --guard)
skill/       the skill: SKILL.md is built from SKILL.template.md; evals/ are the skill's tests
scripts/     install.py, build_skill.py, test_guard.py
_old/        your previous CLAUDE.md and settings.json
```
