#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Base URL
BASE_URL="http://localhost:5001"

echo -e "${GREEN}Testing Photobook Generation System${NC}"

# Get authentication token
echo "Getting authentication token..."
login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "a.manzoni1@proton.me",
        "password": "12345"
    }')

echo "Login response: $login_response"

# Extract tokens
access_token=$(echo $login_response | jq -r '.access_token')

if [ "$access_token" != "null" ] && [ "$access_token" != "" ]; then
    echo -e "\n${GREEN}Authentication successful${NC}"
    echo "Access Token: ${access_token:0:50}..."

    # Test photobook generation for each theme
    echo -e "\n${GREEN}Testing Photobook Generation${NC}"
    
    # Array of themes to test
    themes=("kids_christmas" "kids_dream_jobs" "kids_superhero")
    
    for theme in "${themes[@]}"; do
        echo -e "\nTesting photobook generation for theme: $theme"
        
        # Create photobook
        photobook_response=$(curl -s -X POST "${BASE_URL}/api/model/47/photobook" \
            -H "Authorization: Bearer $access_token" \
            -H "Content-Type: application/json" \
            -d "{
                \"theme_name\": \"$theme\"
            }")
        
        echo "Photobook creation response: $photobook_response"
        
        # Extract photobook ID and job ID
        photobook_id=$(echo $photobook_response | jq -r '.photobook_id')
        job_id=$(echo $photobook_response | jq -r '.job_id')
        
        if [ "$job_id" != "null" ] && [ "$job_id" != "" ]; then
            # Monitor job status
            echo -e "\nMonitoring job status for theme $theme..."
            for i in {1..10}; do
                echo -e "\nChecking job status (attempt $i)..."
                status_response=$(curl -s -X GET "${BASE_URL}/api/model/job/$job_id/status" \
                    -H "Authorization: Bearer $access_token")
                echo "Job status: $status_response"
                
                # Check if job is completed
                job_status=$(echo $status_response | jq -r '.status')
                if [ "$job_status" = "COMPLETED" ]; then
                    echo -e "\n${GREEN}Photobook generation completed for theme $theme!${NC}"
                    
                    # Get photobook details
                    echo -e "\nGetting photobook details..."
                    photobook_details=$(curl -s -X GET "${BASE_URL}/api/photobook/$photobook_id" \
                        -H "Authorization: Bearer $access_token")
                    echo "Photobook details: $photobook_details"
                    break
                elif [ "$job_status" = "FAILED" ]; then
                    echo -e "\n${RED}Photobook generation failed for theme $theme!${NC}"
                    break
                fi
                
                # Wait before next check
                sleep 10
            done
        else
            echo -e "\n${RED}Failed to get job ID for theme $theme${NC}"
        fi
        
        # Wait between themes
        sleep 5
    done

    # List all photobooks
    echo -e "\n${GREEN}Listing all photobooks${NC}"
    photobooks_response=$(curl -s -X GET "${BASE_URL}/api/model/photobooks" \
        -H "Authorization: Bearer $access_token")
    echo "Photobooks list: $photobooks_response"

else
    echo -e "\n${RED}Failed to get access token. Cannot proceed with tests.${NC}"
fi