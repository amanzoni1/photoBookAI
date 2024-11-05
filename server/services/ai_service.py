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
        """Cache AI toolkit files locally to speed up setup"""
        toolkit_cache = self.cache_path / 'ai-toolkit'
        if not toolkit_cache.exists():
            logger.info("Caching AI toolkit files...")
            import subprocess
            subprocess.run([
                'git', 'clone', 'https://github.com/ostris/ai-toolkit',
                str(toolkit_cache)
            ], check=True)
            
            # Create requirements archive
            requirements_txt = toolkit_cache / 'requirements.txt'
            if requirements_txt.exists():
                import zipfile
                with zipfile.ZipFile(self.cache_path / 'requirements.zip', 'w') as zf:
                    zf.write(requirements_txt, 'requirements.txt')

    def launch_instance(self) -> LambdaInstance:
        """Launch a new Lambda instance with optimized environment setup"""
        try:
            # Launch instance with startup script
            startup_script = """#!/bin/bash
            # Parallel execution of apt updates and directory creation
            (sudo apt-get update && sudo apt-get install -y python3-pip git) &
            mkdir -p /home/ubuntu/workspace/{datasets,models,cache} &
            wait
            """
            
            response = requests.post(
                f"{self.base_url}/instance-operations/launch",
                headers={'Authorization': f'Bearer {self.api_key}'},
                json={
                    'region_name': self.region,
                    'instance_type_name': self.instance_type,
                    'quantity': 1,
                    'file_data': startup_script
                }
            )
            response.raise_for_status()
            
            instance_id = response.json()['instance_ids'][0]
            instance = LambdaInstance(instance_id, self.config)
            
            # Wait for instance to be ready
            instance.wait_for_completion()
            
            # Upload cached toolkit and requirements in parallel
            self._setup_environment_parallel(instance)
            
            return instance
            
        except Exception as e:
            logger.error(f"Failed to launch and setup instance: {str(e)}")
            raise

    def _setup_environment_parallel(self, instance: LambdaInstance):
        """Setup environment with parallel operations"""
        try:
            # Upload cached files
            instance.upload_file(
                str(self.cache_path / 'requirements.zip'),
                f"{self.remote_base}/requirements.zip"
            )
            
            # Setup commands optimized for parallel execution
            setup_cmd = """
                cd /home/ubuntu/workspace && \
                (unzip requirements.zip && pip install -r requirements.txt) & \
                (git clone https://github.com/ostris/ai-toolkit && \
                cd ai-toolkit && \
                git submodule update --init --recursive) & \
                wait && \
                echo "export HF_HUB_ENABLE_HF_TRANSFER=1" >> ~/.bashrc && \
                echo "export DISABLE_TELEMETRY=YES" >> ~/.bashrc && \
                source ~/.bashrc
            """
            
            result = instance.execute_command(setup_cmd)
            if result.get('exit_code', 0) != 0:
                raise Exception(f"Setup failed: {result.get('stderr', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Environment setup failed: {str(e)}")
            raise

    def prepare_dataset(self, model_id: int, image_ids: List[int]) -> Path:
        """Prepare dataset for training with optimized file handling"""
        dataset_path = self.datasets_path / str(model_id)
        if dataset_path.exists():
            shutil.rmtree(dataset_path)
        dataset_path.mkdir(parents=True)
        
        # Get images from database efficiently
        images = UserImage.query.filter(UserImage.id.in_(image_ids)).all()
        
        # Process images in chunks for better memory management
        chunk_size = 10
        for i in range(0, len(images), chunk_size):
            chunk = images[i:i + chunk_size]
            
            # Process chunk in parallel using threads
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=chunk_size) as executor:
                executor.map(
                    lambda x: self._process_single_image(x[0], x[1], dataset_path),
                    enumerate(chunk, start=i)
                )
        
        return dataset_path

    def _process_single_image(self, idx: int, image: UserImage, dataset_path: Path):
        """Process a single image and its caption"""
        try:
            # Get image data from storage
            image_data = self.config['storage_service'].get_file_data(image.storage_location)
            
            # Save image
            image_path = dataset_path / f"image_{idx:04d}.jpg"
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            # Create caption with trigger
            caption = image.metadata_json.get('caption', 'an image of [trigger]') if image.metadata_json else 'an image of [trigger]'
            if '[trigger]' not in caption:
                caption = f'an image of [trigger], {caption}'
                
            caption_path = dataset_path / f"image_{idx:04d}.txt"
            with open(caption_path, 'w') as f:
                f.write(caption)
                
            logger.debug(f"Processed image {idx}")
            
        except Exception as e:
            logger.error(f"Error processing image {image.id}: {str(e)}")

    def train_model(self, model_id: int, user_id: int, training_config: Dict) -> bytes:
        """Run model training with optimized data handling"""
        instance = None
        try:
            # Prepare dataset and launch instance in parallel
            logger.info(f"Starting model {model_id} training preparation")
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=2) as executor:
                dataset_future = executor.submit(
                    self.prepare_dataset, model_id, training_config['image_ids']
                )
                instance_future = executor.submit(self.launch_instance)
                
                dataset_path = dataset_future.result()
                instance = instance_future.result()
            
            # Upload dataset
            logger.info("Uploading dataset")
            remote_dataset_path = f"{self.remote_dataset}/{model_id}"
            instance.execute_command(f"mkdir -p {remote_dataset_path}")
            
            # Upload files in parallel using thread pool
            dataset_files = list(dataset_path.glob('*'))
            with ThreadPoolExecutor(max_workers=min(10, len(dataset_files))) as executor:
                upload_futures = [
                    executor.submit(
                        instance.upload_file,
                        str(file_path),
                        f"{remote_dataset_path}/{file_path.name}"
                    )
                    for file_path in dataset_files
                ]
                # Wait for all uploads to complete
                for future in upload_futures:
                    future.result()
            
            # Prepare and upload YAML config
            logger.info("Preparing training configuration")
            config_path = Path(__file__).parent / 'configs' / 'base_training.yaml'
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            # Update paths in config
            config['config']['name'] = f"model_{model_id}"
            config['config']['process'][0].update({
                'training_folder': f"{self.remote_models}/{model_id}",
                'datasets': [{
                    'folder_path': remote_dataset_path,
                    'caption_ext': "txt",
                    'caption_dropout_rate': 0.05,
                    'shuffle_tokens': False,
                    'cache_latents_to_disk': True,
                    'resolution': [512, 768, 1024]
                }]
            })
            
            # Save and upload modified config
            remote_config = f"{self.remote_base}/config_{model_id}.yaml"
            temp_config_path = self.base_path / f"config_{model_id}.yaml"
            
            with open(temp_config_path, 'w') as f:
                yaml.dump(config, f)
            
            instance.upload_file(str(temp_config_path), remote_config)
            
            # Run training with environment variables and error handling
            logger.info("Starting training")
            train_cmd = f"""
                cd {self.remote_base}/ai-toolkit && \
                export HF_HUB_ENABLE_HF_TRANSFER=1 && \
                export DISABLE_TELEMETRY=YES && \
                export HF_TOKEN='{self.config["HF_TOKEN"]}' && \
                python run.py {remote_config} 2>&1 | tee training.log
            """
            
            result = instance.execute_command(train_cmd)
            if result.get('exit_code', 0) != 0:
                # Try to get detailed error from log
                try:
                    log_result = instance.execute_command("cat training.log")
                    error_log = log_result.get('stdout', 'No log available')
                    raise Exception(f"Training failed with log:\n{error_log}")
                except:
                    raise Exception(f"Training failed: {result.get('stderr', 'Unknown error')}")
            
            # Download weights with retry logic
            logger.info("Downloading trained weights")
            remote_weights = f"{self.remote_models}/{model_id}/model.safetensors"
            local_weights = self.base_path / f"model_{model_id}.safetensors"
            
            max_retries = 3
            for retry in range(max_retries):
                try:
                    instance.download_file(remote_weights, str(local_weights))
                    break
                except Exception as e:
                    if retry == max_retries - 1:
                        raise
                    logger.warning(f"Download attempt {retry + 1} failed, retrying...")
                    time.sleep(5)
            
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
                    requests.post(
                        f"{self.base_url}/instances/{instance.instance_id}/terminate",
                        headers={'Authorization': f'Bearer {self.api_key}'}
                    )
                except Exception as e:
                    logger.error(f"Failed to terminate instance: {str(e)}")
                    
            # Cleanup local files
            try:
                if 'dataset_path' in locals():
                    shutil.rmtree(dataset_path)
                if 'local_weights' in locals():
                    local_weights.unlink()
                if 'temp_config_path' in locals():
                    temp_config_path.unlink()
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")