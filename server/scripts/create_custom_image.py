import os
import logging
import requests
import time
from pathlib import Path

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_custom_image(api_key: str, instance_id: str, name: str):
    """Create custom image from an instance"""
    base_url = "https://cloud.lambdalabs.com/api/v1"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Setup environment
    setup_commands = [
        # System setup
        "sudo apt-get update && sudo apt-get upgrade -y",
        
        # Clone and setup AI toolkit
        "mkdir -p /home/ubuntu/workspace",
        "cd /home/ubuntu/workspace && git clone https://github.com/ostris/ai-toolkit",
        "cd /home/ubuntu/workspace/ai-toolkit && git submodule update --init --recursive",
        "cd /home/ubuntu/workspace/ai-toolkit && pip install -r requirements.txt",
        
        # Create necessary directories
        "mkdir -p /home/ubuntu/workspace/datasets",
        "mkdir -p /home/ubuntu/workspace/models",
        "mkdir -p /home/ubuntu/model_cache",
        "mkdir -p /home/ubuntu/data",
        
        # Set environment variables in .bashrc
        'echo "export HF_HUB_ENABLE_HF_TRANSFER=1" >> ~/.bashrc',
        'echo "export DISABLE_TELEMETRY=YES" >> ~/.bashrc',
        'echo "export PATH=$PATH:/home/ubuntu/.local/bin" >> ~/.bashrc',
        
        # Cleanup to reduce image size
        "sudo apt-get clean",
        "sudo apt-get autoremove -y"
    ]
    
    try:
        logger.info("Starting environment setup...")
        # Run setup commands
        for cmd in setup_commands:
            logger.info(f"Running: {cmd}")
            response = requests.post(
                f"{base_url}/instances/{instance_id}/execute",
                headers=headers,
                json={'command': cmd}
            )
            response.raise_for_status()
            result = response.json()
            if result.get('exit_code', 0) != 0:
                raise Exception(f"Command failed: {cmd}\nError: {result.get('stderr', 'Unknown error')}")
            logger.info(f"Command completed successfully")
        
        logger.info("Environment setup completed. Creating image...")
        # Create image
        response = requests.post(
            f"{base_url}/instance-images",
            headers=headers,
            json={
                'instance_id': instance_id,
                'name': name
            }
        )
        response.raise_for_status()
        
        logger.info(f"Started creating image: {name}")
        
        # Wait for image creation
        while True:
            response = requests.get(
                f"{base_url}/instance-images",
                headers=headers
            )
            response.raise_for_status()
            images = response.json()['data']
            
            for image in images:
                if image['name'] == name:
                    if image['status'] == 'active':
                        logger.info(f"Image created successfully: {name}")
                        return image['id']
                    elif image['status'] == 'failed':
                        raise Exception("Image creation failed")
            
            logger.info("Still creating image... waiting 30 seconds")
            time.sleep(30)
            
    except Exception as e:
        logger.error(f"Failed to create image: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        # Get API key from environment
        api_key = os.getenv('LAMBDA_API_KEY')
        if not api_key:
            api_key = input("Enter your Lambda API key: ")
        
        # Get instance ID from environment or input
        instance_id = os.getenv('LAMBDA_INSTANCE_ID')
        if not instance_id:
            instance_id = input("Enter instance ID to create image from: ")
        
        logger.info(f"Using instance ID: {instance_id}")
        
        image_name = "ai-toolkit-environment"
        
        image_id = create_custom_image(api_key, instance_id, image_name)
        print("\n=================================")
        print(f"Created image ID: {image_id}")
        print("=================================")
        print("\nUpdate your config with:")
        print(f"LAMBDA_CUSTOM_IMAGE_ID='{image_id}'")
        
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        raise