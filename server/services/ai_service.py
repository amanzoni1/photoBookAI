# server/services/ai_service.py

import os
import yaml
import logging
import requests
import time
import asyncio
import concurrent.futures
from pathlib import Path
import shutil
from typing import Dict, Any, List, Optional
import subprocess
from models import UserImage

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
        self.ssh_key_path = config['LAMBDA_SSH_KEY_PATH']  # Path to your SSH key

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
                '-o', 'StrictHostKeyChecking=no',  # Bypass host key verification
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
            result = subprocess.run(ssh_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
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
                # logger.debug(f"Current instance status: {current_status}")
                if current_status and current_status.strip().lower() == 'active':
                    logger.info(f"Instance {self.instance_id} is active.")
                    self.instance_ip = status_response.get('data', {}).get('ip')
                    if not self.instance_ip:
                        raise LambdaAPIException("Instance IP not found in the response.")
                    return
                elif current_status in ['error', 'failed']:
                    raise LambdaAPIException(f"Instance encountered an error during boot: {current_status}")
                # logger.debug("Instance not active yet. Waiting...")
                time.sleep(5)  
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
        self.remote_base = '/home/ubuntu'
        self.remote_workspace = f"{self.remote_base}/ai-toolkit"

        # Local paths with caching
        self.base_path = Path(config.get('AI_TRAINING_BASE_PATH', '/tmp/ai_training'))
        self.datasets_path = self.base_path / 'datasets'
        self.cache_path = self.base_path / 'cache'
        self.datasets_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def launch_instance(self) -> LambdaInstance:
        """Launch a new Lambda instance."""
        try:
            ssh_key_name = self.config['LAMBDA_SSH_KEY_NAME']  # Ensure this is set in your config

            payload = {
                'region_name': self.region,
                'instance_type_name': self.instance_type,
                'quantity': 1,
                'ssh_key_names': [ssh_key_name]
            }
            logger.debug(f"Launching instance with payload: {payload}")

            response = requests.post(
                f"{self.base_url}/instance-operations/launch",
                headers={'Authorization': f'Bearer {self.api_key}'},
                json=payload
            )
            logger.debug(f"Lambda API response: {response.status_code} - {response.text}")
            response.raise_for_status()

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
        """Setup environment with the specified steps."""
        try:
            # Commands to execute on the instance
            setup_commands = f"""
            cd {self.remote_base} && \
            git clone https://github.com/amanzoni1/ai-toolkit.git && \
            cd ai-toolkit && \
            git submodule update --init --recursive && \
            python3 -m venv venv && \
            source venv/bin/activate && \
            pip install torch && \
            pip install -r requirements.txt
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

    def prepare_dataset(self, model_id: int, file_info: List[Dict]) -> Path:
        """Prepare dataset for training from temporary files."""
        dataset_path = self.datasets_path / str(model_id)
        if dataset_path.exists():
            shutil.rmtree(dataset_path)
        dataset_path.mkdir(parents=True)

        # Process images
        for idx, info in enumerate(file_info):
            try:
                source_path = Path(info['path'])
                if not source_path.exists():
                    raise FileNotFoundError(f"Source file not found: {source_path}")

                # Copy image to dataset directory
                image_path = dataset_path / f"image_{idx:04d}.jpg"
                shutil.copy2(source_path, image_path)

                # Create caption with trigger
                caption = 'an image of [trigger]'
                caption_path = dataset_path / f"image_{idx:04d}.txt"
                with open(caption_path, 'w') as f:
                    f.write(caption)

                logger.debug(f"Processed image {idx}")

            except Exception as e:
                logger.error(f"Error processing image {info['original_filename']}: {str(e)}")
                raise

        return dataset_path

    def train_model(self, model_id: int, user_id: int, training_config: Dict) -> bytes:
        """Run model training."""
        instance = None
        dataset_path = None
        local_weights = None
        temp_config_path = None

        try:
            logger.info(f"Starting model {model_id} training preparation")

            # Launch instance and prepare dataset simultaneously
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                instance_future = executor.submit(self.launch_instance)
                dataset_future = executor.submit(
                    self.prepare_dataset,
                    model_id,
                    training_config['file_info']
                )

                # Wait for both to complete
                instance = instance_future.result()
                dataset_path = dataset_future.result()

            # Create dataset directory and upload dataset
            logger.info("Uploading dataset")
            remote_dataset_path = f"{self.remote_workspace}/dataset"
            instance.execute_command_ssh(f"mkdir -p {remote_dataset_path}")

            # Upload dataset files
            dataset_files = list(dataset_path.glob('*'))
            for file_path in dataset_files:
                instance.upload_file_scp(str(file_path), f"{remote_dataset_path}/{file_path.name}")

            # Modify existing YAML config to update model name
            logger.info("Updating training configuration")
            model_name = f"model_{model_id}"
            update_config_cmd = f"""
            cd {self.remote_workspace} && \
            sed -i 's/name: ".*"/name: "{model_name}"/' base_training.yaml
            """
            instance.execute_command_ssh(update_config_cmd)

            # Run training
            logger.info("Starting training")
            train_cmd = f"""
            cd {self.remote_workspace} && \
            source venv/bin/activate && \
            export HF_TOKEN='{self.config["HF_TOKEN"]}' && \
            python run.py base_training.yaml
            """
            result = instance.execute_command_ssh(train_cmd)
            logger.debug(f"Training command output: {result}")

            # Check for training success
            if "Error" in result or "Exception" in result:
                # Fetch training log for details
                log_result = instance.execute_command_ssh(f"cat {self.remote_workspace}/training.log")
                raise Exception(f"Training failed with log:\n{log_result}")

            # Download trained weights
            logger.info("Downloading trained weights")
            remote_weights = f"{self.remote_workspace}/output/{model_name}.safetensors"
            local_weights = self.base_path / f"{model_name}.safetensors"

            instance.download_file_scp(remote_weights, str(local_weights))

            with open(local_weights, 'rb') as f:
                weights_data = f.read()

            return weights_data

        except Exception as e:
            logger.error(f"Training error for model {model_id}: {str(e)}")
            raise

        finally:
            # Always terminate the instance when done
            if instance:
                try:
                    logger.info("Terminating instance")
                    response = requests.post(
                        f"{self.base_url}/instance-operations/terminate",
                        headers={'Authorization': f'Bearer {self.api_key}'},
                        json={'instance_ids': [instance.instance_id]}
                    )
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"Failed to terminate instance: {str(e)}")

            # Cleanup local files
            try:
                if dataset_path and dataset_path.exists():
                    shutil.rmtree(dataset_path)
                if local_weights and Path(local_weights).exists():
                    local_weights.unlink()
                if temp_config_path and temp_config_path.exists():
                    temp_config_path.unlink()
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")