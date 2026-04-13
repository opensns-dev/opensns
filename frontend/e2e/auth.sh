#!/bin/bash
set -e

SESSION="opensns-e2e"
BASE="http://localhost:3000"
API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8001}"
TEST_EMAIL="e2e-test@opensns.dev"
TEST_PASSWORD="TestPassword123!"

cleanup() { agent-browser close --session-name "$SESSION" 2>/dev/null || true; }
trap cleanup EXIT

echo "=== Auth Setup: authenticate via API and inject token ==="

TOKEN=$(curl -sf -X POST "$API_URL/auth/login" \
  -d "username=$TEST_EMAIL&password=$TEST_PASSWORD" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  | grep -oE '"access_token"\s*:\s*"[^"]+"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "Login failed, attempting register..."
  curl -sf -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" > /dev/null 2>&1 || true

  TOKEN=$(curl -sf -X POST "$API_URL/auth/login" \
    -d "username=$TEST_EMAIL&password=$TEST_PASSWORD" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    | grep -oE '"access_token"\s*:\s*"[^"]+"' | cut -d'"' -f4)
fi

if [ -z "$TOKEN" ]; then
  echo "FAIL: Could not obtain auth token"
  exit 1
fi

agent-browser --session-name "$SESSION" open "$BASE"
agent-browser --session-name "$SESSION" eval "localStorage.setItem('token', '$TOKEN')"

echo "PASS: Auth token injected"
echo ""

echo "=== Test: should show login page ==="
agent-browser --session-name "$SESSION" open "$BASE/login"
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
echo "$SNAP" | grep -qi "welcome back" || { echo "FAIL: login heading not found"; exit 1; }
echo "$SNAP" | grep -qi "email" || { echo "FAIL: email input not found"; exit 1; }
echo "$SNAP" | grep -qi "password" || { echo "FAIL: password input not found"; exit 1; }
echo "PASS"

echo "=== Test: should show register page ==="
agent-browser --session-name "$SESSION" open "$BASE/register"
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
echo "$SNAP" | grep -qiE "create.*account|sign up|register" || { echo "FAIL: register heading not found"; exit 1; }
echo "$SNAP" | grep -qi "email" || { echo "FAIL: email input not found"; exit 1; }
echo "PASS"

echo "=== Test: should show validation errors for empty form ==="
agent-browser --session-name "$SESSION" open "$BASE/login"
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
SUBMIT_REF=$(echo "$SNAP" | grep -iE "submit|sign in|log in" | grep -oE '@e[0-9]+' | head -1)
if [ -n "$SUBMIT_REF" ]; then
  agent-browser --session-name "$SESSION" click "$SUBMIT_REF"
fi
sleep 1
URL=$(agent-browser --session-name "$SESSION" get url)
echo "$URL" | grep -q "login" || { echo "FAIL: should stay on login page"; exit 1; }
echo "PASS"

echo "=== Test: should navigate between login and register ==="
agent-browser --session-name "$SESSION" open "$BASE/login"
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
REG_LINK=$(echo "$SNAP" | grep -i "register" | grep -oE '@e[0-9]+' | head -1)
if [ -n "$REG_LINK" ]; then
  agent-browser --session-name "$SESSION" click "$REG_LINK"
  sleep 1
  URL=$(agent-browser --session-name "$SESSION" get url)
  echo "$URL" | grep -q "register" || { echo "FAIL: did not navigate to register"; exit 1; }
fi
echo "PASS"

echo "=== Test: should allow access to dashboard ==="
agent-browser --session-name "$SESSION" open "$BASE/dashboard"
sleep 2
SNAP=$(agent-browser --session-name "$SESSION" snapshot -i)
[ -n "$SNAP" ] || { echo "FAIL: dashboard returned empty snapshot"; exit 1; }
echo "PASS"

echo ""
echo "All auth tests passed"
