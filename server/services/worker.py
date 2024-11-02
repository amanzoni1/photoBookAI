# server/services/worker.py

import threading
import logging
from typing import Dict, Any, List
import time
from datetime import datetime
import signal
from queue import Queue
from .queue import JobStatus, JobQueue

logger = logging.getLogger(__name__)

class WorkerService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
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
                # Check training queue
                job = self.job_queue.dequeue_job(self.job_queue.training_queue)
                if job:
                    self._process_job(job, self._process_training_job)
                    continue
                
                # Check generation queue
                job = self.job_queue.dequeue_job(self.job_queue.generation_queue)
                if job:
                    self._process_job(job, self._process_generation_job)
                    continue
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")

    def _process_job(self, job: Dict[str, Any], processor):
        """Process job with error handling"""
        job_id = job['job_id']
        thread_id = threading.current_thread().ident
        self.worker_status[thread_id]['current_job'] = job_id
        
        try:
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

    def _process_training_job(self, job: Dict[str, Any]):
        """Process model training job"""
        job_id = job['job_id']
        logger.info(f"Processing training job {job_id}")
        
        self.job_queue.update_job_status(job_id, JobStatus.PROCESSING)
        
        # TODO: Implement actual training logic here
        time.sleep(5)  # Simulate processing
        
        self.job_queue.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            {'model_path': f'models/{job_id}/model.safetensors'}
        )

    def _process_generation_job(self, job: Dict[str, Any]):
        """Process image generation job"""
        job_id = job['job_id']
        logger.info(f"Processing generation job {job_id}")
        
        self.job_queue.update_job_status(job_id, JobStatus.PROCESSING)
        
        # TODO: Implement actual generation logic here
        time.sleep(2)  # Simulate processing
        
        self.job_queue.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            {'image_path': f'generated/{job_id}/image.png'}
        )

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
    










#     def _process_training_job(self, job: Dict[str, Any]):
#     """Process model training job"""
#     job_id = job['job_id']
#     logger.info(f"Processing training job {job_id}")
    
#     try:
#         self.job_queue.update_job_status(job_id, JobStatus.PROCESSING)
        
#         # Get data from payload
#         model_id = job['payload']['model_id']
#         user_id = job['user_id']
        
#         # TODO: Actual model training here
        
#         # Save model weights using storage service
#         storage_service = get_storage_service()
#         weights_data = b''  # This would be your actual model weights
        
#         weights_location = storage_service.upload_model_weights(
#             user_id=user_id,
#             model_id=model_id,
#             weights_file=io.BytesIO(weights_data),
#             version='1.0'
#         )
        
#         # Update model record
#         model = TrainedModel.query.get(model_id)
#         model.status = JobStatus.COMPLETED
#         model.weights_location_id = weights_location.id
#         model.training_completed_at = datetime.utcnow()
#         db.session.commit()
        
#         # Return the result
#         self.job_queue.update_job_status(
#             job_id,
#             JobStatus.COMPLETED,
#             {
#                 'model_id': model_id,
#                 'weights_location_id': weights_location.id
#             }
#         )
        
#     except Exception as e:
#         logger.error(f"Training error: {str(e)}")
#         self.job_queue.update_job_status(
#             job_id,
#             JobStatus.FAILED,
#             {'error': str(e)}
#         )

# def _process_generation_job(self, job: Dict[str, Any]):
#     """Process image generation job"""
#     job_id = job['job_id']
#     logger.info(f"Processing generation job {job_id}")
    
#     try:
#         self.job_queue.update_job_status(job_id, JobStatus.PROCESSING)
        
#         # Get data from payload
#         model_id = job['payload']['model_id']
#         user_id = job['user_id']
#         prompt = job['payload']['prompt']
#         num_images = job['payload']['num_images']
        
#         # TODO: Actual image generation here
        
#         generated_images = []
#         storage_service = get_storage_service()
        
#         for i in range(num_images):
#             image_data = b''  # This would be your actual generated image
            
#             # Save generated image
#             location = storage_service.save_generated_image(
#                 user_id=user_id,
#                 model_id=model_id,
#                 image_data=image_data,
#                 filename=f"generated_{i}.png"
#             )
            
#             # Create record
#             image = GeneratedImage(
#                 user_id=user_id,
#                 model_id=model_id,
#                 storage_location_id=location.id,
#                 prompt=prompt,
#                 generation_params=job['payload'].get('parameters', {})
#             )
#             db.session.add(image)
#             generated_images.append(image)
            
#         db.session.commit()
        
#         # Return the result
#         self.job_queue.update_job_status(
#             job_id,
#             JobStatus.COMPLETED,
#             {
#                 'generated_images': [
#                     {
#                         'id': img.id,
#                         'url': storage_service.get_public_url(img.storage_location)
#                     } for img in generated_images
#                 ]
#             }
#         )
        
#     except Exception as e:
#         logger.error(f"Generation error: {str(e)}")
#         self.job_queue.update_job_status(
#             job_id,
#             JobStatus.FAILED,
#             {'error': str(e)}
#         )