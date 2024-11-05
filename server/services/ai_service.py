# server/services/ai_service.py

import os
import yaml
import logging
import requests
import time
from pathlib import Path
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime

from app import db
from models import UserImage

logger = logging.getLogger(__name__)

class LambdaAPIException(Exception):
    pass

class LambdaInstance:
    def __init__(self, instance_id: str, config: Dict[str, Any]):
        self.instance_id = instance_id
        self.config = config
        self.api_key = config['LAMBDA_API_KEY']
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make request to Lambda API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Lambda API error: {str(e)}")
            raise LambdaAPIException(f"Lambda API request failed: {str(e)}")

    def upload_file(self, local_path: str, remote_path: str):
        """Upload file to instance using Lambda file transfer API"""
        try:
            with open(local_path, 'rb') as f:
                files = {'file': (os.path.basename(local_path), f)}
                response = requests.post(
                    f"{self.base_url}/instances/{self.instance_id}/files",
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    files=files,
                    data={'path': remote_path}
                )
                response.raise_for_status()
        except Exception as e:
            raise LambdaAPIException(f"File upload failed: {str(e)}")

    def download_file(self, remote_path: str, local_path: str):
        """Download file from instance using Lambda file transfer API"""
        try:
            response = requests.get(
                f"{self.base_url}/instances/{self.instance_id}/files",
                headers={'Authorization': f'Bearer {self.api_key}'},
                params={'path': remote_path}
            )
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            raise LambdaAPIException(f"File download failed: {str(e)}")

    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute command on instance"""
        try:
            response = self._make_request(
                'POST',
                f'instances/{self.instance_id}/execute',
                {'command': command}
            )
            return response
        except Exception as e:
            raise LambdaAPIException(f"Command execution failed: {str(e)}")

    def wait_for_completion(self, timeout: int = 3600):
        """Wait for instance to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self._make_request('GET', f'instances/{self.instance_id}')
            if status['status'] == 'active':
                return
            time.sleep(10)
        raise LambdaAPIException("Instance startup timeout")

