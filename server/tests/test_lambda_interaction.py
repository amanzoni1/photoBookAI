import os
import logging
import requests
import time
from pathlib import Path
import subprocess
from typing import Dict, Any, Optional
from dotenv import load_dotenv  # Ensure you have python-dotenv installed

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LambdaAPIException(Exception):
    """Custom exception for Lambda API errors."""
    pass

class LambdaInstance:
    def __init__(self, instance_id: str, config: Dict[str, Any]):
        self.instance_id = instance_id
        self.config = config
        self.api_key = config['LAMBDA_API_KEY']
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.instance_ip = None  # To be fetched after instance is active
        self.ssh_key_path = config['LAMBDA_SSH_KEY_PATH']

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make request to Lambda API."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        url = f"{self.base_url}/{endpoint}"
        logger.debug(f"Making {method} request to {url} with data: {data}")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            )
            logger.debug(f"Received response: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Lambda API request failed: {str(e)}")
            raise LambdaAPIException(f"Lambda API request failed: {str(e)}")

    def get_instance_details(self) -> Dict[str, Any]:
        """Retrieve detailed information about the instance."""
        logger.debug(f"Fetching details for instance {self.instance_id}")
        return self._make_request('GET', f'instances/{self.instance_id}')

    def upload_file_scp(self, local_path: str, remote_path: str):
        """Upload file to instance using SCP."""
        instance_ip = self.instance_ip
        ssh_key = self.ssh_key_path
        try:
            scp_command = [
                'scp',
                '-i', ssh_key,
                '-o', 'StrictHostKeyChecking=no',  # Optional: to bypass host key verification
                local_path,
                f'ubuntu@{instance_ip}:{remote_path}'
            ]
            logger.info(f"Uploading {local_path} to {instance_ip}:{remote_path}")
            subprocess.run(scp_command, check=True)
            logger.info("File uploaded successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"SCP upload failed: {e}")
            raise LambdaAPIException(f"SCP upload failed: {e}") from e

    def download_file_scp(self, remote_path: str, local_path: str):
        """Download file from instance using SCP."""
        instance_ip = self.instance_ip
        ssh_key = self.ssh_key_path
        try:
            scp_command = [
                'scp',
                '-i', ssh_key,
                '-o', 'StrictHostKeyChecking=no',
                f'ubuntu@{instance_ip}:{remote_path}',
                local_path
            ]
            logger.info(f"Downloading {remote_path} from {instance_ip} to {local_path}")
            subprocess.run(scp_command, check=True)
            logger.info("File downloaded successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"SCP download failed: {e}")
            raise LambdaAPIException(f"SCP download failed: {e}") from e

    def execute_command_ssh(self, command: str) -> str:
        """Execute command on instance via SSH."""
        instance_ip = self.instance_ip
        ssh_key = self.ssh_key_path
        try:
            ssh_command = [
                'ssh',
                '-i', ssh_key,
                '-o', 'StrictHostKeyChecking=no',
                f'ubuntu@{instance_ip}',
                command
            ]
            logger.info(f"Executing command on {instance_ip}: {command}")
            result = subprocess.run(ssh_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.debug(f"Command output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Command stderr: {result.stderr}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"SSH command failed: {e.stderr}")
            raise LambdaAPIException(f"SSH command failed: {e.stderr}") from e

    def wait_for_completion(self, timeout: int = 3600):
        """Wait for instance to be ready."""
        logger.info(f"Waiting for instance {self.instance_id} to become active.")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                status_response = self.get_instance_details()
                current_status = status_response.get('data', {}).get('status')
                logger.debug(f"Current instance status: {current_status} ({repr(current_status)})")
                if current_status and current_status.strip().lower() == 'active':
                    logger.info(f"Instance {self.instance_id} is active.")
                    self.instance_ip = status_response.get('data', {}).get('ip')
                    if not self.instance_ip:
                        raise LambdaAPIException("Instance IP not found in the response.")
                    return
                elif current_status in ['error', 'failed']:
                    raise LambdaAPIException(f"Instance encountered an error during boot: {current_status}")
                logger.debug("Instance not active yet. Waiting...")
                time.sleep(60)  # Wait for 60 seconds before next check
            except LambdaAPIException as e:
                logger.error(f"Error checking instance status: {str(e)}")
                raise
        raise LambdaAPIException("Instance startup timeout.")

class AIService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config['LAMBDA_API_KEY']
        self.instance_type = config['LAMBDA_INSTANCE_TYPE']
        self.region = config['LAMBDA_REGION']
        self.base_url = "https://cloud.lambdalabs.com/api/v1"

        # Lambda paths
        self.remote_base = '/home/ubuntu/workspace'
        self.remote_dataset = f"{self.remote_base}/datasets"
        self.remote_models = f"{self.remote_base}/models"

        # Local paths with caching
        self.base_path = Path(config.get('AI_TRAINING_BASE_PATH', '/tmp/ai_training'))
        self.datasets_path = self.base_path / 'datasets'
        self.cache_path = self.base_path / 'cache'
        self.datasets_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)

        # Cache toolkit requirements
        self._cache_toolkit_files()

    def _cache_toolkit_files(self):
        """Cache AI toolkit files locally to speed up setup."""
        toolkit_cache = self.cache_path / 'ai-toolkit'
        if not toolkit_cache.exists():
            logger.info("Caching AI toolkit files...")
            try:
                subprocess.run([
                    'git', 'clone', 'https://github.com/ostris/ai-toolkit',
                    str(toolkit_cache)
                ], check=True)
                logger.info("AI toolkit cloned successfully.")

                # Create requirements archive
                requirements_txt = toolkit_cache / 'requirements.txt'
                if requirements_txt.exists():
                    import zipfile
                    with zipfile.ZipFile(self.cache_path / 'requirements.zip', 'w') as zf:
                        zf.write(requirements_txt, 'requirements.txt')
                    logger.info("Requirements.zip created successfully.")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone AI toolkit: {str(e)}")
                raise LambdaAPIException(f"Failed to clone AI toolkit: {str(e)}")

    def launch_instance(self) -> LambdaInstance:
        """Launch a new Lambda instance with optimized environment setup."""
        try:
            # Remove 'file_data' from the payload as it's not recognized by the API
            # Specify the file system name if you have one; otherwise, omit it
            # For this example, we'll assume no filesystem is attached

            # SSH key name
            ssh_key_name = 'lambda-ssh'  # Ensure this matches your registered SSH key name

            # Launch payload without 'file_data' and 'file_system_names'
            payload = {
                'region_name': self.region,  # e.g., 'us-west-2'
                'instance_type_name': self.instance_type,  # e.g., 'gpu_1x_h100_pcie'
                'quantity': 1,
                'ssh_key_names': [ssh_key_name]
                # 'file_system_names': ['shared-fs']  # Uncomment if you have a filesystem
            }
            logger.debug(f"Launching instance with payload: {payload}")

            response = requests.post(
                f"{self.base_url}/instance-operations/launch",
                headers={'Authorization': f'Bearer {self.api_key}'},
                json=payload
            )
            logger.debug(f"Lambda API response: {response.status_code} - {response.text}")
            response.raise_for_status()

            # Extract instance ID from the nested 'data' object
            response_data = response.json()
            if 'data' not in response_data or 'instance_ids' not in response_data['data']:
                raise LambdaAPIException("Invalid API response format")

            instance_id = response_data['data']['instance_ids'][0]
            instance = LambdaInstance(instance_id, self.config)

            # Wait for instance to be ready
            instance.wait_for_completion()

            # Setup environment via SSH
            self._setup_environment(instance)

            return instance

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - Response: {http_err.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to launch and setup instance: {str(e)}")
            raise

    def _setup_environment(self, instance: LambdaInstance):
        """Setup environment with sequential operations."""
        try:
            # Step 1: Create workspace directories via SSH
            create_dirs_command = "mkdir -p /home/ubuntu/workspace/datasets /home/ubuntu/workspace/models /home/ubuntu/workspace/cache"
            logger.info("Creating workspace directories on the instance...")
            instance.execute_command_ssh(create_dirs_command)
            logger.info("Workspace directories created successfully.")

            # Step 2: Upload cached requirements.zip via SCP
            local_requirements_zip = str(self.cache_path / 'requirements.zip')
            remote_requirements_zip = f"{self.remote_base}/requirements.zip"
            logger.info("Uploading requirements.zip to the instance...")
            instance.upload_file_scp(local_requirements_zip, remote_requirements_zip)
            logger.info("Requirements.zip uploaded successfully.")

            # Step 3: Execute setup commands via SSH
            setup_commands = """
cd /home/ubuntu/workspace && \
unzip requirements.zip && \
pip install -r requirements.txt && \
git clone https://github.com/ostris/ai-toolkit && \
cd ai-toolkit && \
git submodule update --init --recursive && \
echo "export HF_HUB_ENABLE_HF_TRANSFER=1" >> ~/.bashrc && \
echo "export DISABLE_TELEMETRY=YES" >> ~/.bashrc && \
source ~/.bashrc
"""
            logger.info("Executing setup commands on the instance...")
            command_result = instance.execute_command_ssh(setup_commands)
            logger.debug(f"Setup command output: {command_result}")
            logger.info("Environment setup completed successfully.")
        except LambdaAPIException as e:
            logger.error(f"Environment setup failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Environment setup failed: {str(e)}")
            raise

    def test_interaction(self):
        """Test interaction with Lambda Labs API and SSH."""
        try:
            # Step 1: Launch Instance
            logger.info("Launching Lambda instance...")
            instance = self.launch_instance()
            logger.info(f"Instance {instance.instance_id} launched successfully with IP {instance.instance_ip}.")

            # Step 2: Upload a Test File via SCP
            test_local_file = self.cache_path / 'requirements.zip'  # Example file
            test_remote_path = f"{self.remote_base}/test_requirements.zip"
            logger.info("Uploading test_requirements.zip to the instance...")
            instance.upload_file_scp(str(test_local_file), test_remote_path)
            logger.info("Test file uploaded successfully.")

            # Step 3: Execute a Test Command via SSH
            test_command = f"ls -l {self.remote_base}/"
            logger.info("Executing test command to list remote workspace contents...")
            command_output = instance.execute_command_ssh(test_command)
            logger.info(f"Test command output:\n{command_output}")

            # Step 4: Download the Test File Back via SCP
            download_local_path = self.base_path / 'downloaded_test_requirements.zip'
            logger.info("Downloading test_requirements.zip back to local machine...")
            instance.download_file_scp(test_remote_path, str(download_local_path))
            logger.info(f"Test file downloaded successfully to {download_local_path}")

            # Optional: Verify the downloaded file exists
            if download_local_path.exists():
                logger.info("Downloaded test file exists. Interaction successful.")
            else:
                logger.error("Downloaded test file does not exist. Interaction failed.")

            # Step 5: Terminate the Instance
            logger.info("Terminating the Lambda instance...")
            termination_payload = {'instance_ids': [instance.instance_id]}
            termination_response = requests.post(
                f"{self.base_url}/instance-operations/terminate",
                headers={'Authorization': f'Bearer {self.api_key}'},
                json=termination_payload
            )
            logger.debug(f"Termination response: {termination_response.status_code} - {termination_response.text}")
            termination_response.raise_for_status()
            logger.info(f"Instance {instance.instance_id} terminated successfully.")

        except LambdaAPIException as e:
            logger.error(f"Lambda API Exception: {str(e)}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Load configuration from environment variables or a config file
    config = {
        'LAMBDA_API_KEY': os.getenv('LAMBDA_API_KEY'),
        'LAMBDA_INSTANCE_TYPE': os.getenv('LAMBDA_INSTANCE_TYPE', 'gpu_1x_h100_pcie'),  # Replace with actual instance type
        'LAMBDA_REGION': os.getenv('LAMBDA_REGION', 'us-west-2'),  # Replace with your valid region
        'AI_TRAINING_BASE_PATH': os.getenv('AI_TRAINING_BASE_PATH', '/tmp/ai_training'),
        'HF_TOKEN': os.getenv('HF_TOKEN'),  # If required for your setup
        'LAMBDA_SSH_KEY_PATH': os.getenv('LAMBDA_SSH_KEY_PATH')  # Path to your SSH key
    }

    # Validate configuration
    missing_configs = [key for key, value in config.items() if not value]
    if missing_configs:
        logger.error(f"Missing configuration for: {', '.join(missing_configs)}")
        return

    # Initialize AIService
    ai_service = AIService(config)

    # Run the test interaction
    ai_service.test_interaction()

if __name__ == "__main__":
    main()