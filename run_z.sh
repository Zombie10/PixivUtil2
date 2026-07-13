#!/bin/bash
# ==============================================
# Download bookmarked artists (option z)
# Usage: ./run_z.sh [BOOKMARK_PAGES] [DOWNLOAD_PAGES]
# ==============================================
set -u

BOOKMARK_PAGES=${1:-5}
DOWNLOAD_PAGES=${2:-4}
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

LOG_FILE="run_z.log"
STARTED_AT=$(date '+%Y-%m-%d %H:%M:%S')
EXIT_CODE=0

echo "Activating virtualenv..."
# shellcheck disable=SC1091
source env/bin/activate

echo "Started at: $STARTED_AT"
echo "Running PixivUtil2 -s z (bookmark pages=$BOOKMARK_PAGES, artist pages=1-$DOWNLOAD_PAGES)"
echo "Log: $LOG_FILE"

{
  echo "===== RUN START $STARTED_AT ====="
  python PixivUtil2.py -s z -x --b="$BOOKMARK_PAGES" --sp=1 --ep="$DOWNLOAD_PAGES"
  EXIT_CODE=$?
  echo "===== RUN END $(date '+%Y-%m-%d %H:%M:%S') exit=$EXIT_CODE ====="
} >> "$LOG_FILE" 2>&1

deactivate || true

if command -v osascript >/dev/null 2>&1; then
  if [ "$EXIT_CODE" -eq 0 ]; then
    osascript -e "display notification \"run_z finished OK\" with title \"PixivUtil2\"" || true
  else
    osascript -e "display notification \"run_z failed (exit $EXIT_CODE)\" with title \"PixivUtil2\"" || true
  fi
fi

echo ""
if [ "$EXIT_CODE" -eq 0 ]; then
  echo "✅ Finished OK. Log: $LOG_FILE"
else
  echo "❌ Finished with errors (exit $EXIT_CODE). Log: $LOG_FILE"
fi
exit "$EXIT_CODE"
