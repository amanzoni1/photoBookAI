#!/bin/bash

# Save as test_credits.sh
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Base URL
BASE_URL="http://localhost:5001"

echo -e "${GREEN}Testing Credit Endpoints${NC}"

# Get auth token
echo "Getting authentication token..."
login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@test.com",
        "password": "password123"
    }')

token=$(echo $login_response | jq -r '.token')

if [ "$token" != "null" ] && [ "$token" != "" ]; then
    echo -e "${GREEN}Testing Credit Balance${NC}"
    curl -s -X GET "${BASE_URL}/api/credits/balance" \
        -H "Authorization: Bearer $token" | jq '.'

    echo -e "\n${GREEN}Testing Credit Packages - All${NC}"
    curl -s -X GET "${BASE_URL}/api/credits/packages" | jq '.'

    echo -e "\n${GREEN}Testing Credit Packages - Model Training${NC}"
    curl -s -X GET "${BASE_URL}/api/credits/packages?type=MODEL_TRAINING" | jq '.'

    echo -e "\n${GREEN}Testing Credit Packages - Single Image${NC}"
    curl -s -X GET "${BASE_URL}/api/credits/packages?type=SINGLE_IMAGE" | jq '.'

    echo -e "\n${GREEN}Testing Credit Packages - Photobook${NC}"
    curl -s -X GET "${BASE_URL}/api/credits/packages?type=PHOTOBOOK" | jq '.'

    echo -e "\n${GREEN}Testing Credit Purchase${NC}"
    curl -s -X POST "${BASE_URL}/api/credits/purchase" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d '{
            "credit_type": "MODEL_TRAINING",
            "amount": 1,
            "payment_id": "test_payment_123",
            "price": 9.99
        }' | jq '.'

    echo -e "\n${GREEN}Verifying Updated Balance${NC}"
    curl -s -X GET "${BASE_URL}/api/credits/balance" \
        -H "Authorization: Bearer $token" | jq '.'
else
    echo -e "\n${RED}Failed to get token. Cannot test credit endpoints.${NC}"
fi