#!/usr/bin/env python3
"""Tests for global/hooks/guard-git.py. Run: python3 scripts/test_guard.py

Creates throwaway git repos (with a bare "origin" whose default branch is main) in a temp dir
and feeds the hook the same JSON payload Claude Code sends.
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "global", "hooks", "guard-git.py")


def sh(cwd, cmd):
    subprocess.run(cmd, cwd=cwd, shell=True, check=True, capture_output=True)


def make_repo(root):
    remote = os.path.join(root, "remote.git")
    work = os.path.join(root, "work")
    sh(root, f"git init -q --bare -b main {remote}")
    sh(root, f"git clone -q {remote} work 2>/dev/null || git clone -q {remote} work")
    sh(work, "git config user.email t@t && git config user.name t && git checkout -q -b main")
    sh(work, "echo a > a.txt && git add a.txt && git commit -qm init && git push -q -u origin main")
    sh(work, "git remote set-head origin main")
    sh(work, "git checkout -q -b feat/x && git push -q -u origin feat/x")
    return work


def run(cwd, command):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(payload), capture_output=True, text=True)
    return p.returncode, p.stderr.strip()


def main():
    root = tempfile.mkdtemp()
    work = make_repo(root)
    on_feat = [
        # (command, should_block)
        ("git status", False),
        ("git commit -m 'feat: x; y && z'", False),
        ("git push", False),
        ("git push -u origin feat/x", False),
        ("git push --force origin feat/x", False),
        ("git push -f", False),
        ("git merge main", False),
        ("git rebase main", False),
        ("git reset --hard HEAD~1", False),
        ("git push origin main", True),
        ("git push origin HEAD:main", True),
        ("git push origin feat/x:main", True),
        ("git push origin +feat/x:master", True),
        ("git push origin :main", True),
        ("git push origin release/1.0", True),
        ("git push --all", True),
        ("git branch -D main", True),
        ("git checkout main && git commit -m x", True),
        ("git switch main; git merge feat/x", True),
        ("git checkout -b feat/y && git commit -m x", False),
        ("cd /tmp && cd " + work + " && git push origin main", True),
        ("git -C " + work + " push origin main", True),
        ("gh pr merge 12 --squash", True),
        ("gh pr review 12 --approve", True),
        ("gh pr create --fill", False),
        ("git commit -m \"$(cat <<'EOF'\nfeat: multi\n\nline; git push origin main\nEOF\n)\"", False),
        ("git log --oneline | head", False),
        ("echo 'git push origin main'", False),
    ]
    sh(work, "git checkout -q main")
    on_main = [
        ("git status", False),
        ("git pull", False),
        ("git checkout -b feat/z", False),
        ("git checkout -b feat/z && git commit -am x", False),
        ("git commit -am x", True),
        ("git push", True),
        ("git push origin", True),
        ("git merge feat/x", True),
        ("git rebase feat/x", True),
        ("git reset --hard origin/main", True),
        ("git reset HEAD~1", True),
        ("git reset a.txt", False),
        ("git tag v1", True),
        ("git tag -l", False),
        ("git cherry-pick abc123", True),
        ("git checkout -- a.txt", False),
    ]
    failures = 0
    for label, cases, branch in (("on feat/x", on_feat, "feat/x"), ("on main", on_main, "main")):
        sh(work, f"git checkout -q {branch}")
        for cmd, should_block in cases:
            code, err = run(work, cmd)
            blocked = code == 2
            ok = blocked == should_block
            failures += not ok
            mark = "ok  " if ok else "FAIL"
            print(f"{mark} [{label}] {'BLOCK' if blocked else 'allow'}: {cmd!r}" + (f"  ({err})" if not ok and err else ""))
    # protected-branches file
    os.makedirs(os.path.join(work, ".claude"), exist_ok=True)
    with open(os.path.join(work, ".claude", "protected-branches"), "w") as f:
        f.write("# extra\nstaging\n")
    sh(work, "git checkout -q feat/x")
    code, _ = run(work, "git push origin staging")
    ok = code == 2
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} [extra file] {'BLOCK' if code == 2 else 'allow'}: 'git push origin staging'")
    # outside any repo, explicit main is still blocked
    code, _ = run(root, "git push origin main")
    ok = code == 2
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} [no repo] {'BLOCK' if code == 2 else 'allow'}: 'git push origin main'")
    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
