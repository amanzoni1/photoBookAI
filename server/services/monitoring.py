# server/services/monitoring.py

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from models import TrainedModel, StorageLocation
from app import db

logger = logging.getLogger(__name__)


class StorageMonitor:
    def __init__(self, storage_service):
        self.storage_service = storage_service

        # Set up scheduled tasks
        import schedule

        schedule.every().day.at("00:00").do(self.daily_cleanup)
        schedule.every().hour.do(self.update_usage_stats)

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get storage statistics for a user"""
        try:
            # Get model stats
            model_stats = (
                db.session.query(db.func.count(TrainedModel.id))
                .filter(TrainedModel.user_id == user_id)
                .first()
            )

            return {
                "total_models": model_stats[0] or 0,
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            raise

    def daily_cleanup(self):
        """Clean up old or unused files"""
        try:
            # Find unused models (e.g., not used in 30 days)
            threshold = datetime.utcnow() - timedelta(days=30)
            unused_models = TrainedModel.query.filter(
                TrainedModel.last_used < threshold
            ).all()

            for model in unused_models:
                try:
                    # Delete from storage
                    self.storage_service.delete_file(model.storage_location)
                    # Delete from database
                    db.session.delete(model)
                except Exception as e:
                    logger.error(f"Error cleaning up model {model.id}: {str(e)}")

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            logger.error(f"Cleanup error: {str(e)}")

    def update_usage_stats(self):
        """Update storage usage statistics"""
        try:
            stats = defaultdict(int)

            # Calculate storage usage by type
            for location in StorageLocation.query.all():
                try:
                    size = self.storage_service.get_file_size(location)
                    stats[location.storage_type] += size
                except Exception as e:
                    logger.error(f"Error getting file size for {location.id}: {str(e)}")

            # Store stats (implement your storage method)
            logger.info(f"Storage stats updated: {dict(stats)}")

        except Exception as e:
            logger.error(f"Stats update error: {str(e)}")
