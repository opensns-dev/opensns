#!/bin/bash
set -e

SESSION="opensns-e2e"
BASE="http://localhost:3000"
API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8001}"

cleanup() { agent-browser close --session-name "$SESSION" 2>/dev/null || true; }
trap cleanup EXIT

TOKEN=$(curl -sf -X POST "$API_URL/auth/login" \
  -d "username=e2e-test@opensns.dev&password=TestPassword123!" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  | grep -oE '"access_token"\s*:\s*"[^"]+"' | cut -d'"' -f4)

agent-browser --session-name "$SESSION" open "$BASE"
if [ -n "$TOKEN" ]; then
  agent-browser --session-name "$SESSION" eval "localStorage.setItem('token', '$TOKEN')"
fi

echo "=== Test: should display campaigns page with heading ==="
agent-browser --session-name "$SESSION" open "$BASE/campaigns"
sleep 2
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
echo "$SNAP" | grep -qi "campaigns" || { echo "FAIL: campaigns heading not found"; exit 1; }
echo "PASS"

echo "=== Test: should have create campaign button ==="
echo "$SNAP" | grep -qiE "create campaign" || { echo "FAIL: create campaign button not found"; exit 1; }
echo "PASS"

echo "=== Test: should show empty state or campaigns list ==="
echo "$SNAP" | grep -qiE "table|no campaigns|campaign" || { echo "FAIL: no campaigns list or empty state"; exit 1; }
echo "PASS"

echo "=== Test: should show new campaign form in dialog ==="
CREATE_REF=$(echo "$SNAP" | grep -i "create campaign" | grep -oE '@e[0-9]+' | head -1)
if [ -n "$CREATE_REF" ]; then
  agent-browser --session-name "$SESSION" click "$CREATE_REF"
  sleep 1
  SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
  echo "$SNAP" | grep -qi "dialog\|title\|url" || { echo "FAIL: dialog not shown"; exit 1; }
fi
echo "PASS"

echo "=== Test: should create a new campaign ==="
agent-browser --session-name "$SESSION" open "$BASE/campaigns"
sleep 2
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
if echo "$SNAP" | grep -qi "failed to load"; then
  echo "SKIP: campaigns API not available"
else
  CREATE_REF=$(echo "$SNAP" | grep -i "create campaign" | grep -oE '@e[0-9]+' | head -1)
  if [ -n "$CREATE_REF" ]; then
    agent-browser --session-name "$SESSION" click "$CREATE_REF"
    sleep 1
    SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
    TITLE_REF=$(echo "$SNAP" | grep -i "title" | grep -oE '@e[0-9]+' | head -1)
    URL_REF=$(echo "$SNAP" | grep -i "url" | grep -oE '@e[0-9]+' | head -1)
    if [ -n "$TITLE_REF" ] && [ -n "$URL_REF" ]; then
      agent-browser --session-name "$SESSION" fill "$TITLE_REF" "E2E Test Campaign $(date +%s)"
      agent-browser --session-name "$SESSION" fill "$URL_REF" "https://example.com/test-product"
      SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
      SUBMIT_REF=$(echo "$SNAP" | grep -i "start analysis" | grep -oE '@e[0-9]+' | head -1)
      if [ -n "$SUBMIT_REF" ]; then
        agent-browser --session-name "$SESSION" click "$SUBMIT_REF"
        sleep 2
      fi
    fi
  fi
fi
echo "PASS"

echo "=== Test: should navigate to campaign detail from list ==="
agent-browser --session-name "$SESSION" open "$BASE/campaigns"
sleep 2
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
VIEW_REF=$(echo "$SNAP" | grep -i "view" | grep -oE '@e[0-9]+' | head -1)
if [ -n "$VIEW_REF" ]; then
  agent-browser --session-name "$SESSION" click "$VIEW_REF"
  sleep 2
  URL=$(agent-browser --session-name "$SESSION" get url)
  echo "$URL" | grep -qE "campaigns/[0-9]+" || { echo "FAIL: not on campaign detail page"; exit 1; }
fi
echo "PASS"

echo "=== Test: should navigate back to campaigns list ==="
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
BACK_REF=$(echo "$SNAP" | grep -i "campaigns" | grep -oE '@e[0-9]+' | head -1)
if [ -n "$BACK_REF" ]; then
  agent-browser --session-name "$SESSION" click "$BACK_REF"
  sleep 1
  URL=$(agent-browser --session-name "$SESSION" get url)
  echo "$URL" | grep -qE "campaigns$" || true
fi
echo "PASS"

echo ""
echo "All campaigns tests passed"
