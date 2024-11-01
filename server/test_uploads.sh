#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Base URL
BASE_URL="http://localhost:5001"

echo -e "${GREEN}Testing Auth Endpoints${NC}"

# Test Login
echo -e "\nTesting login..."
login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@test.com",
        "password": "password123"
    }')
echo "Login Response: $login_response"

# Extract token (works with both old and new token system)
token=$(echo $login_response | jq -r '.token // .access_token')

if [ "$token" != "null" ] && [ "$token" != "" ]; then
    echo -e "\n${GREEN}Testing File Uploads${NC}"
    
    # Test single image upload
    echo -e "\nTesting single image upload..."
    curl -s -X POST "${BASE_URL}/api/storage/upload" \
        -H "Authorization: Bearer $token" \
        -F "files=@./test_images/test1.png" | jq '.'

    # Test multiple image upload
    echo -e "\nTesting multiple image upload..."
    curl -s -X POST "${BASE_URL}/api/storage/upload" \
        -H "Authorization: Bearer $token" \
        -F "files=@./test_images/test1.png" \
        -F "files=@./test_images/test2.png" | jq '.'

    # Test model creation
    echo -e "\nTesting model creation..."
    model_response=$(curl -s -X POST "${BASE_URL}/api/model/create" \
        -H "Authorization: Bearer $token" \
        -F "name=test_model" \
        -F "ageYears=25" \
        -F "files=@./test_images/test1.png")
    echo "Model Response:"
    echo $model_response | jq '.'

    # If you get a job ID, check its status
    job_id=$(echo $model_response | jq -r '.job_id')
    if [ "$job_id" != "null" ] && [ "$job_id" != "" ]; then
        echo -e "\nChecking job status..."
        curl -s -X GET "${BASE_URL}/api/model/job/$job_id/status" \
            -H "Authorization: Bearer $token" | jq '.'
    fi

    # List models
    echo -e "\nListing models..."
    curl -s -X GET "${BASE_URL}/api/model/list" \
        -H "Authorization: Bearer $token" | jq '.'

else
    echo -e "\n${RED}Failed to get token. Cannot test uploads.${NC}"
fi