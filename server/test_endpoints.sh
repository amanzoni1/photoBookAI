#!/bin/bash

# Save as test_endpoints.sh and make executable with: chmod +x test_endpoints.sh

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Base URL
BASE_URL="http://localhost:5001"

echo -e "${GREEN}Testing Auth Endpoints${NC}"

# Test Register
echo "Testing register..."
register_response=$(curl -X POST "${BASE_URL}/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@test.com",
        "username": "test",
        "password": "password123"
    }')
echo "Register Response: $register_response"

# Test Login
echo -e "\nTesting login..."
login_response=$(curl -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@test.com",
        "password": "password123"
    }')
echo "Login Response: $login_response"

# Extract token (requires jq - install with: brew install jq)
token=$(echo $login_response | jq -r '.token')
echo "Token: $token"

if [ "$token" != "null" ] && [ "$token" != "" ]; then
    echo -e "\n${GREEN}Testing Protected Endpoints${NC}"
    
    # Test User Profile
    echo -e "\nTesting get profile..."
    curl -X GET "${BASE_URL}/api/user/profile" \
        -H "Authorization: Bearer $token"
    
    # Test User Stats
    echo -e "\nTesting get stats..."
    curl -X GET "${BASE_URL}/api/user/stats" \
        -H "Authorization: Bearer $token"
    
    # Test Storage Status
    echo -e "\nTesting storage status..."
    curl -X GET "${BASE_URL}/api/storage/status" \
        -H "Authorization: Bearer $token"
    
    # Test Get Images
    echo -e "\nTesting get images..."
    curl -X GET "${BASE_URL}/api/storage/images" \
        -H "Authorization: Bearer $token"
    
    # Test List Models
    echo -e "\nTesting list models..."
    curl -X GET "${BASE_URL}/api/model/list" \
        -H "Authorization: Bearer $token"
else
    echo -e "\n${RED}Failed to get token. Skipping protected endpoints.${NC}"
fi