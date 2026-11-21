#!/usr/bin/env bash
# Fixture paths that remote tools refuse to write (Makefile, .github, .claude) are stored with a
# leading underscore and renamed here.
set -eu
cp -R "$(dirname "$0")/files/." .
[ -e repo/_Makefile ] && mv repo/_Makefile repo/Makefile
[ -e repo/_github ] && mv repo/_github repo/.github
[ -e home/_claude ] && mv home/_claude home/.claude
exit 0
