# list_instances.py

import os
import requests

def list_instances(api_key: str):
    base_url = "https://cloud.lambdalabs.com/api/v1"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{base_url}/instances",
            headers=headers
        )
        response.raise_for_status()
        instances = response.json()
        
        print("\nYour running instances:")
        print("-----------------------")
        for instance in instances.get('data', []):
            print(f"Instance ID: {instance['id']}")
            print(f"Name: {instance['name']}")
            print(f"Type: {instance['instance_type']}")
            print(f"Region: {instance['region']}")
            print(f"Status: {instance['status']}")
            print("-----------------------")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    api_key = os.getenv('LAMBDA_API_KEY')
    if not api_key:
        api_key = input("Enter your Lambda API key: ")
    
    list_instances(api_key)