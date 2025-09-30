#!/bin/bash

# Test API Direct - Script untuk test API endpoint
# Usage: bash test_api_direct.sh

echo "=========================================="
echo "TESTING BACKEND API ENDPOINTS"
echo "=========================================="

API_URL="https://api.aksesgptmurah.tech"
ORIGIN="https://aksesgptmurah.tech"

echo ""
echo "1. Testing Health Endpoint"
echo "------------------------------------------"
curl -s "${API_URL}/health" | jq '.' 2>/dev/null || curl -s "${API_URL}/health"
echo ""

echo ""
echo "2. Testing Packages Endpoint"
echo "------------------------------------------"
curl -s "${API_URL}/api/packages" | jq '.' 2>/dev/null || curl -s "${API_URL}/api/packages"
echo ""

echo ""
echo "3. Testing Create Order Endpoint (with valid email)"
echo "------------------------------------------"
echo "Request payload:"
cat <<EOF
{
  "customer_email": "testuser@gmail.com",
  "package_id": "chatgpt_plus_1_month",
  "full_name": "Test User",
  "phone_number": "+628123456789"
}
EOF

echo ""
echo "Response:"
curl -X POST "${API_URL}/api/orders" \
  -H "Content-Type: application/json" \
  -H "Origin: ${ORIGIN}" \
  -d '{
    "customer_email": "testuser@gmail.com",
    "package_id": "chatgpt_plus_1_month",
    "full_name": "Test User",
    "phone_number": "+628123456789"
  }' 2>&1 | jq '.' 2>/dev/null || curl -X POST "${API_URL}/api/orders" \
  -H "Content-Type: application/json" \
  -H "Origin: ${ORIGIN}" \
  -d '{
    "customer_email": "testuser@gmail.com",
    "package_id": "chatgpt_plus_1_month",
    "full_name": "Test User",
    "phone_number": "+628123456789"
  }' 2>&1

echo ""
echo ""
echo "=========================================="
echo "TEST COMPLETE"
echo "=========================================="
echo ""
echo "Expected Results:"
echo "  1. Health: Should return status 'healthy'"
echo "  2. Packages: Should return list of packages"
echo "  3. Create Order:"
echo "     - Success: Returns checkout_url, order_id, reference"
echo "     - Error: Returns error message with details"
echo ""
echo "Common Errors:"
echo "  - 'Internal server error': Backend config issue (DB, Tripay, etc)"
echo "  - 'Validation failed': Input data issue"
echo "  - 'Failed to fetch' (in browser): CORS/cache issue"
echo ""