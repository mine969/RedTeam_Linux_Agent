#!/bin/bash
# Auto-sync script for DRL-Agent-vul
# Usage: ./git_sync.sh "your commit message"

set -e  # Exit on error

echo "🔄 Starting Git sync..."

# 1. Add all changes
git add -A
echo "✅ Staged all changes"

# 2. Commit with message
if [ -z "$1" ]; then
    # No message provided, use default
    COMMIT_MSG="chore: Auto-sync $(date '+%Y-%m-%d %H:%M')"
else
    COMMIT_MSG="$1"
fi

git commit -m "$COMMIT_MSG" || echo "⚠️  No changes to commit"

# 3. Pull with rebase (handles diverged branches)
echo "📥 Pulling latest changes..."
git pull --rebase origin master

# 4. Push
echo "📤 Pushing to GitHub..."
git push origin master

echo "✅ Sync complete!"
