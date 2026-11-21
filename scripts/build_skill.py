#!/usr/bin/env python3
"""Rebuild skill/SKILL.md from skill/SKILL.template.md by embedding the files in global/ and project/.

Run after editing anything in global/ or project/:  python3 scripts/build_skill.py
Then save the new skill/SKILL.md to your account (ask Claude to update the boilerplate-setup skill).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    template = open(os.path.join(ROOT, "skill", "SKILL.template.md")).read()

    def embed(match):
        path = os.path.join(ROOT, match.group(1))
        content = open(path).read().rstrip("\n")
        if "````" in content:
            sys.exit(f"{match.group(1)} contains a 4-backtick fence; it cannot be embedded")
        return content

    out = re.sub(r"\{\{file:([^}]+)\}\}", embed, template)
    dst = os.path.join(ROOT, "skill", "SKILL.md")
    with open(dst, "w") as f:
        f.write(out)
    print(f"wrote {dst} ({out.count(chr(10)) + 1} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
