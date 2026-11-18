#!/bin/sh
# Usage: tests/smoke.sh <python version, e.g. 3.3>
# Runs tests/smoke.py in the python:<version> Docker image against the package as Package Control would download it
# (git archive: export-ignore applied), including uncommitted changes to tracked files.
set -e
cd "$(dirname "$0")/.."
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/Packages/LiveReload" "$work/Packages/User"
ref=$(git stash create)
git archive "${ref:-HEAD}" | tar -x -C "$work/Packages/LiveReload"
# no .pyc: the container runs as root, and root-owned __pycache__ folders would make the cleanup fail on Linux
docker run --rm -e ST_PACKAGES=/st/Packages -e PYTHONPATH=/tests/stubs -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$work:/st" -v "$PWD/tests:/tests:ro" "python:$1" python -u /tests/smoke.py
