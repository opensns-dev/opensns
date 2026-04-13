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

echo "=== Test: should display settings page with header ==="
agent-browser --session-name "$SESSION" open "$BASE/settings"
sleep 2
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
echo "$SNAP" | grep -qi "settings" || { echo "FAIL: settings heading not found"; exit 1; }
echo "PASS"

echo "=== Test: should have theme toggle options ==="
echo "$SNAP" | grep -qi "light" || { echo "FAIL: light button not found"; exit 1; }
echo "$SNAP" | grep -qi "dark" || { echo "FAIL: dark button not found"; exit 1; }
echo "$SNAP" | grep -qi "system" || { echo "FAIL: system button not found"; exit 1; }
echo "PASS"

echo "=== Test: should toggle to dark mode ==="
DARK_REF=$(echo "$SNAP" | grep -i "dark" | grep -oE '@e[0-9]+' | head -1)
if [ -n "$DARK_REF" ]; then
  agent-browser --session-name "$SESSION" click "$DARK_REF"
  sleep 1
  HTML_CLASS=$(agent-browser --session-name "$SESSION" eval "document.documentElement.className")
  echo "$HTML_CLASS" | grep -q "dark" || { echo "FAIL: dark class not applied"; exit 1; }
fi
echo "PASS"

echo "=== Test: should toggle to light mode ==="
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
LIGHT_REF=$(echo "$SNAP" | grep -i "light" | grep -oE '@e[0-9]+' | head -1)
if [ -n "$LIGHT_REF" ]; then
  agent-browser --session-name "$SESSION" click "$LIGHT_REF"
  sleep 1
  HTML_CLASS=$(agent-browser --session-name "$SESSION" eval "document.documentElement.className")
  echo "$HTML_CLASS" | grep -qv "dark" || { echo "FAIL: dark class still present"; exit 1; }
fi
echo "PASS"

echo "=== Test: should have API key configuration section ==="
agent-browser --session-name "$SESSION" open "$BASE/settings"
sleep 2
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
echo "$SNAP" | grep -qiE "openai.*api.*key|api.*key" || { echo "FAIL: OpenAI API key field not found"; exit 1; }
echo "PASS"

echo "=== Test: should have save button ==="
echo "$SNAP" | grep -qi "save settings" || { echo "FAIL: save settings button not found"; exit 1; }
echo "PASS"

echo "=== Test: should display dashboard with heading ==="
agent-browser --session-name "$SESSION" open "$BASE/dashboard"
sleep 2
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
[ -n "$SNAP" ] || { echo "FAIL: dashboard empty"; exit 1; }
echo "PASS"

echo "=== Test: should have navigation to campaigns ==="
echo "$SNAP" | grep -qi "campaigns" || { echo "FAIL: campaigns link not found"; exit 1; }
echo "PASS"

echo "=== Test: should have quick action buttons ==="
echo "$SNAP" | grep -qi "New Campaign" || { echo "FAIL: New Campaign link not found"; exit 1; }
echo "PASS"

echo "=== Test: should display stats cards ==="
echo "$SNAP" | grep -qi "total campaigns" || { echo "FAIL: total campaigns stat not found"; exit 1; }
echo "PASS"

echo ""
echo "All settings & dashboard tests passed"
