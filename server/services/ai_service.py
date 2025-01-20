# server/services/ai_service.py

import os
import yaml
import json
import logging
import requests
import time
import concurrent.futures
from pathlib import Path
import shutil
from typing import Dict, Any, List, Optional, Tuple
import subprocess
from config import PHOTOSHOOT_THEMES

# Configure logging
logging.basicConfig(level=logging.INFO)
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
        self.instance_ip = None
        self.ssh_key_path = config['LAMBDA_SSH_KEY_PATH']

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make request to Lambda API with better error handling."""
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
                json=data,
                timeout=30  # Add timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Lambda API request timed out")
            raise LambdaAPIException("Request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Lambda API request failed: {str(e)}")
            raise LambdaAPIException(f"Request failed: {str(e)}")
        
    def get_instance_details(self) -> Dict[str, Any]:
        """Get instance details with retries."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self._make_request('GET', f'instances/{self.instance_id}')
            except LambdaAPIException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

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
        """Wait for instance to be ready with improved status checking."""
        logger.info(f"Waiting for instance {self.instance_id} to become active")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status_response = self.get_instance_details()
                current_status = status_response.get('data', {}).get('status', '').strip().lower()
                
                if current_status == 'active':
                    self.instance_ip = status_response.get('data', {}).get('ip')
                    if not self.instance_ip:
                        raise LambdaAPIException("Instance IP not found")
                    logger.info(f"Instance {self.instance_id} is active at {self.instance_ip}")
                    return
                elif current_status in ['error', 'failed', 'terminated']:
                    raise LambdaAPIException(f"Instance failed with status: {current_status}")
                
                time.sleep(5)
            except LambdaAPIException as e:
                logger.error(f"Error checking instance status: {str(e)}")
                raise

        raise LambdaAPIException("Instance startup timeout")
    
