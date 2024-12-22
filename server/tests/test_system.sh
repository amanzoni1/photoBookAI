#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

BASE_URL="http://localhost:5001"

echo -e "${GREEN}Running Complete System Test${NC}"

# 1. Test Auth
echo -e "\n${GREEN}1. Testing Authentication${NC}"
register_response=$(curl -s -X POST "${BASE_URL}/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "systemtest@test.com",
        "username": "systemtest",
        "password": "password123"
    }')
echo "Register Response: $register_response"

login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "systemtest@test.com",
        "password": "password123"
    }')
echo "Login Response: $login_response"

token=$(echo $login_response | jq -r '.token')

if [ "$token" != "null" ] && [ "$token" != "" ]; then
    # 2. Test Credits
    echo -e "\n${GREEN}2. Testing Credits System${NC}"
    
    echo "Initial Balance:"
    curl -s -X GET "${BASE_URL}/api/credits/balance" \
        -H "Authorization: Bearer $token" | jq '.'
    
    echo -e "\nPurchasing Credits:"
    curl -s -X POST "${BASE_URL}/api/credits/purchase" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d '{
            "credit_type": "MODEL_TRAINING",
            "amount": 1,
            "payment_id": "test_payment_123",
            "price": 9.99
        }' | jq '.'

    # 3. Test Storage
    echo -e "\n${GREEN}3. Testing Storage System${NC}"
    
    # Create test image
    convert -size 100x100 xc:white PNG:test_image.png
    
    echo "Uploading Image:"
    curl -s -X POST "${BASE_URL}/api/storage/upload" \
        -H "Authorization: Bearer $token" \
        -F "files=@test_image.png" \
        -F "quality=high" | jq '.'
    
    echo -e "\nListing Images:"
    curl -s -X GET "${BASE_URL}/api/storage/images" \
        -H "Authorization: Bearer $token" | jq '.'
    
    # 4. Test Model Creation
    echo -e "\n${GREEN}4. Testing Model System${NC}"
    
    echo "Creating Model:"
    curl -s -X POST "${BASE_URL}/api/model/create" \
        -H "Authorization: Bearer $token" \
        -F "name=test_model" \
        -F "ageYears=25" \
        -F "files=@test_image.png" | jq '.'
    
    echo -e "\nListing Models:"
    curl -s -X GET "${BASE_URL}/api/model/list" \
        -H "Authorization: Bearer $token" | jq '.'
    
    # 5. Test Storage Status
    echo -e "\n${GREEN}5. Testing Storage Status${NC}"
    curl -s -X GET "${BASE_URL}/api/storage/status" \
        -H "Authorization: Bearer $token" | jq '.'
    
    # Cleanup
    rm -f test_image.png
    
else
    echo -e "\n${RED}Authentication failed. Skipping remaining tests.${NC}"
fi