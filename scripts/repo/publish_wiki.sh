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

# Publish only specifically reviewed pages. Never delete unrelated wiki pages.
# Example: WIKI_PUBLISH_PAGES=Home,Architecture
PUBLISH_PAGES="${WIKI_PUBLISH_PAGES:-}"
if [[ -z "$PUBLISH_PAGES" ]]; then
  echo "WIKI_PUBLISH_PAGES must explicitly name reviewed pages; refusing full wiki replacement." >&2
  exit 4
fi
IFS=',' read -r -a pages <<< "$PUBLISH_PAGES"
published_files=()
for page in "${pages[@]}"; do
  if [[ ! "$page" =~ ^[A-Za-z0-9_-]+$ ]]; then
    echo "Invalid wiki page name: $page" >&2
    exit 4
  fi
  if [[ ! -f "$BUILD_DIR/$page.md" ]]; then
    echo "Missing generated wiki page: $page.md" >&2
    exit 4
  fi
  cp -- "$BUILD_DIR/$page.md" "$wiki_dir/$page.md"
  published_files+=("$page.md")
done

cd "$wiki_dir"
git config user.name "$ACTOR"
git config user.email "${ACTOR}@users.noreply.github.com"
git add -- "${published_files[@]}"

if git diff --cached --quiet; then
  echo "GitHub Wiki is already synchronized."
  exit 0
fi

git commit -m "Publish reviewed HueyOS wiki pages"
git push origin HEAD:master
