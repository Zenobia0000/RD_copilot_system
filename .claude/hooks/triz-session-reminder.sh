#!/usr/bin/env bash
# TRIZ Session Reminder Hook (UserPromptSubmit)
# Reads .triz-state.json and prints a session status reminder
# when the user's prompt does NOT start with /triz-*
#
# Output goes to stderr → injected as system context to Claude.
# Exit 0 always (non-blocking).

set -euo pipefail

STATE_FILE=".claude/context/triz/.triz-state.json"

# Skip if no active session
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

# Read user prompt from stdin (hook receives it via stdin)
USER_PROMPT=$(cat)

# Skip if user is already using a /triz command
if echo "$USER_PROMPT" | grep -qE '^\s*/triz'; then
  exit 0
fi

# Parse state file
SESSION_ID=$(python3 -c "import json,sys; d=json.load(open('$STATE_FILE')); print(d.get('session_id','unknown'))" 2>/dev/null || echo "unknown")
CURRENT_STEP=$(python3 -c "import json,sys; d=json.load(open('$STATE_FILE')); print(d.get('current_step','unknown'))" 2>/dev/null || echo "unknown")
PATH_TYPE=$(python3 -c "import json,sys; d=json.load(open('$STATE_FILE')); print(d.get('path','unknown'))" 2>/dev/null || echo "unknown")

# Check if session is already completed (all steps done)
ALL_DONE=$(python3 -c "
import json
d=json.load(open('$STATE_FILE'))
done = all(d.get(f'step{i}',{}).get('completed',False) for i in range(5))
print('yes' if done else 'no')
" 2>/dev/null || echo "no")

if [ "$ALL_DONE" = "yes" ]; then
  exit 0
fi

# Build step progress
PROGRESS=$(python3 -c "
import json
d=json.load(open('$STATE_FILE'))
steps = ['step0','step1','step2','step3','step4']
labels = ['Step 0: 問題定向','Step 1: 功能建模','Step 2: TC 定義','Step 3: PC/SF 解題','Step 4: 驗證']
for s,l in zip(steps,labels):
    done = d.get(s,{}).get('completed',False)
    mark = '✓' if done else '○'
    print(f'  {mark} {l}')
" 2>/dev/null || echo "  (無法讀取進度)")

# Map current_step to next command suggestion
NEXT_CMD=$(python3 -c "
import json
d=json.load(open('$STATE_FILE'))
step = d.get('current_step','')
m = {
  'step0': '/triz-scope',
  'step1': '/triz-model',
  'step2': '/triz-solve',
  'step3': '/triz-solve',
  'step4': '/triz-verify'
}
print(m.get(step, '/triz-status'))
" 2>/dev/null || echo "/triz-status")

# Output reminder to stderr
cat >&2 <<EOF
[TRIZ Session 提醒] Session: $SESSION_ID | 目前: $CURRENT_STEP | 路徑: $PATH_TYPE
$PROGRESS
→ 下一步建議: $NEXT_CMD
EOF

exit 0
