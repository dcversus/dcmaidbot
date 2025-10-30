#!/bin/bash
# Test PRP-017: Role-Based Access Control via /call endpoint
#
# This script manually tests RBAC for lesson management:
# - Admin can see lesson commands and use lesson tools
# - Non-admin sees no lesson information (security requirement)

set -e

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8080}"
SECRET="${NUDGE_SECRET:-test_secret_for_e2e}"
ADMIN_ID="${ADMIN_ID:-199572554}"
NON_ADMIN_ID="${NON_ADMIN_ID:-888888888}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🔒 PRP-017 RBAC Testing Script${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Configuration:"
echo "  Base URL: $BASE_URL"
echo "  Admin ID: $ADMIN_ID"
echo "  Non-Admin ID: $NON_ADMIN_ID"
echo ""

# Function to call bot
call_bot() {
    local user_id=$1
    local is_admin=$2
    local message=$3
    local command=$4

    local data="{\"user_id\": $user_id"

    if [ -n "$is_admin" ]; then
        data="$data, \"is_admin\": $is_admin"
    fi

    if [ -n "$message" ]; then
        data="$data, \"message\": \"$message\""
    fi

    if [ -n "$command" ]; then
        data="$data, \"command\": \"$command\""
    fi

    data="$data}"

    curl -s -X POST "$BASE_URL/call" \
        -H "Authorization: Bearer $SECRET" \
        -H "Content-Type: application/json" \
        -d "$data" | python3 -m json.tool
}

# Test 1: Admin /help
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Test 1: Admin /help (should show lesson tools)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
call_bot "$ADMIN_ID" "true" "" "/help"
echo ""
echo -e "${YELLOW}Expected: Response should mention lesson commands${NC}"
echo ""

# Test 2: Non-admin /help
echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
echo -e "${RED}❌ Test 2: Non-admin /help (should hide lesson tools)${NC}"
echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
call_bot "$NON_ADMIN_ID" "false" "" "/help"
echo ""
echo -e "${YELLOW}Expected: NO mention of lessons or admin features${NC}"
echo ""

# Test 3: Admin creates lesson
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Test 3: Admin creates lesson via natural language${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
call_bot "$ADMIN_ID" "true" "Save this as a lesson: Always use nya~ at the end" ""
echo ""
echo -e "${YELLOW}Expected: Confirmation of lesson creation${NC}"
echo ""

# Test 4: Non-admin tries to create lesson
echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
echo -e "${RED}❌ Test 4: Non-admin tries to create lesson (should get vague response)${NC}"
echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
call_bot "$NON_ADMIN_ID" "false" "Save this as a lesson: Test instruction" ""
echo ""
echo -e "${YELLOW}Expected: Vague deflection like 'I don't understand'${NC}"
echo -e "${YELLOW}Expected: NO explanation of what lessons are${NC}"
echo ""

# Test 5: Admin lists lessons
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Test 5: Admin lists all lessons${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
call_bot "$ADMIN_ID" "true" "Show me all my lessons" ""
echo ""
echo -e "${YELLOW}Expected: List of lessons or 'no lessons yet'${NC}"
echo ""

# Test 6: Non-admin tries to list lessons
echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
echo -e "${RED}❌ Test 6: Non-admin tries to list lessons (should get vague response)${NC}"
echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
call_bot "$NON_ADMIN_ID" "false" "Show me your lessons" ""
echo ""
echo -e "${YELLOW}Expected: Vague deflection, NO lesson information${NC}"
echo ""

# Test 7: Admin edits lesson
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Test 7: Admin edits a lesson${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
call_bot "$ADMIN_ID" "true" "Edit lesson #1 to say: New instruction here" ""
echo ""
echo -e "${YELLOW}Expected: Confirmation of lesson edit${NC}"
echo ""

# Test 8: Non-admin tries to edit lesson
echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
echo -e "${RED}❌ Test 8: Non-admin tries to edit lesson (should get vague response)${NC}"
echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
call_bot "$NON_ADMIN_ID" "false" "Edit lesson #1 to say: Different text" ""
echo ""
echo -e "${YELLOW}Expected: Vague deflection, NO lesson feature revealed${NC}"
echo ""

# Test 9: Admin deletes lesson
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Test 9: Admin deletes a lesson${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
call_bot "$ADMIN_ID" "true" "Delete lesson #1" ""
echo ""
echo -e "${YELLOW}Expected: Confirmation of lesson deletion${NC}"
echo ""

# Test 10: Non-admin tries to delete lesson
echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
echo -e "${RED}❌ Test 10: Non-admin tries to delete lesson (should get vague response)${NC}"
echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
call_bot "$NON_ADMIN_ID" "false" "Delete lesson #1" ""
echo ""
echo -e "${YELLOW}Expected: Vague deflection, NO permission error or feature explanation${NC}"
echo ""

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📊 RBAC Testing Complete${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Manual Verification Checklist:"
echo ""
echo -e "${GREEN}✅ Admin Tests (1, 3, 5, 7, 9):${NC}"
echo "   - Admin /help shows lesson commands"
echo "   - Admin can create, list, edit, delete lessons"
echo "   - Responses are helpful and positive"
echo ""
echo -e "${RED}❌ Non-Admin Tests (2, 4, 6, 8, 10):${NC}"
echo "   - Non-admin /help shows NO lesson information"
echo "   - Non-admin gets vague deflections (e.g., 'I don't understand')"
echo "   - NO explanation of what lessons are"
echo "   - NO 'permission denied' or 'admin only' messages"
echo "   - ZERO information leakage about lesson features"
echo ""
echo -e "${YELLOW}Security Requirement:${NC}"
echo "Non-admins should have NO way to discover that lessons exist!"
echo ""
