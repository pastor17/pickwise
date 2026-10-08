#!/usr/bin/env bash
# =============================================================
# PickWise — build + deploy to the branch GitHub Pages serves.
#
# Why this script exists:
#   The repo keeps Hugo source in src/ and the BUILT html at the
#   repo root. GitHub Pages serves the `main` branch (Jekyll is
#   disabled by .nojekyll). A naive `cp -r src/public/* .` never
#   deletes pages that were removed or renamed, which silently
#   leaves stale files and can 404 new ones. rsync --delete fixes
#   that while protecting the source files.
#
# Usage:  bash src/scripts/deploy.sh "commit message"
# =============================================================
set -euo pipefail

HUGO="${HUGO:-/Users/game-netease/Documents/dshworkspace/.tools/hugo}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MSG="${1:-Update site content}"

cd "$ROOT/src"
echo "▶ Building with Hugo…"
"$HUGO" --minify

cd "$ROOT"
echo "▶ Syncing build output to repo root (rsync --delete, source protected)…"
rsync -a --delete \
  --exclude='.git/' \
  --exclude='src/' \
  --exclude='.github/' \
  --exclude='.gitignore' \
  --exclude='.nojekyll' \
  --exclude='CNAME' \
  --exclude='README.md' \
  --exclude='deploy.sh' \
  src/public/ ./

rm -rf src/public src/resources src/.hugo_build.lock

# Sanity checks — fail loudly rather than deploying a broken site.
for f in index.html .nojekyll CNAME; do
  [[ -e "$f" ]] || { echo "✖ Missing required root file: $f" >&2; exit 1; }
done

echo "▶ Committing…"
git add -A
if git diff --cached --quiet; then
  echo "  (no changes to commit)"
else
  git commit -m "$MSG"
fi

echo "▶ Pushing master…"
git push origin master

echo "▶ Syncing main (the branch GitHub Pages actually serves)…"
git checkout main
git merge master -m "Sync: $MSG" || git merge master --no-edit
git push origin main
git checkout master

echo "✔ Done. GitHub Pages will rebuild main in ~1-2 min."
echo "  Verify: curl -sL https://pickwise.irudder.me/ | grep -oE '<title>[^<]*</title>'"
