# server/services/ai_service.py

import json
import logging
import requests
import time
import concurrent.futures
from pathlib import Path
import shutil
from typing import Dict, Any, List, Optional, Tuple
import subprocess

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
        self.api_key = config["LAMBDA_API_KEY"]
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.instance_ip = None
        self.ssh_key_path = config["LAMBDA_SSH_KEY_PATH"]

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict:
        """Make request to Lambda API with better error handling."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30,
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
                return self._make_request("GET", f"instances/{self.instance_id}")
            except LambdaAPIException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)  # Exponential backoff

    def upload_file_scp(self, local_path: str, remote_path: str):
        """Upload file to instance using SCP."""
        instance_ip = self.instance_ip
        ssh_key = self.ssh_key_path
        try:
            scp_command = [
                "scp",
                "-i",
                ssh_key,
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                local_path,
                f"ubuntu@{instance_ip}:{remote_path}",
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
                "scp",
                "-i",
                ssh_key,
                "-o",
                "StrictHostKeyChecking=no",
                f"ubuntu@{instance_ip}:{remote_path}",
                local_path,
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
                "ssh",
                "-i",
                ssh_key,
                "-o",
                "StrictHostKeyChecking=no",
                f"ubuntu@{instance_ip}",
                command,
            ]
            logger.info(f"Executing command on {instance_ip}: {command}")
            result = subprocess.run(
                ssh_command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
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
                current_status = (
                    status_response.get("data", {}).get("status", "").strip().lower()
                )

                if current_status == "active":
                    self.instance_ip = status_response.get("data", {}).get("ip")
                    if not self.instance_ip:
                        raise LambdaAPIException("Instance IP not found")
                    logger.info(
                        f"Instance {self.instance_id} is active at {self.instance_ip}"
                    )
                    return
                elif current_status in ["error", "failed", "terminated"]:
                    raise LambdaAPIException(
                        f"Instance failed with status: {current_status}"
                    )

                time.sleep(5)
            except LambdaAPIException as e:
                logger.error(f"Error checking instance status: {str(e)}")
                raise

        raise LambdaAPIException("Instance startup timeout")


class AIService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.api_key = config["LAMBDA_API_KEY"]

        # Region and instance configuration
        self.regions = (
            config["LAMBDA_REGIONS"]
            if isinstance(config["LAMBDA_REGIONS"], list)
            else config["LAMBDA_REGIONS"].split(",")
        )
        self.instance_types = (
            config["LAMBDA_INSTANCE_TYPES"]
            if isinstance(config["LAMBDA_INSTANCE_TYPES"], list)
            else config["LAMBDA_INSTANCE_TYPES"].split(",")
        )

        # Local paths
        self.base_path = Path("/tmp/ai_training")
        self.datasets_path = self.base_path / "datasets"
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
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={
                            "region_name": region,
                            "instance_type_name": instance_type,
                            "quantity": 1,
                            "ssh_key_names": [self.config["LAMBDA_SSH_KEY_NAME"]],
                        },
                        timeout=30,
                    )

                    # Handle specific error cases
                    if response.status_code == 400:
                        error_data = response.json()
                        error_message = error_data.get("error", "")

                        if "insufficient-capacity" in error_message:
                            # No capacity in this region, try next region
                            logger.warning(
                                f"No capacity in {region} for {instance_type}"
                            )
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
                    instance_id = response.json()["data"]["instance_ids"][0]

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
                    logger.error(
                        f"Unexpected error launching {instance_type} in {region}: {str(e)}"
                    )
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
            git submodule update --init --recursive \
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

    def _pull_docker_image(self, instance: LambdaInstance):
        """Pull the pre-built Docker image on the remote instance."""
        try:
            logger.info(f"Pulling Docker image on instance {instance.instance_ip}")
            pull_cmd = "sudo docker pull amanzoni1/aitoolkit:stable-env"
            result = instance.execute_command_ssh(pull_cmd)
            logger.debug(f"Docker pull result: {result}")
        except Exception as e:
            logger.error(f"Failed to pull Docker image: {str(e)}")
            raise

    def prepare_dataset(
        self, model_id: int, file_info: List[Dict]
    ) -> Tuple[Path, List[str]]:
        """
        Prepare dataset locally.
        Return (local_dataset_path, list_of_files).
        Same as your original logic.
        """
        dataset_path = self.datasets_path / str(model_id)
        if dataset_path.exists():
            shutil.rmtree(dataset_path)
        dataset_path.mkdir(parents=True)

        processed_files = []

        try:
            for idx, info in enumerate(file_info):
                source_path = Path(info["path"])
                if not source_path.exists():
                    raise FileNotFoundError(f"Source file not found: {source_path}")

                # Copy and validate image
                image_path = dataset_path / f"image_{idx:04d}.jpg"
                shutil.copy2(source_path, image_path)
                processed_files.append(str(image_path))

                # Create caption
                caption_path = dataset_path / f"image_{idx:04d}.txt"
                with open(caption_path, "w") as f:
                    f.write("an image of [trigger]")

            return dataset_path, processed_files

        except Exception as e:
            logger.error(f"Dataset preparation failed: {str(e)}")
            if dataset_path.exists():
                shutil.rmtree(dataset_path)
            raise

    def generate_theme_images(
        self,
        instance: LambdaInstance,
        model_path: str,
        theme_name: str,
        prompts: List[str],
    ) -> List[str]:
        """Generate images for a theme in Docker container, referencing your original paths."""
        try:
            # Host folder where images will end up
            output_dir = f"{self.remote_base}/generated_images/{theme_name}"
            instance.execute_command_ssh(f"mkdir -p {output_dir}")

            # We'll set environment variables inside the container for HF_TOKEN, PROMPTS, OUTPUT_DIR, MODEL_PATH
            # then run `python generation/generate_batch.py`.
            docker_generation_cmd = f"""
            sudo docker run --gpus all --rm \
                -v {self.remote_workspace}:/app/ai-toolkit \
                -v {self.remote_base}/generated_images:/app/ai-toolkit/generated_images \
                --workdir /app/ai-toolkit \
                -e HF_TOKEN='{self.config["HF_TOKEN"]}' \
                -e PROMPTS='{json.dumps(prompts)}' \
                -e OUTPUT_DIR='/app/ai-toolkit/generated_images/{theme_name}' \
                -e MODEL_PATH='{model_path}' \
                amanzoni1/aitoolkit:stable-env \
                python generation/generate_batch.py
            """
            logger.info(f"Running generation in Docker: {docker_generation_cmd}")
            result = instance.execute_command_ssh(docker_generation_cmd)

            if "Error" in result or "Exception" in result:
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

            return local_paths

        except Exception as e:
            logger.error(f"Theme generation failed for {theme_name}: {str(e)}")
            raise

    def adapt_prompt(
        self, base_prompt: str, user_sex: str, user_age_years: float
    ) -> str:
        """
        Replace placeholders in the base_prompt with actual age and gender terms.
        For example:
        - If user_sex='M': GENDER_NOUN='boy', PRONOUN='he'
        - If user_sex='F': GENDER_NOUN='girl', PRONOUN='she'
        - Age might be '4 y.o.' if user_age_years=4, or '5 y.o.' etc.
        """
        # Basic gender logic
        if user_sex == "M":
            GENDER_NOUN = "boy"
            PRONOUN = "he"
        elif user_sex == "F":
            GENDER_NOUN = "girl"
            PRONOUN = "she"

        age_str = f"{int(user_age_years)} y.o."
        updated = base_prompt.replace("{GENDER_NOUN}", GENDER_NOUN)
        updated = updated.replace("{PRONOUN}", PRONOUN)
        updated = updated.replace("{AGE}", age_str)
        return updated

    def safe_int(self, value: Any, default: int) -> int:
        """
        Attempts to convert the value to an integer.
        Returns the default if value is None, an empty string, or cannot be converted.
        """
        if value in (None, ""):
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def train_model(
        self, model_id: int, user_id: int, training_config: Dict
    ) -> Tuple[str, Dict[str, List[str]]]:
        """Train model and generate initial photobooks.
        Returns:
            Tuple[str, Dict[str, List[str]]]: Tuple containing:
                - Path to trained model weights
                - Dictionary mapping theme names to lists of generated image paths
        """
        instance = None
        dataset_path = None
        temp_weights_path = None
        theme_images: Dict[str, List[str]] = {}

        try:
            logger.info(f"Starting model {model_id} training preparation")

            # Launch instance and prepare dataset concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                instance_future = executor.submit(self.launch_instance)
                dataset_future = executor.submit(
                    self.prepare_dataset, model_id, training_config["file_info"]
                )
                instance = instance_future.result()
                dataset_path, _ = dataset_future.result()

            # Set Up enviroment
            logger.info("Setting up training environment...")
            self._setup_training_environment(instance)

            # Pull Docker image
            logger.info("Pulling Docker image for stable environment.")
            self._pull_docker_image(instance)

            # Create dataset directory and upload dataset
            logger.info("Uploading dataset")
            remote_dataset_path = f"{self.remote_workspace}/dataset"
            instance.execute_command_ssh(f"mkdir -p {remote_dataset_path}")
            dataset_files = list(dataset_path.glob("*"))
            for file_path in dataset_files:
                instance.upload_file_scp(
                    str(file_path), f"{remote_dataset_path}/{file_path.name}"
                )

            # Update yaml with model name
            logger.info("Updating training configuration")
            model_name = f"model_{model_id}"
            update_config_cmd = f"""
            cd {self.remote_workspace} && \
            sed -i 's/name: ".*"/name: "{model_name}"/' base_training_short.yaml
            """
            instance.execute_command_ssh(update_config_cmd)

            # Run training
            logger.info("Starting training")
            docker_train_cmd = f"""
            sudo docker run --gpus all --rm \
                -v {self.remote_workspace}:/app/ai-toolkit \
                --workdir /app/ai-toolkit \
                -e HF_TOKEN='{self.config["HF_TOKEN"]}' \
                amanzoni1/aitoolkit:stable-env \
                python run.py base_training_short.yaml
            """
            train_result = instance.execute_command_ssh(docker_train_cmd)
            logger.debug(f"Training command output: {train_result}")

            if "Error" in train_result or "Exception" in train_result:
                log_result = instance.execute_command_ssh(
                    f"cat {self.remote_workspace}/training.log"
                )
                raise Exception(f"Training failed with log:\n{log_result}")

            # Download .safetensors
            remote_model_path = (
                f"{self.remote_workspace}/output/{model_name}/{model_name}.safetensors"
            )
            temp_weights_path = self.base_path / f"{model_name}.safetensors"
            logger.info(f"Downloading trained weights from {remote_model_path}")
            instance.download_file_scp(remote_model_path, str(temp_weights_path))

            # Generate photobooks for each theme
            logger.info("Generating photobooks")
            all_themes = self.config["PHOTOSHOOT_THEMES"]

            user_sex = training_config.get("sex", "M")
            age_years = self.safe_int(training_config.get("age_years"), 4)
            age_months = self.safe_int(training_config.get("age_months"), 0)
            user_age_years = age_years + (age_months / 12.0)

            for theme_name, theme_data in all_themes.items():
                theme_gender = theme_data["gender"]
                min_age = theme_data["age_min"]
                max_age = theme_data["age_max"]

                # Gender filter
                if theme_gender != "U" and theme_gender != user_sex:
                    logger.info(f"Skipping {theme_name} for user_sex={user_sex}")
                    continue

                # Age filter
                if user_age_years < min_age or user_age_years > max_age:
                    logger.info(f"Skipping {theme_name} due to age {user_age_years}")
                    continue

                try:
                    logger.info(f"Generating images for theme: {theme_name}")
                    prompt_items = theme_data["prompts"]
                    expanded_prompts: List[str] = []

                    for item in prompt_items:
                        base_prompt = item["prompt"]
                        how_many = item["count"]
                        for _ in range(how_many):
                            final_prompt = self.adapt_prompt(
                                base_prompt, user_sex, user_age_years
                            )
                            expanded_prompts.append(final_prompt)

                    image_paths = self.generate_theme_images(
                        instance=instance,
                        model_path=remote_model_path,
                        theme_name=theme_name,
                        prompts=expanded_prompts,
                    )
                    theme_images[theme_name] = image_paths

                except Exception as e:
                    logger.error(
                        f"Failed to generate theme {theme_name}: {str(e)}",
                        exc_info=True,
                    )
                    theme_images[theme_name] = []
                    continue

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
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={"instance_ids": [instance.instance_id]},
                    )
                    response.raise_for_status()
                except Exception as ex:
                    logger.error(f"Failed to terminate instance: {str(ex)}")

            if dataset_path and dataset_path.exists():
                try:
                    shutil.rmtree(dataset_path)
                except Exception as ex:
                    logger.error(f"Cleanup error: {str(ex)}")
