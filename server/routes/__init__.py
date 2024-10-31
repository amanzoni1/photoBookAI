# server/routes/__init__.py

from flask import Blueprint, current_app
from services.storage import StorageService
from services.monitoring import StorageMonitor
from services.cache import ModelCache
import logging
import threading
import schedule
import time

logger = logging.getLogger(__name__)

# Create blueprints for different features
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
user_bp = Blueprint('user', __name__, url_prefix='/api/user')
model_bp = Blueprint('model', __name__, url_prefix='/api/model')
storage_bp = Blueprint('storage', __name__, url_prefix='/api/storage')

# Service accessor functions
def get_storage_service():
    """Get storage service from current app"""
    return current_app.config.get('storage_service')

def get_model_cache():
    """Get model cache from current app"""
    return current_app.config.get('model_cache')

def get_storage_monitor():
    """Get storage monitor from current app"""
    return current_app.config.get('storage_monitor')

def init_services(app):
    """Initialize required services"""
    # Create services with app context
    storage_service = StorageService(app.config)
    model_cache = ModelCache(app.config['MODEL_CACHE_PATH'], storage_service)
    storage_monitor = StorageMonitor(storage_service)
    
    # Store services in app config
    app.config['storage_service'] = storage_service
    app.config['model_cache'] = model_cache
    app.config['storage_monitor'] = storage_monitor
    
    # Start monitoring thread
    def run_monitoring():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
    monitoring_thread.start()
    
    logger.info("Services initialized successfully")

def init_app(app):
    """Register all blueprints with the app"""
    # Import routes here to avoid circular imports
    from .auth import auth_bp
    from .user import user_bp
    from .model import model_bp
    from .storage import storage_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(storage_bp)
    logger.info("Blueprints registered successfully")