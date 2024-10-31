# server/services/cache.py

import os
import shutil
from typing import Optional
import threading
import time
import logging
from pathlib import Path
import hashlib

from models import StorageLocation

logger = logging.getLogger(__name__)

class ModelCache:
    def __init__(self, cache_dir: str, storage_service, max_size_gb: int = 50):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        self.lock = threading.Lock()
        self.storage_service = storage_service 
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self.cleanup_thread.start()
    
    def get_or_cache(self, storage_location: StorageLocation) -> str:
        """Get model from cache or download it"""
        model_hash = self._get_location_hash(storage_location)
        cache_path = self.cache_dir / model_hash
        
        with self.lock:
            if cache_path.exists():
                # Update access time
                os.utime(cache_path, None)
                return str(cache_path)
            
            # Download model
            try:
                temp_path = cache_path.with_suffix('.tmp')
                
                # Ensure enough space
                self._ensure_space(storage_location.metadata_json.get('size', 0))
                
                # Download to temporary file
                with open(temp_path, 'wb') as f:
                    self.storage_service.download_file(storage_location, f)
                
                # Move to final location
                temp_path.rename(cache_path)
                
                return str(cache_path)
                
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise Exception(f"Cache error: {str(e)}")
    
    def _cleanup_loop(self):
        """Periodically clean up old cache files"""
        while True:
            try:
                self._cleanup_cache()
            except Exception as e:
                logger.error(f"Cache cleanup error: {str(e)}")
            time.sleep(3600)  # Check every hour
    
    def _cleanup_cache(self):
        """Remove least recently used files if cache is too large"""
        with self.lock:
            # Get all cache files with their access times
            files = []
            total_size = 0
            
            for path in self.cache_dir.iterdir():
                if path.is_file() and not path.name.endswith('.tmp'):
                    size = path.stat().st_size
                    atime = path.stat().st_atime
                    files.append((path, size, atime))
                    total_size += size
            
            # Sort by access time (oldest first)
            files.sort(key=lambda x: x[2])
            
            # Remove files until we're under the limit
            while total_size > self.max_size_bytes and files:
                path, size, _ = files.pop(0)
                try:
                    path.unlink()
                    total_size -= size
                    logger.info(f"Removed cached model: {path}")
                except Exception as e:
                    logger.error(f"Error removing cache file {path}: {str(e)}")
    
    def _ensure_space(self, needed_bytes: int):
        """Ensure enough space for new file"""
        with self.lock:
            # Get current cache size
            total_size = sum(f.stat().st_size for f in self.cache_dir.iterdir() if f.is_file())
            
            if total_size + needed_bytes > self.max_size_bytes:
                self._cleanup_cache()
    
    def _get_location_hash(self, location: StorageLocation) -> str:
        """Generate unique hash for storage location"""
        return hashlib.sha256(
            f"{location.bucket}/{location.path}".encode()
        ).hexdigest()