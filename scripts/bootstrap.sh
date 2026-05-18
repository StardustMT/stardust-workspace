#!/usr/bin/env bash
# Clone all Stardust sibling repos into the workspace.
# Idempotent — skips repos that already exist locally.

set -euo pipefail

ORG="StardustMT"

REPOS=(
    "stardust-pit"
    "stardust-core"
    "stardustmt.github.io"
)

cd "$(dirname "$0")/.."

for repo in "${REPOS[@]}"; do
    if [ -d "$repo/.git" ]; then
        echo "✓ $repo already cloned"
        continue
    fi
    echo "→ cloning $ORG/$repo"
    git clone "git@github.com:$ORG/$repo.git" "$repo"
done

echo ""
echo "Done. Run \`just status\` to verify."
