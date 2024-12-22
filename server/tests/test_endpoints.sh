#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Base URL
BASE_URL="http://localhost:5001"

echo -e "${GREEN}Testing Auth and Jobs System${NC}"

# Get authentication token
echo "Getting authentication token..."
login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@test.com",
        "password": "password123"
    }')

echo "Login response: $login_response"

# Extract tokens
access_token=$(echo $login_response | jq -r '.access_token')
refresh_token=$(echo $login_response | jq -r '.refresh_token')

if [ "$access_token" != "null" ] && [ "$access_token" != "" ]; then
    echo -e "\n${GREEN}Authentication successful${NC}"
    echo "Access Token: ${access_token:0:50}..."
    echo "Refresh Token: ${refresh_token:0:50}..."

    echo -e "\n${GREEN}Testing File Uploads${NC}"
    
    # Test single image upload
    echo -e "\nTesting single image upload..."
    upload_response=$(curl -s -X POST "${BASE_URL}/api/storage/upload" \
        -H "Authorization: Bearer $access_token" \
        -F "files=@./test_images/test1.png")
    echo "Upload response: $upload_response"
    
    # Test multiple image upload
    echo -e "\n${GREEN}Testing multiple image upload...${NC}"
    multi_upload_response=$(curl -s -X POST "${BASE_URL}/api/storage/upload" \
        -H "Authorization: Bearer $access_token" \
        -F "files=@./test_images/test1.png" \
        -F "files=@./test_images/test2.png")
    echo "Multiple upload response: $multi_upload_response"
    
    # Test model creation with images
    echo -e "\n${GREEN}Testing model creation with images...${NC}"
    model_response=$(curl -s -X POST "${BASE_URL}/api/model/create" \
        -H "Authorization: Bearer $access_token" \
        -F "name=test_model" \
        -F "ageYears=25" \
        -F "files=@./test_images/test1.png" \
        -F "files=@./test_images/test2.png")
    echo "Model creation response: $model_response"
    
    # Extract job ID from model creation response
    job_id=$(echo $model_response | jq -r '.job_id')
    
    if [ "$job_id" != "null" ] && [ "$job_id" != "" ]; then
        # Test job status
        echo -e "\n${GREEN}Testing job status...${NC}"
        for i in {1..5}; do
            echo -e "\nChecking job status (attempt $i)..."
            status_response=$(curl -s -X GET "${BASE_URL}/api/model/job/$job_id/status" \
                -H "Authorization: Bearer $access_token")
            echo "Job status: $status_response"
            
            # Check if job is completed
            job_status=$(echo $status_response | jq -r '.status')
            if [ "$job_status" = "COMPLETED" ]; then
                echo -e "\n${GREEN}Job completed successfully!${NC}"
                break
            elif [ "$job_status" = "FAILED" ]; then
                echo -e "\n${RED}Job failed!${NC}"
                break
            fi
            
            # Wait before next check
            sleep 2
        done
    else
        echo -e "\n${RED}Failed to get job ID from model creation response${NC}"
    fi
    
    # Test token refresh
    echo -e "\n${GREEN}Testing token refresh...${NC}"
    refresh_response=$(curl -s -X POST "${BASE_URL}/api/auth/refresh" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"$refresh_token\"
        }")
    echo "Refresh response: $refresh_response"
    
else
    echo -e "\n${RED}Failed to get tokens. Cannot proceed with tests.${NC}"
fi