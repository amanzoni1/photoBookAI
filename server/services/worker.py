# server/services/worker.py

import threading
import logging
from typing import Dict, Any
import time
from datetime import datetime

from .queue import JobQueue, JobType, JobStatus

logger = logging.getLogger(__name__)

class WorkerService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.job_queue = JobQueue(config)
        self.should_stop = False
        self.workers = []
        
    def start_workers(self, num_workers: int = 2):
        """Start worker threads"""
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
    
    def stop_workers(self):
        """Stop all workers"""
        self.should_stop = True
        for worker in self.workers:
            worker.join()
    
    def _worker_loop(self, worker_id: int):
        """Main worker loop"""
        logger.info(f"Starting worker {worker_id}")
        
        while not self.should_stop:
            try:
                # Check training queue
                job = self.job_queue.dequeue_job(self.job_queue.training_queue)
                if job:
                    self._process_training_job(job)
                    continue
                
                # Check generation queue
                job = self.job_queue.dequeue_job(self.job_queue.generation_queue)
                if job:
                    self._process_generation_job(job)
                    continue
                
                # No jobs, sleep briefly
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
    
    def _process_training_job(self, job: Dict[str, Any]):
        """Process model training job"""
        try:
            job_id = job['job_id']
            logger.info(f"Processing training job {job_id}")
            
            # Update status to processing
            self.job_queue.update_job_status(job_id, JobStatus.PROCESSING)
            
            # TODO: AI training code
            
            # For now, simulate processing
            time.sleep(5)
            
            # Update status to completed
            self.job_queue.update_job_status(
                job_id, 
                JobStatus.COMPLETED,
                {'model_path': f'models/{job_id}/model.safetensors'}
            )
            
        except Exception as e:
            logger.error(f"Training job {job_id} failed: {str(e)}")
            self.job_queue.update_job_status(
                job_id,
                JobStatus.FAILED,
                {'error': str(e)}
            )
    
    def _process_generation_job(self, job: Dict[str, Any]):
        """Process image generation job"""
        try:
            job_id = job['job_id']
            logger.info(f"Processing generation job {job_id}")
            
            self.job_queue.update_job_status(job_id, JobStatus.PROCESSING)
            
            # TODO: AI generation code
                        
            # Simulate processing
            time.sleep(2)
            
            self.job_queue.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                {'image_path': f'generated/{job_id}/image.png'}
            )
            
        except Exception as e:
            logger.error(f"Generation job {job_id} failed: {str(e)}")
            self.job_queue.update_job_status(
                job_id,
                JobStatus.FAILED,
                {'error': str(e)}
            )