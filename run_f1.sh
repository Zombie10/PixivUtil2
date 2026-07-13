#!/bin/bash
# ==============================================
# Download FANBOX supporting list (option f1)
# Usage: ./run_f1.sh [END_PAGE]
#        END_PAGE=0 means no page limit
# ==============================================
set -u

END_PAGE=${1:-1}
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

LOG_FILE="run_f1.log"
STARTED_AT=$(date '+%Y-%m-%d %H:%M:%S')
EXIT_CODE=0

echo "Activating virtualenv..."
# shellcheck disable=SC1091
source env/bin/activate

echo "Started at: $STARTED_AT"
echo "Running PixivUtil2 -s f1 (end_page=$END_PAGE)"
echo "Log: $LOG_FILE"
echo "Tip: use --no-resume to ignore checkpoint_fanbox_supporting.json"

{
  echo "===== RUN START $STARTED_AT ====="
  python PixivUtil2.py -s f1 -x --ep="$END_PAGE"
  EXIT_CODE=$?
  echo "===== RUN END $(date '+%Y-%m-%d %H:%M:%S') exit=$EXIT_CODE ====="
} >> "$LOG_FILE" 2>&1

deactivate || true

if command -v osascript >/dev/null 2>&1; then
  if [ "$EXIT_CODE" -eq 0 ]; then
    osascript -e "display notification \"run_f1 finished OK\" with title \"PixivUtil2\"" || true
  else
    osascript -e "display notification \"run_f1 failed (exit $EXIT_CODE)\" with title \"PixivUtil2\"" || true
  fi
fi

echo ""
if [ "$EXIT_CODE" -eq 0 ]; then
  echo "✅ Finished OK. Log: $LOG_FILE"
else
  echo "❌ Finished with errors (exit $EXIT_CODE). Log: $LOG_FILE"
fi
exit "$EXIT_CODE"
