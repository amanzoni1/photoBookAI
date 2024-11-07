# server/routes/__init__.py

from flask import Blueprint, current_app
from services.storage import StorageService
from services.monitoring import StorageMonitor
from services.cache import ModelCache
from services.credits import CreditService
from services.auth import TokenManager
from services.queue import JobQueue
from services.worker import WorkerService
from services.job_monitor import JobMonitor
from services.alerts import AlertService
from services.temp_files import TempFileManager
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
credits_bp = Blueprint('credits', __name__, url_prefix='/api/credits')

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

def get_credit_service():
    """Get credit service from current app"""
    return current_app.config.get('credit_service')

def get_token_manager():
    """Get token manager from current app"""
    return current_app.config.get('token_manager')

def get_job_queue():
    """Get job queue from current app"""
    return current_app.config.get('job_queue')

def get_worker_service():
    """Get worker service from current app"""
    return current_app.config.get('worker_service')

def get_job_monitor():
    """Get job monitor from current app"""
    return current_app.config.get('job_monitor')

def get_alert_service():
    """Get alert service from current app"""
    return current_app.config.get('alert_service')

def get_temp_manager():
    """Get temp file manager from current app"""
    return current_app.config.get('temp_manager')

def init_services(app):
    """Initialize required services"""
    # Create services with app context
    temp_manager = TempFileManager(app.config)
    storage_service = StorageService(app.config)
    model_cache = ModelCache(app.config['MODEL_CACHE_PATH'], storage_service)
    storage_monitor = StorageMonitor(storage_service)
    credit_service = CreditService(app.config)
    token_manager = TokenManager(app.config)
    job_queue = JobQueue(app.config)
    
    # Store initial services in config
    app.config['temp_manager'] = temp_manager
    app.config['storage_service'] = storage_service
    app.config['model_cache'] = model_cache
    app.config['storage_monitor'] = storage_monitor
    app.config['credit_service'] = credit_service
    app.config['token_manager'] = token_manager
    app.config['job_queue'] = job_queue
    
    # Initialize worker service
    worker_service = WorkerService(app.config, app)
    app.config['worker_service'] = worker_service
    
    # Initialize job monitor
    job_monitor = JobMonitor(app.config, job_queue)
    app.config['job_monitor'] = job_monitor
    
    # Initialize alert service and connect to worker
    alert_service = AlertService(app.config)
    app.config['alert_service'] = alert_service
    
    # Add alert handler to worker service
    worker_service.add_alert_handler(alert_service.handle_alert)
    
    # Start monitoring thread
    def run_monitoring():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
    monitoring_thread.start()
    
    # Start workers
    worker_service.start_workers(num_workers=app.config.get('MIN_WORKERS', 2))
    
    logger.info("Services initialized successfully")

def init_app(app):
    """Register all blueprints with the app"""
    # Import routes here to avoid circular imports
    from .auth import auth_bp
    from .user import user_bp
    from .model import model_bp
    from .storage import storage_bp
    from .credits import credits_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(storage_bp)
    app.register_blueprint(credits_bp)
    logger.info("Blueprints registered successfully")