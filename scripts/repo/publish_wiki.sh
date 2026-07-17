#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build/wiki}"
REPOSITORY="${GITHUB_REPOSITORY:-DylanLRPollock/Monkey-Head-Project}"
TOKEN="${WIKI_TOKEN:-${GH_TOKEN:-}}"
ACTOR="${GITHUB_ACTOR:-wiki-publisher}"

if [[ -z "$TOKEN" ]]; then
  echo "WIKI_TOKEN or GH_TOKEN is required to publish the GitHub Wiki." >&2
  exit 2
fi

python3 "$ROOT_DIR/scripts/repo/build_wiki.py" "$BUILD_DIR"

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
wiki_dir="$workdir/wiki"
remote="https://x-access-token:${TOKEN}@github.com/${REPOSITORY}.wiki.git"

if ! git clone "$remote" "$wiki_dir"; then
  echo "Could not clone ${REPOSITORY}.wiki.git." >&2
  echo "Initialize the GitHub Wiki with one page or verify token permissions." >&2
  exit 3
fi

find "$wiki_dir" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
find "$BUILD_DIR" -maxdepth 1 -type f -name '*.md' -exec cp {} "$wiki_dir"/ \;

cd "$wiki_dir"
git config user.name "$ACTOR"
git config user.email "${ACTOR}@users.noreply.github.com"
git add -A

if git diff --cached --quiet; then
  echo "GitHub Wiki is already synchronized."
  exit 0
fi

git commit -m "Publish v201.x wiki overhaul"
git push origin HEAD:master
