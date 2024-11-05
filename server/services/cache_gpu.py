# server/services/cache_gpu.py

import paramiko
import logging
from pathlib import Path
import json
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GPUModelCache:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config['GPU_DROPLET_HOST']
        self.port = config['GPU_DROPLET_PORT']
        self.username = config['GPU_DROPLET_USERNAME']
        self.key_path = config['GPU_DROPLET_SSH_KEY_PATH']
        
        # Cache settings
        self.cache_path = config.get('GPU_CACHE_PATH', '/app/model_cache')
        self.max_size = config.get('GPU_CACHE_SIZE_GB', 50) * 1024 * 1024 * 1024
        self.max_models = config.get('GPU_MAX_MODELS', 5)
        self.enabled = config.get('GPU_CACHE_ENABLED', True)
        
        # Initialize SSH client
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Initialize remote cache
        self._init_cache()

    def connect(self):
        """Establish SSH connection"""
        self.ssh.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            key_filename=self.key_path
        )

    def _init_cache(self):
        """Initialize cache directory and metadata"""
        try:
            self.connect()
            
            commands = [
                f'mkdir -p {self.cache_path}',
                f'touch {self.cache_path}/metadata.json',
                f'if [ ! -s {self.cache_path}/metadata.json ]; then '
                f'echo "{{\\"models\\": {{}}, \\"total_size\\": 0}}" > {self.cache_path}/metadata.json; '
                f'fi'
            ]
            
            for cmd in commands:
                _, stdout, stderr = self.ssh.exec_command(cmd)
                if stdout.channel.recv_exit_status() != 0:
                    raise Exception(f"Command failed: {stderr.read().decode()}")
                    
        finally:
            self.ssh.close()

    def get_model_path(self, model_id: int, model_data: Optional[bytes] = None) -> str:
        """Get path to model on GPU, optionally caching if provided"""
        if not self.enabled:
            return self._store_temp(model_id, model_data)
            
        try:
            self.connect()
            
            model_path = f"{self.cache_path}/{model_id}/model.safetensors"
            
            # Check if model exists
            _, stdout, _ = self.ssh.exec_command(f"test -f {model_path}")
            if stdout.channel.recv_exit_status() == 0:
                # Update access time
                self.ssh.exec_command(f"touch {model_path}")
                return model_path
                
            # Cache new model if provided
            if model_data:
                return self._cache_model(model_id, model_data)
                
            raise FileNotFoundError(f"Model {model_id} not in cache")
            
        finally:
            self.ssh.close()

    def _cache_model(self, model_id: int, model_data: bytes) -> str:
        """Cache model on GPU"""
        try:
            self.connect()
            
            # Ensure enough space
            self._ensure_space(len(model_data))
            
            # Create model directory
            model_dir = f"{self.cache_path}/{model_id}"
            model_path = f"{model_dir}/model.safetensors"
            
            self.ssh.exec_command(f"mkdir -p {model_dir}")
            
            # Upload model
            sftp = self.ssh.open_sftp()
            with sftp.file(model_path, 'wb') as f:
                f.write(model_data)
            sftp.close()
            
            # Update metadata
            metadata = self._get_metadata()
            metadata['models'][str(model_id)] = {
                'size': len(model_data),
                'last_used': time.time()
            }
            metadata['total_size'] = sum(m['size'] for m in metadata['models'].values())
            self._save_metadata(metadata)
            
            return model_path
            
        finally:
            self.ssh.close()

    def _store_temp(self, model_id: int, model_data: bytes) -> str:
        """Store model in temporary location when cache is disabled"""
        try:
            self.connect()
            
            temp_path = f"/tmp/model_{model_id}_{time.time()}.safetensors"
            
            sftp = self.ssh.open_sftp()
            with sftp.file(temp_path, 'wb') as f:
                f.write(model_data)
            sftp.close()
            
            return temp_path
            
        finally:
            self.ssh.close()

    def _get_metadata(self) -> Dict:
        """Get cache metadata"""
        try:
            self.connect()
            sftp = self.ssh.open_sftp()
            with sftp.file(f"{self.cache_path}/metadata.json") as f:
                return json.load(f)
        finally:
            sftp.close()
            self.ssh.close()

    def _save_metadata(self, metadata: Dict):
        """Save cache metadata"""
        try:
            self.connect()
            sftp = self.ssh.open_sftp()
            with sftp.file(f"{self.cache_path}/metadata.json", 'w') as f:
                json.dump(metadata, f)
        finally:
            sftp.close()
            self.ssh.close()

    def _ensure_space(self, needed_bytes: int):
        """Ensure enough space for new model"""
        metadata = self._get_metadata()
        
        # Check number of models
        if len(metadata['models']) >= self.max_models:
            self._remove_oldest_model(metadata)
        
        # Check size
        if metadata['total_size'] + needed_bytes > self.max_size:
            self._remove_until_fit(metadata, needed_bytes)
        
        self._save_metadata(metadata)

    def _remove_oldest_model(self, metadata: Dict):
        """Remove least recently used model"""
        if not metadata['models']:
            return
            
        oldest = min(metadata['models'].items(), key=lambda x: x[1]['last_used'])
        model_id = oldest[0]
        
        try:
            self.connect()
            self.ssh.exec_command(f"rm -rf {self.cache_path}/{model_id}")
            
            metadata['total_size'] -= metadata['models'][model_id]['size']
            del metadata['models'][model_id]
            
        finally:
            self.ssh.close()

    def _remove_until_fit(self, metadata: Dict, needed_bytes: int):
        """Remove models until we have enough space"""
        while metadata['total_size'] + needed_bytes > self.max_size and metadata['models']:
            self._remove_oldest_model(metadata)

    def clear_cache(self):
        """Clear entire cache"""
        try:
            self.connect()
            self.ssh.exec_command(f"rm -rf {self.cache_path}/*")
            self._init_cache()
        finally:
            self.ssh.close()