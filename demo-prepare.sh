#!/bin/bash

# ============================================
#  Duiodle — Demo Preparation Script
# ============================================

CANISTER_ID="bk36a-naaaa-aaaah-asmaa-cai"
NETWORK="ic"
CYCLES_THRESHOLD=1000000000000  # 1 Trillion

# ANSI color codes
RED="\033[0;31m"
YELLOW="\033[1;33m"
GREEN="\033[0;32m"
BOLD_GREEN="\033[1;32m"
RESET="\033[0m"
BOLD="\033[1m"

echo ""
echo -e "${BOLD}========================================${RESET}"
echo -e "${BOLD}   Duiodle — Demo Preparation Checklist${RESET}"
echo -e "${BOLD}========================================${RESET}"
echo ""

# ── Step 1: Start canister ──────────────────
echo -e "${BOLD}[1/3] Starting canister...${RESET}"
START_OUTPUT=$(dfx canister start "$CANISTER_ID" --network "$NETWORK" 2>&1)
START_EXIT=$?

# A "already running" message is not an error
if echo "$START_OUTPUT" | grep -qi "already running"; then
  echo -e "    ${GREEN}✓ Canister was already running.${RESET}"
elif [ $START_EXIT -eq 0 ]; then
  echo -e "    ${GREEN}✓ Canister started successfully.${RESET}"
else
  echo -e "    ${YELLOW}⚠ Start command returned: $START_OUTPUT${RESET}"
  echo -e "    ${YELLOW}  (This may be fine if it was already running — continuing...)${RESET}"
fi
echo ""

# ── Step 2: Get canister status ─────────────
echo -e "${BOLD}[2/3] Checking canister status and balance...${RESET}"
STATUS_OUTPUT=$(dfx canister status "$CANISTER_ID" --network "$NETWORK" 2>&1)

if [ $? -ne 0 ]; then
  echo -e "${RED}✗ ERROR: Could not reach canister $CANISTER_ID${RESET}"
  echo -e "${RED}  Make sure your dfx identity is a controller of this canister.${RESET}"
  echo -e "  Verify controllers: dfx canister info $CANISTER_ID --network ic"
  exit 1
fi

# Extract Status
STATUS=$(echo "$STATUS_OUTPUT" | grep -i "^Status:" | awk -F': ' '{print $2}' | xargs)
if [ -z "$STATUS" ]; then
  STATUS=$(echo "$STATUS_OUTPUT" | grep -i "status" | head -1 | awk -F': ' '{print $2}' | xargs)
fi

# Extract Balance / Cycles
CYCLES_LINE=$(echo "$STATUS_OUTPUT" | grep -i "balance")
CYCLES_RAW=$(echo "$CYCLES_LINE" | grep -oE '[0-9_]+' | head -1 | tr -d '_')

echo "    Status  : $STATUS"
echo "    Balance : $CYCLES_LINE"
echo ""

# ── Step 3: Evaluate results ─────────────────
echo -e "${BOLD}[3/3] Evaluating...${RESET}"
HAS_ISSUE=0

# Check status is Running
if [ "$STATUS" != "Running" ]; then
  echo -e "${RED}"
  echo "  ╔══════════════════════════════════════════════╗"
  echo "  ║  ✗ ERROR: Canister is NOT running!          ║"
  echo "  ║  Status reported: $STATUS"
  echo "  ║  Run manually:                               ║"
  echo "  ║  dfx canister start $CANISTER_ID --network ic ║"
  echo "  ╚══════════════════════════════════════════════╝"
  echo -e "${RESET}"
  HAS_ISSUE=1
else
  echo -e "    ${GREEN}✓ Status is Running.${RESET}"
fi

# Check cycles balance
if [ -n "$CYCLES_RAW" ]; then
  if [ "$CYCLES_RAW" -lt "$CYCLES_THRESHOLD" ]; then
    echo -e "${YELLOW}"
    echo "  ╔══════════════════════════════════════════════════╗"
    echo "  ║  ⚠ WARNING: Cycles below 1 Trillion!           ║"
    echo "  ║  Current: $CYCLES_RAW cycles"
    echo "  ║  The canister may stop mid-demo if not topped up. ║"
    echo "  ║  Top up: dfx cycles top-up $CANISTER_ID <amt> --network ic ║"
    echo "  ╚══════════════════════════════════════════════════╝"
    echo -e "${RESET}"
    HAS_ISSUE=1
  else
    echo -e "    ${GREEN}✓ Cycles balance is sufficient.${RESET}"
  fi
else
  echo -e "    ${YELLOW}⚠ Could not parse cycles balance. Review output above manually.${RESET}"
fi

echo ""
echo -e "${BOLD}========================================${RESET}"

# ── Final verdict ─────────────────────────────
if [ $HAS_ISSUE -eq 0 ]; then
  echo -e "${BOLD_GREEN}"
  echo "  ██████╗ ███████╗ █████╗ ██████╗ ██╗   ██╗"
  echo "  ██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝"
  echo "  ██████╔╝█████╗  ███████║██║  ██║ ╚████╔╝ "
  echo "  ██╔══██╗██╔══╝  ██╔══██║██║  ██║  ╚██╔╝  "
  echo "  ██║  ██║███████╗██║  ██║██████╔╝   ██║   "
  echo "  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝   "
  echo ""
  echo "  ███████╗ ██████╗ ██████╗     ██████╗ ███████╗███╗   ███╗ ██████╗ ██╗"
  echo "  ██╔════╝██╔═══██╗██╔══██╗    ██╔══██╗██╔════╝████╗ ████║██╔═══██╗██║"
  echo "  █████╗  ██║   ██║██████╔╝    ██║  ██║█████╗  ██╔████╔██║██║   ██║██║"
  echo "  ██╔══╝  ██║   ██║██╔══██╗    ██║  ██║██╔══╝  ██║╚██╔╝██║██║   ██║╚═╝"
  echo "  ██║     ╚██████╔╝██║  ██║    ██████╔╝███████╗██║ ╚═╝ ██║╚██████╔╝██╗"
  echo "  ╚═╝      ╚═════╝ ╚═╝  ╚═╝    ╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝"
  echo -e "${RESET}"
else
  echo -e "${RED}  ✗ One or more checks failed. Fix the issues above before your demo.${RESET}"
  echo ""
  exit 1
fi

echo ""
