#!/usr/bin/env python3
"""Install the boilerplate by hand (the boilerplate-setup skill does the same steps interactively).

  python3 scripts/install.py --global              # ~/.claude: CLAUDE.md, docs/, hooks/, settings.json
  python3 scripts/install.py --project PATH        # PATH/CLAUDE.md from the template (if absent)
  python3 scripts/install.py --project PATH --guard  # also PATH/.claude/hooks + settings.json
  add --dry-run to only print what would change

Existing files are never overwritten silently: a changed file is backed up as <file>.bak-<timestamp>
first, and settings.json is merged (attribution, deny rules, hook) instead of replaced.
"""
import argparse
import filecmp
import json
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP = time.strftime("%Y%m%d-%H%M%S")
DRY = False


def say(msg):
    print(("[dry-run] " if DRY else "") + msg)


def copy(src, dst, executable=False):
    if os.path.exists(dst):
        if filecmp.cmp(src, dst, shallow=False):
            say(f"unchanged  {dst}")
            return
        say(f"backup     {dst} -> {dst}.bak-{STAMP}")
        if not DRY:
            shutil.copy2(dst, f"{dst}.bak-{STAMP}")
    say(f"write      {dst}")
    if not DRY:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        if executable:
            os.chmod(dst, 0o755)


def merge_settings(src, dst):
    new = json.load(open(src))
    if not os.path.exists(dst):
        copy(src, dst)
        return
    cur = json.load(open(dst))
    merged = json.loads(json.dumps(cur))
    merged.setdefault("$schema", new["$schema"])
    merged.setdefault("attribution", {}).update(new["attribution"])
    if "permissions" in new:
        deny = merged.setdefault("permissions", {}).setdefault("deny", [])
        deny += [r for r in new["permissions"]["deny"] if r not in deny]
    new_hook = new["hooks"]["PreToolUse"][0]
    groups = merged.setdefault("hooks", {}).setdefault("PreToolUse", [])
    cmd = new_hook["hooks"][0]["command"]
    if not any(h.get("command") == cmd for g in groups for h in g.get("hooks", [])):
        groups.append(new_hook)
    if merged == cur:
        say(f"unchanged  {dst}")
        return
    say(f"backup     {dst} -> {dst}.bak-{STAMP}")
    say(f"merge      {dst}")
    if not DRY:
        shutil.copy2(dst, f"{dst}.bak-{STAMP}")
        with open(dst, "w") as f:
            json.dump(merged, f, indent=2)
            f.write("\n")


def install_global():
    home = os.path.expanduser("~/.claude")
    g = os.path.join(ROOT, "global")
    copy(os.path.join(g, "CLAUDE.md"), os.path.join(home, "CLAUDE.md"))
    for name in ("handoff.md", "multi-agent.md"):
        copy(os.path.join(g, "docs", name), os.path.join(home, "docs", name))
    copy(os.path.join(g, "hooks", "guard-git.py"), os.path.join(home, "hooks", "guard-git.py"), executable=True)
    merge_settings(os.path.join(g, "settings.json"), os.path.join(home, "settings.json"))


def install_project(path, guard):
    p = os.path.join(ROOT, "project")
    dst = os.path.join(path, "CLAUDE.md")
    if os.path.exists(dst):
        say(f"skip       {dst} exists (fill or merge it by hand, or use the skill)")
    else:
        copy(os.path.join(p, "CLAUDE.md"), dst)
    if guard:
        copy(os.path.join(ROOT, "global", "hooks", "guard-git.py"),
             os.path.join(path, ".claude", "hooks", "guard-git.py"), executable=True)
        merge_settings(os.path.join(p, "settings.project.json"),
                       os.path.join(path, ".claude", "settings.json"))


def main():
    global DRY
    ap = argparse.ArgumentParser()
    ap.add_argument("--global", dest="glob", action="store_true")
    ap.add_argument("--project")
    ap.add_argument("--guard", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    DRY = a.dry_run
    if not (a.glob or a.project):
        ap.print_help()
        return 1
    if a.glob:
        install_global()
    if a.project:
        install_project(os.path.abspath(a.project), a.guard)
    return 0


if __name__ == "__main__":
    sys.exit(main())
