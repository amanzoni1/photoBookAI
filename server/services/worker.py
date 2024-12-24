# server/services/worker.py

import threading
import logging
from typing import Dict, Any, List
import time
from datetime import datetime
import signal
import shutil
from pathlib import Path
from queue import Queue
import io
from typing import Dict, Any, List, Optional, Tuple

from flask import Flask
from app import db
from models import JobStatus, TrainedModel, GeneratedImage, PhotoBook, UserImage
from config import PHOTOSHOOT_THEMES
from .queue import JobQueue
from .ai_service import AIService  

logger = logging.getLogger(__name__)

class WorkerService:
    def __init__(self, config: Dict[str, Any], app: Flask):
        self.config = config
        self.app = app  
        self.job_queue = JobQueue(config)
        self.should_stop = False
        self.workers: List[threading.Thread] = []
        
        # Worker status tracking
        self.worker_status = {}
        
        # Scaling settings
        self.min_workers = config.get('MIN_WORKERS', 2)
        self.max_workers = config.get('MAX_WORKERS', 10)
        self.scaling_threshold = config.get('SCALING_THRESHOLD', 5)
        
        # Retry settings
        self.max_retries = config.get('JOB_MAX_RETRIES', 3)
        
        # Alert queue
        self.alert_queue = Queue()
        self.alert_handlers = []
        
        # Start supervisor thread
        self.supervisor = threading.Thread(target=self._supervisor_loop, daemon=True)
        self.supervisor.start()
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Graceful shutdown"""
        logger.info("Initiating graceful shutdown...")
        self.should_stop = True
        self.stop_workers()

    def start_workers(self, num_workers: int = None):
        """Start worker threads"""
        num_workers = num_workers or self.min_workers
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(len(self.workers),),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            self.worker_status[worker.ident] = {
                'start_time': datetime.utcnow(),
                'jobs_processed': 0,
                'current_job': None
            }

    def stop_workers(self, num_workers: int = None):
        """Stop worker threads"""
        if num_workers is None:
            self.should_stop = True
            for worker in self.workers:
                worker.join()
            self.workers = []
            self.worker_status = {}
        else:
            workers_to_stop = self.workers[-num_workers:]
            self.workers = self.workers[:-num_workers]
            for worker in workers_to_stop:
                if worker.ident in self.worker_status:
                    del self.worker_status[worker.ident]

    def _supervisor_loop(self):
        """Monitor and scale workers"""
        while not self.should_stop:
            try:
                self._check_scaling()
                self._check_stuck_jobs()
                self._process_alerts()
                time.sleep(30)
            except Exception as e:
                logger.error(f"Supervisor error: {str(e)}")

    def _check_scaling(self):
        """Scale workers based on queue size"""
        try:
            queue_size = self.job_queue.get_queue_size()
            active_workers = len([w for w in self.workers if w.is_alive()])
            jobs_per_worker = queue_size / max(active_workers, 1)

            if jobs_per_worker > self.scaling_threshold and active_workers < self.max_workers:
                new_workers = min(
                    self.max_workers - active_workers,
                    (queue_size // self.scaling_threshold) - active_workers
                )
                if new_workers > 0:
                    logger.info(f"Scaling up {new_workers} workers")
                    self.start_workers(new_workers)
            
            elif jobs_per_worker < (self.scaling_threshold / 2) and active_workers > self.min_workers:
                to_remove = active_workers - max(
                    self.min_workers,
                    queue_size // self.scaling_threshold
                )
                if to_remove > 0:
                    logger.info(f"Scaling down {to_remove} workers")
                    self.stop_workers(to_remove)

        except Exception as e:
            logger.error(f"Scaling error: {str(e)}")

    def _check_stuck_jobs(self):
        """Check for stuck jobs and retry if needed"""
        try:
            stuck_jobs = self.job_queue.get_stuck_jobs()
            for job in stuck_jobs:
                retries = job.get('retries', 0)
                if retries < self.max_retries:
                    logger.info(f"Retrying stuck job {job['job_id']}")
                    self.job_queue.retry_job(job['job_id'])
                else:
                    logger.error(f"Job {job['job_id']} failed after {retries} retries")
                    self._send_alert({
                        'type': 'job_failed',
                        'job_id': job['job_id'],
                        'retries': retries,
                        'error': job.get('error')
                    })
        except Exception as e:
            logger.error(f"Stuck job check error: {str(e)}")

    def _worker_loop(self, worker_id: int):
        """Main worker loop with error handling"""
        logger.info(f"Starting worker {worker_id}")
        
        while not self.should_stop:
            try:
                # Check each queue type
                for queue_name, processor in [
                    (self.job_queue.training_queue, self._process_training_job),
                    (self.job_queue.generation_queue, self._process_generation_job),
                    (self.job_queue.photobook_queue, self._process_photobook_job)
                ]:
                    job = self.job_queue.dequeue_job(queue_name)
                    if job:
                        self._process_job(job, processor)
                        break
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")

    def _send_alert(self, alert_data: Dict[str, Any]):
        """Send alert to handlers"""
        self.alert_queue.put(alert_data)

    def _process_alerts(self):
        """Process queued alerts"""
        while not self.alert_queue.empty():
            alert = self.alert_queue.get()
            for handler in self.alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler error: {str(e)}")

    def add_alert_handler(self, handler):
        """Add alert handler function"""
        self.alert_handlers.append(handler)

    def get_status(self) -> Dict[str, Any]:
        """Get worker service status"""
        return {
            'active_workers': len([w for w in self.workers if w.is_alive()]),
            'worker_status': self.worker_status,
            'queue_size': self.job_queue.get_queue_size()
        }

    def _process_job(self, job: Dict[str, Any], processor):
        """Process job with error handling"""
        job_id = job['job_id']
        thread_id = threading.current_thread().ident
        self.worker_status[thread_id]['current_job'] = job_id
        
        try:
            # Run within application context
            with self.app.app_context():
                processor(job)
            self.worker_status[thread_id]['jobs_processed'] += 1
        except Exception as e:
            logger.error(f"Job processing error: {str(e)}")
            if job.get('retries', 0) < self.max_retries:
                self.job_queue.retry_job(job_id)
            else:
                self._send_alert({
                    'type': 'job_failed',
                    'job_id': job_id,
                    'error': str(e)
                })
        finally:
            self.worker_status[thread_id]['current_job'] = None


    def _get_theme_prompts(self, theme_name: str) -> List[str]:
        """Get predefined prompts for a theme"""
        from config import PHOTOSHOOT_THEMES
        
        if theme_name not in PHOTOSHOOT_THEMES:
            raise ValueError(f"Invalid theme name: {theme_name}")
            
        # Get base prompts for theme
        theme_prompts = PHOTOSHOOT_THEMES[theme_name]
        
        # Add trigger word to prompts
        return [f"{prompt}, p3r5onTr1g style" for prompt in theme_prompts]

    def _get_trained_model_weights(self, model_id: int, training_config: Dict) -> Tuple[str, Dict[str, List[str]]]:
        """Get the path to trained model weights and theme images using AI service"""
        try:
            # Initialize AI service with config
            ai_service = AIService(self.config)
            
            # Run training and get the local weights file path and theme images
            return ai_service.train_model(
                model_id=model_id,
                user_id=training_config['user_id'],
                training_config=training_config
            )
                
        except Exception as e:
            logger.error(f"Training error: {str(e)}")
            raise

    def _save_initial_photobook(self, user_id: int, model_id: int, theme_name: str, image_paths: List[str]) -> None:
        """Helper function to save initial photobook and its images"""
        storage_service = self.config['storage_service']
        theme_prompts = PHOTOSHOOT_THEMES[theme_name]
        
        try:
            # Create photobook entry
            photobook = PhotoBook(
                user_id=user_id,
                model_id=model_id,
                name=f"Initial Photoshoot - {theme_name}",
                theme_name=theme_name,
                status=JobStatus.COMPLETED,
                is_unlocked=False
            )
            db.session.add(photobook)
            db.session.commit()
            
            # Save each image with its prompt
            for idx, (image_path, prompt) in enumerate(zip(image_paths, theme_prompts)):
                try:
                    # First save the image and get storage location
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                        location = storage_service.save_photobook_image(
                            user_id=user_id,
                            photobook_id=photobook.id,
                            image_data=image_data,
                            image_number=idx + 1,
                            prompt=f"{prompt}, p3r5onTr1g style"
                        )
                        # Add storage location to session and commit to get ID
                        db.session.add(location)
                        db.session.commit()
                        
                        # Now create GeneratedImage with the storage location ID
                        image = GeneratedImage(
                            user_id=user_id,
                            model_id=model_id,
                            photobook_id=photobook.id,
                            storage_location_id=location.id,  
                            prompt=f"{prompt}, p3r5onTr1g style"
                        )
                        db.session.add(image)
                        db.session.commit()
                        
                except Exception as e:
                    logger.error(f"Failed to save image {idx} for theme {theme_name}: {str(e)}")
                    continue
                    
            logger.info(f"Successfully saved initial photobook for theme {theme_name}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save initial photobook for theme {theme_name}: {str(e)}")
            raise

    def _get_generated_images(self, model_id: int, generation_config: Dict) -> List[str]:
        """Get generated images using AI service"""
        try:
            # Initialize AI service with config
            ai_service = AIService(self.config)
            
            # Handle both single prompt and multiple prompts cases
            if 'prompts' in generation_config:
                # Multiple prompts case (photobook)
                prompts = generation_config['prompts']
            elif 'prompt' in generation_config:
                # Single prompt case (single image generation)
                prompts = [generation_config['prompt']]
            else:
                raise ValueError("No prompts provided in generation config")
            
            # Generate images and get the local paths
            image_paths = ai_service.generate_images(
                model_id=model_id,
                user_id=generation_config['user_id'],
                model_path=generation_config['model_weights_path'],
                prompts=prompts
            )
            
            return image_paths
                
        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            raise

    def _process_training_job(self, job: Dict[str, Any]):
        """Process model training job"""
        job_id = job['job_id']
        logger.info(f"Processing training job {job_id}")
        model = None
        temp_dir = Path(job['payload']['temp_dir'])
        
        try:
            self.job_queue.update_job_status(job_id, JobStatus.PROCESSING)
            
            # Get data from payload
            model_id = job['payload']['model_id']
            user_id = job['user_id']
            
            # Update model status
            with db.session.begin_nested():
                model = TrainedModel.query.get(model_id)
                model.training_started_at = datetime.utcnow()
                model.status = JobStatus.PROCESSING
                db.session.add(model)
            
            db.session.commit()
            
            # Run training using AI service and get both weights and theme images
            logger.info(f"Starting model training for model_id {model_id}")
            weights_file_path, theme_images = self._get_trained_model_weights(
                model_id=model_id,
                training_config={
                    'user_id': user_id,
                    'file_info': job['payload']['file_info']
                }
            )
            
            # Upload model weights
            logger.info(f"Uploading model weights for model {model_id}")
            storage_service = self.config['storage_service']
            with open(weights_file_path, 'rb') as f:
                weights_location = storage_service.upload_model_weights(
                    user_id=user_id,
                    model_id=model_id,
                    weights_file=f,
                    version='1.0'
                )
                
                db.session.add(weights_location)
                db.session.commit()

                if weights_location.id is None:
                    logger.error("Failed to get weights storage location ID after committing.")
                    raise Exception("Weights storage location ID is None after commit.")
            
            # Cleanup local weights file
            if Path(weights_file_path).exists():
                Path(weights_file_path).unlink()
            
            # Save initial photobooks
            n_themes = len(theme_images)
            logger.info(f"Processing {n_themes} initial photobooks for model {model_id}")
            
            theme_images_dir = None
            for theme_name, image_paths in theme_images.items():
                try:
                    if not image_paths:
                        logger.warning(f"Empty image paths for theme {theme_name}")
                        continue
                        
                    logger.info(f"Saving photobook for theme {theme_name} with {len(image_paths)} images")
                    theme_images_dir = Path(image_paths[0]).parent.parent  # Get base theme_images dir
                    self._save_initial_photobook(user_id, model_id, theme_name, image_paths)
                except Exception as theme_error:
                    logger.error(f"Failed to save theme {theme_name}: {str(theme_error)}", exc_info=True)
                    continue
            
            # Update model status
            with db.session.begin_nested():
                model.status = JobStatus.COMPLETED
                model.weights_location_id = weights_location.id
                model.training_completed_at = datetime.utcnow()
                db.session.add(model)
            
            db.session.commit()
            
            # Update job status
            self.job_queue.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                {
                    'model_id': model_id,
                    'weights_location_id': weights_location.id
                }
            )
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Training error: {str(e)}")
            
            if model:
                try:
                    with db.session.begin_nested():
                        model.status = JobStatus.FAILED
                        model.error_message = str(e)
                        db.session.add(model)
                    db.session.commit()
                except Exception as ex:
                    logger.error(f"Failed to update model status to FAILED: {str(ex)}")
                    
            self.job_queue.update_job_status(
                job_id,
                JobStatus.FAILED,
                {'error': str(e)}
            )
        
        finally:
            # Cleanup all temporary directories
            cleanup_paths = [
                temp_dir,
                theme_images_dir
            ]
            
            for path in cleanup_paths:
                if path and path.exists():
                    try:
                        shutil.rmtree(path)
                    except Exception as cleanup_error:
                        logger.error(f"Failed to cleanup {path}: {cleanup_error}")













   


    def _process_photobook_job(self, job: Dict[str, Any]):
        """Process themed photoshoot generation"""
        job_id = job['job_id']
        logger.info(f"Processing photobook job {job_id}")
        photobook = None
        
        try:
            self.job_queue.update_job_status(job_id, JobStatus.PROCESSING)
            
            # Get data from payload
            photobook_id = job['payload']['photobook_id']
            model_id = job['payload']['model_id']
            user_id = job['user_id']
            prompts = job['payload']['prompts']  # Use prompts directly from payload
            model_weights_path = job['payload']['model_weights_path']
            
            # Get storage service
            storage_service = self.config['storage_service']
            
            # Update photobook status
            with db.session.begin_nested():
                photobook = PhotoBook.query.get(photobook_id)
                photobook.status = JobStatus.PROCESSING
                db.session.add(photobook)
            db.session.commit()
            
            # Add trigger word to prompts
            themed_prompts = [f"{prompt}, p3r5onTr1g style" for prompt in prompts]
            
            # Generate images
            image_paths = self._get_generated_images(
                model_id=model_id,
                generation_config={
                    'user_id': user_id,
                    'model_weights_path': model_weights_path,
                    'prompts': themed_prompts
                }
            )

            # Save images
            generated_images = []
            for idx, (image_path, prompt) in enumerate(zip(image_paths, themed_prompts)):
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                    
                    location = storage_service.save_photobook_image(
                        user_id=user_id,
                        photobook_id=photobook_id,
                        image_data=image_data,
                        image_number=idx + 1,
                        prompt=prompt
                    )
                    
                    image = GeneratedImage(
                        user_id=user_id,
                        model_id=model_id,
                        photobook_id=photobook_id,
                        storage_location_id=location.id,
                        prompt=prompt
                    )
                    db.session.add(image)
                    generated_images.append(image)
            
            # Update status and unlock the photobook
            with db.session.begin_nested():
                photobook.status = JobStatus.COMPLETED
                photobook.is_unlocked = True  # Unlock the photobook after successful generation
                db.session.add(photobook)
            db.session.commit()
            
            # Return result
            self.job_queue.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                {
                    'photobook_id': photobook_id,
                    'images': [
                        {
                            'id': img.id,
                            'url': storage_service.get_public_url(img.storage_location)
                        } for img in generated_images
                    ]
                }
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Photobook generation error: {str(e)}")
            if photobook:
                try:
                    with db.session.begin_nested():
                        photobook.status = JobStatus.FAILED
                        photobook.error_message = str(e)
                        db.session.add(photobook)
                    db.session.commit()
                except Exception as ex:
                    logger.error(f"Failed to update photobook status to FAILED: {str(ex)}")
            
            self.job_queue.update_job_status(
                job_id,
                JobStatus.FAILED,
                {'error': str(e)}
            )

    def _process_generation_job(self, job: Dict[str, Any]):
        """Process single image generation job"""
        job_id = job['job_id']
        logger.info(f"Processing generation job {job_id}")
        
        try:
            self.job_queue.update_job_status(job_id, JobStatus.PROCESSING)
            
            # Get data from payload - match route parameters
            model_id = job['payload']['model_id']
            user_id = job['user_id']
            
            # Prepare generation config
            generation_config = {
                'user_id': user_id,
                'model_weights_path': job['payload']['model_weights_path'],
                'prompt': job['payload']['prompt'],
                'parameters': job['payload'].get('parameters', {}),
            }
            
            # Get storage service
            storage_service = self.config['storage_service']
            
            # Generate image
            image_paths = self._get_generated_images(
                model_id=model_id,
                generation_config=generation_config
            )
            
            # Save generated images
            generated_images = []
            for idx, image_path in enumerate(image_paths):
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                location = storage_service.save_generated_image(
                    user_id=user_id,
                    model_id=model_id,
                    image_data=image_data,
                    filename=f"generated_{idx}.png",
                    prompt=generation_config['prompt'],
                    generation_params=generation_config['parameters']
                )
                
                image = GeneratedImage(
                    user_id=user_id,
                    model_id=model_id,
                    storage_location_id=location.id,
                    prompt=generation_config['prompt'],
                    generation_params=generation_config['parameters']
                )
                db.session.add(image)
                generated_images.append(image)
            
            db.session.commit()
            
            # Update job status
            self.job_queue.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                {
                    'generated_images': [
                        {
                            'id': img.id,
                            'url': storage_service.get_public_url(img.storage_location)
                        } for img in generated_images
                    ]
                }
            )
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Generation error: {str(e)}")
            self.job_queue.update_job_status(
                job_id,
                JobStatus.FAILED,
                {'error': str(e)}
            )

