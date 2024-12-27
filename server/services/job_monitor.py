# server/services/job_monitor.py

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import threading
import time
from collections import defaultdict

from .queue import JobQueue, JobStatus

logger = logging.getLogger(__name__)

class JobMonitor:
    def __init__(self, config: Dict[str, Any], job_queue: JobQueue):
        self.config = config
        self.job_queue = job_queue
        self.metrics = defaultdict(int)
        self.cleanup_interval = config.get('JOB_CLEANUP_HOURS', 24)
        self.retention_days = config.get('JOB_RETENTION_DAYS', 7)
        
        # Start monitoring thread
        self.should_stop = False
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_loop(self):
        """Background monitoring and cleanup"""
        while not self.should_stop:
            try:
                self._update_metrics()
                self._cleanup_old_jobs()
                time.sleep(600)  # Check every 10 minutes
            except Exception as e:
                logger.error(f"Monitor error: {str(e)}")
                time.sleep(60)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Safely parse ISO date string"""
        try:
            return datetime.fromisoformat(date_str) if date_str else None
        except (ValueError, TypeError):
            return None
    
    def _update_metrics(self):
        """Update job metrics"""
        try:
            # Reset metrics
            self.metrics.clear()
            self.metrics.update({
                'total_jobs': 0,
                'pending_jobs': 0,
                'processing_jobs': 0,
                'completed_jobs': 0,
                'failed_jobs': 0,
                'avg_processing_time': 0,
                'last_updated': datetime.utcnow().isoformat()
            })
            
            processing_times = []
            jobs = self.job_queue.get_all_jobs()
            self.metrics['total_jobs'] = len(jobs)
            
            for job in jobs:
                status = job.get('status')
                if not status:
                    continue
                
                # Update status counts
                if status == JobStatus.PENDING.value:
                    self.metrics['pending_jobs'] += 1
                elif status == JobStatus.PROCESSING.value:
                    self.metrics['processing_jobs'] += 1
                elif status == JobStatus.COMPLETED.value:
                    self.metrics['completed_jobs'] += 1
                    # Calculate processing time for completed jobs
                    start_time = self._parse_date(job.get('started_at'))
                    end_time = self._parse_date(job.get('completed_at'))
                    if start_time and end_time:
                        processing_times.append((end_time - start_time).total_seconds())
                elif status == JobStatus.FAILED.value:
                    self.metrics['failed_jobs'] += 1
            
            # Calculate average processing time
            if processing_times:
                self.metrics['avg_processing_time'] = sum(processing_times) / len(processing_times)
            
            logger.info(f"Updated metrics: {dict(self.metrics)}")
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}", exc_info=True)
    
    def _cleanup_old_jobs(self):
        """Clean up completed/failed jobs older than retention period"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
            cleaned_count = 0
            
            for job in self.job_queue.get_all_jobs():
                try:
                    # Only cleanup completed or failed jobs
                    if job.get('status') not in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
                        continue
                    
                    # Check completion date
                    completed_at = self._parse_date(job.get('completed_at'))
                    if not completed_at:
                        completed_at = self._parse_date(job.get('updated_at'))
                    
                    if completed_at and completed_at < cutoff:
                        if self.job_queue.remove_job(job['job_id']):
                            cleaned_count += 1
                            
                except Exception as e:
                    logger.error(f"Error cleaning up job {job.get('job_id')}: {str(e)}")
                    continue
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old jobs")
                
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}", exc_info=True)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return dict(self.metrics)
    
    def get_job_stats(self, user_id: int) -> Dict[str, Any]:
        """Get job statistics for a user"""
        try:
            user_jobs = self.job_queue.get_user_jobs(user_id)
            
            stats = defaultdict(int)
            processing_times = []
            
            for job in user_jobs:
                stats['total_jobs'] += 1
                stats[f"{job['status']}_jobs"] += 1
                
                if job['status'] == JobStatus.COMPLETED.value:
                    if job.get('started_at') and job.get('completed_at'):
                        start = datetime.fromisoformat(job['started_at'])
                        end = datetime.fromisoformat(job['completed_at'])
                        processing_times.append((end - start).total_seconds())
            
            if processing_times:
                stats['avg_processing_time'] = sum(processing_times) / len(processing_times)
            
            return dict(stats)
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {}

    def stop(self):
        """Stop monitoring"""
        self.should_stop = True
        self.monitor_thread.join()