class AIService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.api_key = config['LAMBDA_API_KEY']
        
        # Region and instance configuration
        self.regions = config['LAMBDA_REGIONS'] if isinstance(config['LAMBDA_REGIONS'], list) else config['LAMBDA_REGIONS'].split(',')
        self.instance_types = config['LAMBDA_INSTANCE_TYPES'] if isinstance(config['LAMBDA_INSTANCE_TYPES'], list) else config['LAMBDA_INSTANCE_TYPES'].split(',')
        
        # Local paths
        self.base_path = Path('/tmp/ai_training')
        self.datasets_path = self.base_path / 'datasets'
        self.datasets_path.mkdir(parents=True, exist_ok=True)
        
        # Remote paths
        self.remote_base = "/home/ubuntu"
        self.remote_workspace = f"{self.remote_base}/ai-toolkit"

    def launch_instance(self) -> LambdaInstance:
        """Launch instance with proper ordering and error handling."""
        errors = []
        
        # Try each instance type in order (first is preferred)
        for instance_type in self.instance_types:
            # Try each region in order (first is closest/preferred)
            for region in self.regions:
                try:
                    logger.info(f"Attempting to launch {instance_type} in {region}")
                    
                    response = requests.post(
                        f"{self.base_url}/instance-operations/launch",
                        headers={'Authorization': f'Bearer {self.api_key}'},
                        json={
                            'region_name': region,
                            'instance_type_name': instance_type,
                            'quantity': 1,
                            'ssh_key_names': [self.config['LAMBDA_SSH_KEY_NAME']]
                        },
                        timeout=30
                    )
                    
                    # Handle specific error cases
                    if response.status_code == 400:
                        error_data = response.json()
                        error_message = error_data.get('error', '')
                        
                        if "insufficient-capacity" in error_message:
                            # No capacity in this region, try next region
                            logger.warning(f"No capacity in {region} for {instance_type}")
                            continue
                            
                        elif "invalid-instance-type" in error_message:
                            # Invalid instance type, skip to next type
                            logger.error(f"Invalid instance type {instance_type}")
                            break  # Break inner loop to try next instance type
                            
                        elif "invalid-region" in error_message:
                            # Invalid region, skip this region
                            logger.error(f"Invalid region {region}")
                            continue
                            
                        else:
                            # Other API error
                            raise LambdaAPIException(f"API error: {error_message}")
                    
                    # If we get here, request was successful
                    response.raise_for_status()
                    instance_id = response.json()['data']['instance_ids'][0]
                    
                    # Create instance and wait for it to be ready
                    instance = LambdaInstance(instance_id, self.config)
                    instance.wait_for_completion()
                    
                    logger.info(f"Successfully launched {instance_type} in {region}")
                    return instance
                    
                except requests.exceptions.Timeout:
                    # Timeout error, try next region
                    logger.warning(f"Request timed out for {instance_type} in {region}")
                    errors.append(f"Timeout in {region}")
                    continue
                    
                except LambdaAPIException as e:
                    # API error, decide whether to try next region or instance type
                    if "capacity" in str(e).lower():
                        logger.warning(f"Capacity error in {region}: {str(e)}")
                        continue  # Try next region
                    else:
                        logger.error(f"API error with {instance_type}: {str(e)}")
                        break  # Try next instance type
                    
                except Exception as e:
                    # Unexpected error, try next region
                    logger.error(f"Unexpected error launching {instance_type} in {region}: {str(e)}")
                    errors.append(f"Error in {region}: {str(e)}")
                    continue
        
        # If we get here, all combinations failed
        error_msg = f"Failed to launch instance with any configuration. Errors: {'; '.join(errors)}"
        logger.error(error_msg)
        raise LambdaAPIException(error_msg)
    
    def _setup_training_environment(self, instance: LambdaInstance):
        """Setup training environment with the specified steps."""
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

    def _setup_generation_environment(self, instance: LambdaInstance):
        """Setup generation environment"""
        try:
            setup_commands = f"""
            cd {self.remote_workspace} && \
            source venv/bin/activate && \
            pip install --no-cache-dir transformers accelerate peft diffusers safetensors
            """
            
            logger.info("Setting up generation environment...")
            command_result = instance.execute_command_ssh(setup_commands)
            logger.info("Generation environment setup completed")
        except Exception as e:
            logger.error(f"Generation environment setup failed: {str(e)}")
            raise

    # def _setup_generation_environment(self, instance: LambdaInstance):
    #     """Setup environment specifically for image generation."""
    #     try:
    #         setup_commands = f"""
    #         cd {self.remote_base} && \
    #         python3 -m venv venv && \
    #         source venv/bin/activate && \
    #         pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu118 && \
    #         pip install --no-cache-dir transformers accelerate peft diffusers safetensors && \
    #         mkdir -p output
    #         """
            
    #         logger.info("Setting up generation environment...")
    #         result = instance.execute_command_ssh(setup_commands)
    #         logger.debug(f"Setup output: {result}")

    #         # Create simple generation script
    #         generation_script = """
    #         import os
    #         import torch
    #         from diffusers import DiffusionPipeline

    #         def generate():
    #             # Load pipeline
    #             pipeline = DiffusionPipeline.from_pretrained(
    #                 "black-forest-labs/FLUX.1-dev",
    #                 torch_dtype=torch.float16
    #             )
                
    #             # Load LoRA weights
    #             pipeline.load_lora_weights(".", weight_name="model.safetensors")
    #             pipeline = pipeline.to("cuda")

    #             # Generate
    #             image = pipeline(
    #                 prompt=os.environ['PROMPT'],
    #                 num_inference_steps=int(os.environ.get('STEPS', '20')),
    #                 guidance_scale=float(os.environ.get('GUIDANCE_SCALE', '4.0'))
    #             ).images[0]
                
    #             image.save(os.environ['OUTPUT_PATH'])

    #         if __name__ == "__main__":
    #             generate()
    #         """
            
    #         # Save generation script
    #         script_path = f"{self.remote_base}/generate.py"
    #         instance.execute_command_ssh(f'echo "{generation_script}" > {script_path}')
            
    #         logger.info("Generation environment setup completed")
            
    #     except Exception as e:
    #         logger.error(f"Generation environment setup failed: {str(e)}")
    #         raise

    def prepare_dataset(self, model_id: int, file_info: List[Dict]) -> Tuple[Path, List[str]]:
        """Prepare dataset with validation."""
        dataset_path = self.datasets_path / str(model_id)
        if dataset_path.exists():
            shutil.rmtree(dataset_path)
        dataset_path.mkdir(parents=True)
        
        processed_files = []
        
        try:
            for idx, info in enumerate(file_info):
                source_path = Path(info['path'])
                if not source_path.exists():
                    raise FileNotFoundError(f"Source file not found: {source_path}")
                
                # Copy and validate image
                image_path = dataset_path / f"image_{idx:04d}.jpg"
                shutil.copy2(source_path, image_path)
                processed_files.append(str(image_path))
                
                # Create caption
                caption_path = dataset_path / f"image_{idx:04d}.txt"
                with open(caption_path, 'w') as f:
                    f.write('an image of [trigger]')
            
            return dataset_path, processed_files
            
        except Exception as e:
            logger.error(f"Dataset preparation failed: {str(e)}")
            if dataset_path.exists():
                shutil.rmtree(dataset_path)
            raise

    def generate_theme_images(self, instance: LambdaInstance, model_path: str, theme_name: str, 
                     prompts: List[str]) -> List[str]:
        """Generate images for a theme and return local paths"""
        try:
            # Setup output directory
            output_dir = f"{self.remote_base}/generated_images/{theme_name}"
            instance.execute_command_ssh(f"mkdir -p {output_dir}")
            
            # Run generation using repository script
            generation_cmd = f"""
            cd {self.remote_workspace} && \
            source venv/bin/activate && \
            export HF_TOKEN='{self.config["HF_TOKEN"]}' && \
            export PROMPTS='{json.dumps(prompts)}' && \
            export OUTPUT_DIR="{output_dir}" && \
            export MODEL_PATH="{model_path}" && \
            python generation/generate_batch.py
            """
            
            logger.info(f"Starting generation for theme: {theme_name}")
            result = instance.execute_command_ssh(generation_cmd)
            
            if "Error" in result:
                logger.error(f"Generation output: {result}")
                raise Exception(f"Generation failed for theme {theme_name}")
            
            # Download generated images
            local_paths = []
            local_dir = self.base_path / f"theme_images/{theme_name}"
            local_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Downloading generated images for theme {theme_name}")
            for i in range(len(prompts)):
                remote_path = f"{output_dir}/gen_{i:03d}.png"
                local_path = local_dir / f"gen_{i:03d}.png"
                instance.download_file_scp(remote_path, str(local_path))
                local_paths.append(str(local_path))
            
            logger.info(f"Successfully generated {len(local_paths)} images for {theme_name}")
            return local_paths
            
        except Exception as e:
            logger.error(f"Theme generation failed for {theme_name}: {str(e)}")
            raise

    def train_model(self, model_id: int, user_id: int, training_config: Dict) -> Tuple[str, Dict[str, List[str]]]:
        """Train model and generate initial photobooks.
        Returns:
            Tuple[str, Dict[str, List[str]]]: Tuple containing:
                - Path to trained model weights
                - Dictionary mapping theme names to lists of generated image paths
        """
        instance = None
        dataset_path = None
        temp_weights_path = None
        theme_images = {}
        
        try:
            logger.info(f"Starting model {model_id} training preparation")
            
            # Launch instance and prepare dataset concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                instance_future = executor.submit(self.launch_instance)
                dataset_future = executor.submit(
                    self.prepare_dataset,
                    model_id,
                    training_config['file_info']
                )
                
                instance = instance_future.result()
                dataset_path, _ = dataset_future.result()
            
            # Setup training environment first
            logger.info("Setting up training environment...")
            self._setup_training_environment(instance)
            
            # Update base_training.yaml with model info
            logger.info("Updating training configuration")
            model_name = f"model_{model_id}"
            update_config_cmd = f"""
            cd {self.remote_workspace} && \
            sed -i 's/name: ".*"/name: "{model_name}"/' base_training.yaml
            """
            instance.execute_command_ssh(update_config_cmd)
            
            # Create dataset directory and upload dataset
            logger.info("Uploading dataset")
            remote_dataset_path = f"{self.remote_workspace}/dataset"
            instance.execute_command_ssh(f"mkdir -p {remote_dataset_path}")

            # Upload dataset files
            dataset_files = list(dataset_path.glob('*'))
            for file_path in dataset_files:
                instance.upload_file_scp(str(file_path), f"{remote_dataset_path}/{file_path.name}")
            
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
                log_result = instance.execute_command_ssh(f"cat {self.remote_workspace}/training.log")
                raise Exception(f"Training failed with log:\n{log_result}")
                
            # Get model path
            remote_model_path = f"{self.remote_workspace}/output/{model_name}/{model_name}.safetensors"
            
            # Then setup generation environment
            logger.info("Setting up generation environment...")
            self._setup_generation_environment(instance)

            # Generate photobooks for each theme
            logger.info("Generating initial photobooks")
            for theme_name, items in PHOTOSHOOT_THEMES.items():
                try:
                    logger.info(f"Generating images for theme: {theme_name}")
                    # items = list of { 'prompt': str, 'count': int }
                    
                    expanded_prompts = []
                    for item in items:
                        base = item["prompt"]
                        how_many = item["count"]
                        # Add 'base' multiple times
                        for _ in range(how_many):
                            expanded_prompts.append(base)
                    
                    # Now pass expanded_prompts to your generate function
                    image_paths = self.generate_theme_images(
                        instance=instance,
                        model_path=remote_model_path,
                        theme_name=theme_name,
                        prompts=expanded_prompts
                    )
                    theme_images[theme_name] = image_paths
                    
                except Exception as e:
                    logger.error(f"Failed to generate theme {theme_name}: {str(e)}", exc_info=True)
                    # Skip this theme, continue with next
                    theme_images[theme_name] = []
                    continue
            
            # Download weights file
            logger.info("Downloading trained weights")
            temp_weights_path = self.base_path / f"{model_name}.safetensors"
            instance.download_file_scp(remote_model_path, str(temp_weights_path))
            
            return str(temp_weights_path), theme_images
            
        except Exception as e:
            logger.error(f"Training error for model {model_id}: {str(e)}")
            raise
            
        finally:
            # Cleanup
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
            
            if dataset_path and dataset_path.exists():
                try:
                    shutil.rmtree(dataset_path)
                except Exception as e:
                    logger.error(f"Cleanup error: {str(e)}")

    # def generate_images(self, model_id: int, user_id: int, model_path: str, prompts: List[str]) -> List[str]:
    #     """Generate images using provided model."""
    #     instance = None
    #     generation_dir = self.base_path / f"generation_{model_id}"
    #     temp_paths = []
        
    #     try:
    #         logger.info(f"Starting image generation for model {model_id}")
            
    #         # Create temporary generation directory
    #         if generation_dir.exists():
    #             shutil.rmtree(generation_dir)
    #         generation_dir.mkdir(parents=True)
            
    #         # Launch instance and setup
    #         instance = self.launch_instance()
    #         self._setup_generation_environment(instance)
            
    #         # Upload model weights
    #         logger.info("Uploading model weights")
    #         remote_model_path = f"{self.remote_base}/model.safetensors"
    #         instance.upload_file_scp(model_path, remote_model_path)
            
    #         # Generate images
    #         for idx, prompt in enumerate(prompts):
    #             output_path = f"{self.remote_base}/output/gen_{idx:03d}.png"
                
    #             # Run generation
    #             logger.info(f"Generating image {idx + 1}/{len(prompts)}")
    #             generation_cmd = f"""
    #             cd {self.remote_base} && \
    #             source venv/bin/activate && \
    #             export HF_TOKEN='{self.config["HF_TOKEN"]}' && \
    #             export PROMPT="{prompt}" && \
    #             export OUTPUT_PATH="{output_path}" && \
    #             python generate.py
    #             """
                
    #             result = instance.execute_command_ssh(generation_cmd)
                
    #             if "Error" in result or "Exception" in result:
    #                 raise Exception(f"Generation failed: {result}")
                
    #             # Download generated image
    #             local_path = generation_dir / f"gen_{idx:03d}.png"
    #             instance.download_file_scp(output_path, str(local_path))
    #             temp_paths.append(str(local_path))
                
    #         return temp_paths
            
    #     except Exception as e:
    #         logger.error(f"Generation error for model {model_id}: {str(e)}")
    #         raise
            
    #     finally:
    #         # Cleanup instance
    #         if instance:
    #             try:
    #                 logger.info("Terminating instance")
    #                 response = requests.post(
    #                     f"{self.base_url}/instance-operations/terminate",
    #                     headers={'Authorization': f'Bearer {self.api_key}'},
    #                     json={'instance_ids': [instance.instance_id]}
    #                 )
    #                 response.raise_for_status()
    #             except Exception as e:
    #                 logger.error(f"Failed to terminate instance: {str(e)}")