#!/usr/bin/env bash
# Pull latest on every sibling git repo in the workspace.
# Skips repos with uncommitted changes (reports them instead).

set -uo pipefail

cd "$(dirname "$0")/.."

for d in */; do
    [ -d "$d.git" ] || continue
    printf "\n=== %s ===\n" "$d"
    (
        cd "$d" || exit 1
        if [ -n "$(git status --porcelain)" ]; then
            echo "  ! uncommitted changes — skipping pull"
            git -c color.status=always status --short
        else
            git pull --ff-only
        fi
    )
done

echo ""
echo "Done."
