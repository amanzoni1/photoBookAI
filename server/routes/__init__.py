# server/routes/__init__.py

from flask import Blueprint, current_app
from services.storage import StorageService
from services.monitoring import StorageMonitor
from services.credits import CreditService
from services.auth import TokenManager
from services.queue import JobQueue
from services.worker import WorkerService
from services.job_monitor import JobMonitor
from services.alerts import AlertService
from services.temp_files import TempFileManager
from services.oauth import OAuthService
from services.payments import PaymentService
import logging
import threading
import schedule
import time

logger = logging.getLogger(__name__)

# Create blueprints for different features
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
user_bp = Blueprint('user', __name__, url_prefix='/api/user')
payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')
credits_bp = Blueprint('credits', __name__, url_prefix='/api/credits')
model_bp = Blueprint('model', __name__, url_prefix='/api/model')
photoshoot_bp = Blueprint('photoshoot', __name__, url_prefix='/api/photoshoot')
job_bp = Blueprint('job', __name__, url_prefix='/api/job')

# Service accessor functions
def get_storage_service():
    """Get storage service from current app"""
    return current_app.config.get('storage_service')

def get_storage_monitor():
    """Get storage monitor from current app"""
    return current_app.config.get('storage_monitor')

def get_credit_service():
    """Get credit service from current app"""
    return current_app.config.get('credit_service')

def get_token_manager():
    """Get token manager from current app"""
    return current_app.config.get('token_manager')

def get_oauth_service():
    """Get OAuth service from current app"""
    return current_app.config.get('oauth_service')

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

def get_payment_service():
    """Get payment service from current app"""
    return current_app.config.get('payment_service')

def init_services(app):
    """Initialize required services"""
    try:
        # 1. Initialize core services first
        temp_manager = TempFileManager(app.config)
        app.config['temp_manager'] = temp_manager
        logger.info("Initialized temp manager")

        storage_service = StorageService(app.config)
        app.config['storage_service'] = storage_service
        logger.info("Initialized storage service")

        # 2. Initialize monitoring (depends on storage)
        storage_monitor = StorageMonitor(storage_service)
        app.config['storage_monitor'] = storage_monitor
        logger.info("Initialized storage monitor")

        # 3. Initialize user-related services
        credit_service = CreditService(app.config)
        app.config['credit_service'] = credit_service
        logger.info("Initialized credit service")

        token_manager = TokenManager(app.config)
        app.config['token_manager'] = token_manager
        logger.info("Initialized token manager")

        oauth_service = OAuthService(app.config)
        app.config['oauth_service'] = oauth_service
        logger.info("Initialized OAuth service")

        # 4. Initialize payment service (depends on credit service)
        payment_service = PaymentService(app.config)
        app.config['payment_service'] = payment_service
        logger.info("Initialized payment service")

        # 5. Initialize job processing services
        job_queue = JobQueue(app.config)
        app.config['job_queue'] = job_queue
        logger.info("Initialized job queue")

        worker_service = WorkerService(app.config, app)
        app.config['worker_service'] = worker_service
        logger.info("Initialized worker service")

        job_monitor = JobMonitor(app.config, job_queue)
        app.config['job_monitor'] = job_monitor
        logger.info("Initialized job monitor")

        # 6. Initialize alert service last (depends on worker)
        alert_service = AlertService(app.config)
        app.config['alert_service'] = alert_service
        logger.info("Initialized alert service")

        # Connect alert service to worker
        worker_service.add_alert_handler(alert_service.handle_alert)

        # Start monitoring thread
        def run_monitoring():
            while True:
                schedule.run_pending()
                time.sleep(60)

        monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
        monitoring_thread.start()
        logger.info("Started monitoring thread")

        # Start workers
        worker_service.start_workers(num_workers=app.config.get('MIN_WORKERS', 2))
        logger.info("Started worker processes")

        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Service initialization failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to initialize services: {str(e)}")

def init_app(app):
    """Register all blueprints with the app"""
    from .auth import auth_bp
    from .user import user_bp
    from .payments import payments_bp
    from .credits import credits_bp
    from .model import model_bp
    from .photoshoot import photoshoot_bp
    from .job import job_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(credits_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(photoshoot_bp)
    app.register_blueprint(job_bp)
    logger.info("Blueprints registered successfully")