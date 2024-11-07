# server/services/temp_files.py

import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

class TempFileManager:
    def __init__(self, config):
        self.temp_dir = Path(config.get('TEMP_FILES_DIR', Path(tempfile.gettempdir()) / 'ai_training'))
        self.max_age = config.get('TEMP_FILES_MAX_AGE', 24 * 3600)  # 24 hours default
        self._ensure_temp_dir()

    def _ensure_temp_dir(self):
        """Ensure temporary directory exists with correct permissions."""
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir.chmod(0o755)
        except Exception as e:
            logger.error(f"Failed to create temp directory: {e}")
            # Fallback to system temp directory
            self.temp_dir = Path(tempfile.gettempdir()) / 'ai_training'
            self.temp_dir.mkdir(parents=True, exist_ok=True)

    def create_temp_dir(self) -> Path:
        """Create a new temporary directory for a specific job."""
        unique_dir = self.temp_dir / str(uuid.uuid4())
        unique_dir.mkdir(parents=True, exist_ok=True)
        return unique_dir

    def cleanup_old_files(self):
        """Clean up old temporary files."""
        try:
            cutoff = datetime.now() - timedelta(seconds=self.max_age)
            for path in self.temp_dir.glob('*'):
                if path.is_dir():
                    try:
                        mtime = datetime.fromtimestamp(path.stat().st_mtime)
                        if mtime < cutoff:
                            shutil.rmtree(path, ignore_errors=True)
                    except Exception as e:
                        logger.error(f"Failed to remove old directory {path}: {e}")
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")