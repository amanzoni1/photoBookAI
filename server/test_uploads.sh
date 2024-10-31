#!/bin/bash

# Save as test_uploads.sh and make executable with: chmod +x test_uploads.sh

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Base URL
BASE_URL="http://localhost:5001"

# First get token
echo "Getting authentication token..."
login_response=$(curl -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@test.com",
        "password": "password123"
    }')

token=$(echo $login_response | jq -r '.token')

if [ "$token" != "null" ] && [ "$token" != "" ]; then
    echo -e "\n${GREEN}Testing File Uploads${NC}"
    
    # Test image upload (replace with actual image path)
    echo -e "\nTesting single image upload..."
    curl -X POST "${BASE_URL}/api/storage/upload" \
        -H "Authorization: Bearer $token" \
        -F "files=@./test_images/test1.png"
    
    # Test multiple image upload
    echo -e "\nTesting multiple image upload..."
    curl -X POST "${BASE_URL}/api/storage/upload" \
        -H "Authorization: Bearer $token" \
        -F "files=@./test_images/test1.png" \
        -F "files=@./test_images/test2.png"
    
    # Test model creation with images
    echo -e "\nTesting model creation with images..."
    curl -X POST "${BASE_URL}/api/model/create" \
        -H "Authorization: Bearer $token" \
        -F "name=test_model" \
        -F "ageYears=25" \
        -F "files=@./test_images/test1.png" \
        -F "files=@./test_images/test2.png"
else
    echo -e "\n${RED}Failed to get token. Cannot test uploads.${NC}"
fi