class AIService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config['LAMBDA_API_KEY']
        self.instance_type = config['LAMBDA_INSTANCE_TYPE']
        self.region = config['LAMBDA_REGION']
        self.custom_image_id = config.get('LAMBDA_CUSTOM_IMAGE_ID')
        
        # Lambda paths (now pre-existing in custom image)
        self.remote_base = '/home/ubuntu/workspace'
        self.remote_dataset = f"{self.remote_base}/datasets"
        self.remote_models = f"{self.remote_base}/models"
        
        # Local paths
        self.base_path = Path(config.get('AI_TRAINING_BASE_PATH', '/tmp/ai_training'))
        self.datasets_path = self.base_path / 'datasets'
        self.datasets_path.mkdir(parents=True, exist_ok=True)
        
        # Load base YAML config
        self.config_path = Path(__file__).parent / 'configs' / 'base_training.yaml'
        if not self.config_path.exists():
            raise FileNotFoundError(f"Base training config not found at {self.config_path}")

    def launch_instance(self) -> LambdaInstance:
        """Launch a new Lambda instance using custom image"""
        try:
            # Launch instance with custom image
            response = requests.post(
                f"{self.base_url}/instance-operations/launch",
                headers={'Authorization': f'Bearer {self.api_key}'},
                json={
                    'region_name': self.region,
                    'instance_type_name': self.instance_type,
                    'quantity': 1,
                    'instance_image_id': self.custom_image_id  
                }
            )
            response.raise_for_status()
            
            instance_id = response.json()['instance_ids'][0]
            instance = LambdaInstance(instance_id, self.config)
            
            # Wait for instance to be ready
            instance.wait_for_completion()
            
            return instance
            
        except Exception as e:
            logger.error(f"Failed to launch instance: {str(e)}")
            raise

    def _load_base_config(self) -> Dict:
        """Load base training config"""
        config_path = Path(__file__).parent / 'configs' / 'base_training.yaml'
        with open(config_path) as f:
            return yaml.safe_load(f)

    def _setup_environment(self, instance: LambdaInstance):
        """Setup training environment on instance"""
        try:
            # Create directories and setup environment
            commands = [
                f'mkdir -p {self.remote_base}',
                f'mkdir -p {self.remote_dataset}',
                f'mkdir -p {self.remote_models}',
                
                # Clone and setup AI toolkit
                f'cd {self.remote_base} && git clone https://github.com/ostris/ai-toolkit',
                f'cd {self.remote_base}/ai-toolkit && git submodule update --init --recursive',
                f'cd {self.remote_base}/ai-toolkit && pip install -r requirements.txt'
            ]
            
            for cmd in commands:
                result = instance.execute_command(cmd)
                if result.get('exit_code', 0) != 0:
                    raise Exception(f"Command failed: {cmd}\nError: {result.get('stderr', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Environment setup failed: {str(e)}")
            raise

    def prepare_dataset(self, model_id: int, image_ids: List[int]) -> Path:
        """Prepare dataset for training"""
        dataset_path = self.datasets_path / str(model_id)
        if dataset_path.exists():
            shutil.rmtree(dataset_path)
        dataset_path.mkdir(parents=True)
        
        # Get images from database
        images = UserImage.query.filter(UserImage.id.in_(image_ids)).all()
        
        # Copy each image and create caption
        for idx, image in enumerate(images):
            try:
                # Get image data from storage
                image_data = self.config['storage_service'].get_file_data(image.storage_location)
                
                # Save image
                image_path = dataset_path / f"image_{idx:04d}.jpg"
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                # Create caption file with better default
                caption = image.metadata_json.get('caption', 'an image of [trigger]') if image.metadata_json else 'an image of [trigger]'
                # Ensure caption includes [trigger] if not already present
                if '[trigger]' not in caption:
                    caption = f'an image of [trigger], {caption}'
                    
                caption_path = dataset_path / f"image_{idx:04d}.txt"
                with open(caption_path, 'w') as f:
                    f.write(caption)
                    
                logger.debug(f"Processed image {idx} for model {model_id}")
                
            except Exception as e:
                logger.error(f"Error processing image {image.id}: {str(e)}")
                continue
        
        return dataset_path

    def train_model(self, model_id: int, user_id: int, training_config: Dict) -> bytes:
        """Run model training on Lambda instance"""
        instance = None
        try:
            # Prepare dataset locally
            logger.info(f"Preparing dataset for model {model_id}")
            dataset_path = self.prepare_dataset(model_id, training_config['image_ids'])
            
            # Launch instance with custom image
            logger.info("Launching Lambda instance")
            instance = self.launch_instance()
            
            # Upload dataset
            logger.info("Uploading dataset")
            remote_dataset_path = f"{self.remote_dataset}/{model_id}"
            instance.execute_command(f"mkdir -p {remote_dataset_path}")
            
            for file_path in dataset_path.glob('*'):
                instance.upload_file(
                    str(file_path),
                    f"{remote_dataset_path}/{file_path.name}"
                )
            
            # Prepare and upload YAML config
            logger.info("Preparing training configuration")
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
            
            # Update paths in config
            config['config']['name'] = f"model_{model_id}"
            config['config']['process'][0]['training_folder'] = f"{self.remote_models}/{model_id}"
            config['config']['process'][0]['datasets'][0]['folder_path'] = remote_dataset_path
            
            # Save and upload modified config
            remote_config = f"{self.remote_base}/config_{model_id}.yaml"
            config_path = self.base_path / f"config_{model_id}.yaml"
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
            
            instance.upload_file(str(config_path), remote_config)
            
            # Run training 
            logger.info("Starting training")
            train_cmd = f"""
                cd {self.remote_base}/ai-toolkit && \
                HF_TOKEN='{self.config["HF_TOKEN"]}' \
                python run.py {remote_config}
            """
            
            result = instance.execute_command(train_cmd)
            if result.get('exit_code', 0) != 0:
                raise Exception(f"Training failed: {result.get('stderr', 'Unknown error')}")
            
            # Download weights
            logger.info("Downloading trained weights")
            remote_weights = f"{self.remote_models}/{model_id}/model.safetensors"
            local_weights = self.base_path / f"model_{model_id}.safetensors"
            
            instance.download_file(remote_weights, str(local_weights))
            
            with open(local_weights, 'rb') as f:
                weights_data = f.read()
            
            return weights_data
            
        finally:
            # Cleanup
            if instance:
                try:
                    instance.execute_command(f'rm -rf {self.remote_base}/config_{model_id}.yaml')
                    instance.execute_command(f'rm -rf {self.remote_dataset}/{model_id}')
                    instance.execute_command(f'rm -rf {self.remote_models}/{model_id}')
                    requests.post(
                        f"{self.base_url}/instances/{instance.instance_id}/terminate",
                        headers={'Authorization': f'Bearer {self.api_key}'}
                    )
                except:
                    pass
                    
            # Remove local files
            try:
                shutil.rmtree(dataset_path)
                if 'local_weights' in locals():
                    local_weights.unlink()
                if 'config_path' in locals():
                    config_path.unlink()
            except:
                pass