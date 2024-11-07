# server/config.py

import os
from pathlib import Path
import tempfile
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

IMAGES_PER_PHOTOBOOK = 15 
PRICES = {
    'MODEL': 24.99,
    'PHOTOBOOK': 3.99
}
    

class Config:
    # Base directory for the application
    BASE_DIR = Path(__file__).parent.parent

    # Temporary files configuration
    TEMP_FILES_DIR = os.getenv('TEMP_FILES_DIR', Path(tempfile.gettempdir()) / 'ai_training')
    TEMP_FILES_MAX_AGE = 24 * 3600  # 24 hours in seconds

    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + str(basedir / 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage configuration
    STORAGE_ENDPOINT = os.environ.get('STORAGE_ENDPOINT', 'https://nyc3.digitalocean.com')
    STORAGE_REGION = os.environ.get('STORAGE_REGION', 'nyc3')
    STORAGE_ACCESS_KEY = os.environ.get('STORAGE_ACCESS_KEY')
    STORAGE_SECRET_KEY = os.environ.get('STORAGE_SECRET_KEY')
    STORAGE_BUCKET = os.environ.get('STORAGE_BUCKET')
    
    # Model storage settings
    MODEL_CACHE_ENABLED = os.environ.get('MODEL_CACHE_ENABLED', 'True').lower() == 'true'
    MODEL_CACHE_PATH = os.environ.get('MODEL_CACHE_PATH', '/tmp/model_cache')
    MODEL_CACHE_SIZE_GB = 20

    # Lambda GPU Settings
    LAMBDA_API_KEY = os.environ.get('LAMBDA_API_KEY')
    LAMBDA_INSTANCE_ID= os.environ.get('LAMBDA_INSTANCE_ID')
    LAMBDA_SSH_KEY = os.environ.get('LAMBDA_SSH_KEY')
    LAMBDA_SSH_KEY_NAME = os.environ.get('LAMBDA_SSH_KEY_NAME')
    LAMBDA_SSH_KEY_PATH= os.environ.get('LAMBDA_SSH_KEY_PATH')
    LAMBDA_REGION = os.environ.get('LAMBDA_REGION')
    LAMBDA_INSTANCE_TYPE = 'gpu_1x_h100_pcie'
    LAMBDA_CUSTOM_IMAGE_ID = 'your-custom-image-id'

    # AI Training settings
    HF_TOKEN = os.environ.get('HF_TOKEN')
    AI_TRAINING_BASE_PATH = os.environ.get('AI_TRAINING_BASE_PATH', '/tmp/ai_training')

    # Lambda specific paths
    LAMBDA_WORKING_DIR = '/home/ubuntu/workspace'  # Default Lambda working directory
    LAMBDA_MODEL_CACHE = '/home/ubuntu/model_cache'
    LAMBDA_DATA_PATH = '/home/ubuntu/data'
    
    # GPU Cache Settings (adjusted for Lambda)
    GPU_CACHE_ENABLED = True
    GPU_CACHE_PATH = LAMBDA_MODEL_CACHE
    GPU_CACHE_SIZE_GB = 50  # Adjust based on your instance storage
    GPU_MAX_MODELS = 5

    # Redis configuration
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # Token settings
    TOKEN_EXPIRY_HOURS = int(os.environ.get('TOKEN_EXPIRY_HOURS', 1))
    REFRESH_TOKEN_DAYS = int(os.environ.get('REFRESH_TOKEN_DAYS', 30))

    # Job monitoring settings
    JOB_CLEANUP_HOURS = 24
    JOB_RETENTION_DAYS = 7
    JOB_MONITOR_ENABLED = True

     # Worker settings
    MIN_WORKERS = 2
    MAX_WORKERS = 10
    SCALING_THRESHOLD = 5
    JOB_MAX_RETRIES = 3
    JOB_RETRY_DELAY = 300  # 5 minutes
    JOB_CLEANUP_HOURS = 24
    JOB_RETENTION_DAYS = 7

    # Alert settings
    ALERT_EMAIL_ENABLED = False  
    ALERT_SLACK_ENABLED = False  
    
    # Email settings 
    SMTP_HOST = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASS = os.environ.get('SMTP_PASS')
    ALERT_EMAIL = os.environ.get('ALERT_EMAIL')
        
    # Image quality settings
    IMAGE_QUALITY_PRESET = os.environ.get('IMAGE_QUALITY_PRESET', 'high')
    MAX_IMAGE_SIZE = {
        'high': 4096,
        'medium': 2048,
        'low': 1024
    }
    IMAGE_QUALITY = {
        'high': 95,
        'medium': 90,
        'low': 85
    }
    
    # Upload limits
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size for model uploads
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    ALLOWED_MODEL_EXTENSIONS = {'safetensors', 'bin', 'pt', 'pth'}