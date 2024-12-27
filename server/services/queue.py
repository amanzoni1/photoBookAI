# server/services/queue.py

from enum import Enum
import json
import redis
import logging
from typing import Dict, Any, Optional, List 
from datetime import datetime
from models import JobStatus

logger = logging.getLogger(__name__)

class JobType(Enum):
    MODEL_TRAINING = "model_training"
    IMAGE_GENERATION = "image_generation"
    PHOTOBOOK_GENERATION = "photobook_generation"

class JobQueue:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = redis.Redis(
            host=config.get('REDIS_HOST', 'localhost'),
            port=config.get('REDIS_PORT', 6379),
            db=config.get('REDIS_JOB_DB', 1)  # Use different DB than token manager
        )
        
        # Queue names
        self.training_queue = 'training_jobs'
        self.photobook_queue = 'photobook_jobs'
        self.generation_queue = 'generation_jobs'
        
        # Status hash
        self.job_status_hash = 'job_statuses'

    def enqueue_job(self, job_type: JobType, user_id: int, payload: Dict[str, Any]) -> str:
        try:
            job_id = f"{job_type.value}_{user_id}_{datetime.utcnow().timestamp()}"
            
            job_data = {
                'job_id': job_id,
                'job_type': job_type.value,
                'user_id': user_id,
                'status': JobStatus.PENDING.value,
                'created_at': datetime.utcnow().isoformat(),
                'payload': payload
            }
            
            # Store job data
            self.redis_client.hset(
                self.job_status_hash,
                job_id,
                json.dumps(job_data)
            )
            
            # Select appropriate queue
            queue_name = {
                JobType.MODEL_TRAINING: self.training_queue,
                JobType.IMAGE_GENERATION: self.generation_queue,
                JobType.PHOTOBOOK_GENERATION: self.photobook_queue
            }[job_type]
            
            self.redis_client.rpush(queue_name, job_id)
            
            logger.info(f"Enqueued job {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error enqueuing job: {str(e)}")
            raise

    def dequeue_job(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get next job from queue"""
        try:
            # Get job ID using blocking pop (waits for new jobs)
            result = self.redis_client.blpop(queue_name, timeout=1)
            if not result:
                return None
                
            _, job_id = result
            job_id = job_id.decode('utf-8')
            
            # Get job data
            job_data = self.redis_client.hget(self.job_status_hash, job_id)
            if not job_data:
                return None
                
            return json.loads(job_data)
            
        except Exception as e:
            logger.error(f"Error dequeuing job: {str(e)}")
            return None
        
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve all jobs from the job_status_hash."""
        try:
            all_jobs = self.redis_client.hgetall(self.job_status_hash)
            return [json.loads(job_data) for job_data in all_jobs.values()]
        except Exception as e:
            logger.error(f"Error getting all jobs: {str(e)}")
            return [] 

    def update_job_status(self, 
                         job_id: str, 
                         status: JobStatus, 
                         result: Optional[Dict] = None) -> bool:
        """Update job status and result"""
        try:
            job_data = self.redis_client.hget(self.job_status_hash, job_id)
            if not job_data:
                return False
                
            job_data = json.loads(job_data)
            job_data.update({
                'status': status.value,
                'updated_at': datetime.utcnow().isoformat(),
                'result': result
            })
            
            self.redis_client.hset(
                self.job_status_hash,
                job_id,
                json.dumps(job_data)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")
            return False

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and data"""
        try:
            job_data = self.redis_client.hget(self.job_status_hash, job_id)
            return json.loads(job_data) if job_data else None
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return None
        
    def get_queue_size(self) -> int:
        """Get total number of pending jobs"""
        try:
            training_size = self.redis_client.llen(self.training_queue)
            generation_size = self.redis_client.llen(self.generation_queue)
            return training_size + generation_size
        except Exception as e:
            logger.error(f"Error getting queue size: {str(e)}")
            return 0

    def get_stuck_jobs(self) -> list:
        """Get jobs that have been processing too long"""
        try:
            stuck_jobs = []
            all_jobs = self.redis_client.hgetall(self.job_status_hash)
            
            for _, job_data in all_jobs.items():
                job = json.loads(job_data)
                if job['status'] == JobStatus.PROCESSING.value:
                    started_at_str = job.get('started_at')
                    if not started_at_str:
                        continue
                    try:
                        started_at = datetime.fromisoformat(started_at_str)
                    except ValueError:
                        logger.error(f"Invalid date format for job {job['job_id']}")
                        continue
                    if (datetime.utcnow() - started_at).total_seconds() > 3600:  # 1 hour
                        stuck_jobs.append(job)
            
            return stuck_jobs
        except Exception as e:
            logger.error(f"Error getting stuck jobs: {str(e)}")
            return []

    def retry_job(self, job_id: str) -> bool:
        """Reset job status and requeue"""
        try:
            job_data = self.redis_client.hget(self.job_status_hash, job_id)
            if not job_data:
                return False
            
            job = json.loads(job_data)
            job['status'] = JobStatus.PENDING.value
            job['retries'] = job.get('retries', 0) + 1
            
            # Update job data
            self.redis_client.hset(
                self.job_status_hash,
                job_id,
                json.dumps(job)
            )
            
            # Re-queue job
            queue = self.training_queue if job['job_type'] == JobType.MODEL_TRAINING.value else self.generation_queue
            self.redis_client.rpush(queue, job_id)
            
            return True
        except Exception as e:
            logger.error(f"Error retrying job: {str(e)}")
            return False

    def get_user_jobs(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all jobs for a specific user."""
        try:
            all_jobs = self.redis_client.hgetall(self.job_status_hash)
            user_jobs = [
                json.loads(job_data) for job_data in all_jobs.values()
                if job_data and json.loads(job_data).get('user_id') == user_id
            ]
            return user_jobs
        except Exception as e:
            logger.error(f"Error getting jobs for user {user_id}: {str(e)}")
            return [] 

    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the status hash"""
        try:
            # Delete job from status hash
            return self.redis_client.hdel(self.job_status_hash, job_id) > 0
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {str(e)}")
            return False

    def reset_all_jobs(self) -> bool:
        """Reset all job statuses by clearing the status hash"""
        try:
            # Clear job status hash
            self.redis_client.delete(self.job_status_hash)
            # Clear all queues
            self.redis_client.delete(self.training_queue)
            self.redis_client.delete(self.generation_queue)
            self.redis_client.delete(self.photobook_queue)
            logger.info("All job statuses and queues reset successfully")
            return True
        except Exception as e:
            logger.error(f"Error resetting jobs: {str(e)}")
            return False