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
