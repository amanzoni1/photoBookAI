# server/config.py

import os
from pathlib import Path
import tempfile
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')


PRICES = {
    'MODEL': 24.99,
    'PHOTOBOOK': 3.99
}
IMAGES_PER_PHOTOBOOK = 20 
IMAGES_PER_THEME = 5

# Update PHOTOSHOOT_THEMES
PHOTOSHOOT_THEMES = {
    "kids_christmas": [
        "Professional portrait of p3r5onTr1g, 4years old kid, in Santa hat smiling in studio",
        "Professional portrait of p3r5onTr1g, 4years old kid, wearing reindeer antlers, smiling in studio",
        "Professional portrait of p3r5onTr1g, 4years old kid, in festive sweater in studio",
        "Professional portrait of p3r5onTr1g, 4years old kid, smiling holding gift by decorated Christmas tree",
        "Professional portrait of p3r5onTr1g, 4years old kid, holding ornament by decorated Christmas tree"
    ],
    "kids_dream_jobs": [
        "Professional portrait of p3r5onTr1g, 4years old kid, dressed as firefighter smiling in studio",
        "Professional portrait of p3r5onTr1g, 4years old kid, wearing pilot uniform smiling in studio",
        "Professional portrait of p3r5onTr1g, 4years old kid, dressed as doctor with stethoscope in studio",
        "Professional portrait of p3r5onTr1g, 4years old kid, dressed as astronaut smiling with stars backdrop",
        "Professional portrait of p3r5onTr1g, 4years old kid, dressed as chef holding whisk in kitchen setting"
    ],
    "kids_superhero": [
        "Professional portrait of p3r5onTr1g, 4years old kid, in superhero costume posing heroically in studio",
        "Professional portrait of p3r5onTr1g, 4years old kid, wearing cape and mask smiling in studio",
        "Professional portrait of p3r5onTr1g, 4years old kid, dressed as superhero with arms crossed, city backdrop",
        "Professional portrait of p3r5onTr1g, 4years old kid, in superhero outfit in flying pose in studio",
        "Professional portrait of p3r5onTr1g, 4years old kid, as superhero with shield in outdoor park setting"
    ]
}

# Add age groups configuration (useful for future)
AGE_GROUPS = {
    "newborn": {
        "min_months": 0,
        "max_months": 12,
        "description": "Newborn (0-12 months)"
    },
    "toddler": {
        "min_months": 13,
        "max_months": 36,
        "description": "Toddler (1-3 years)"
    },
    "kid": {
        "min_months": 48,
        "max_months": 96,
        "description": "Kid (4-8 years)"
    }
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
    LAMBDA_REGIONS = ['us-west-3', 'us-west-2', 'us-west-1', 'us-south-1', 'us-south-2', 'us-south-3', 'us-east-1', 'us-east-2', 'us-east-3', 'us-midwest-1',] 
    LAMBDA_INSTANCE_TYPES = ['gpu_1x_h100_pcie', 'gpu_1x_h100_sxm5']

    # AI Training settings
    HF_TOKEN = os.environ.get('HF_TOKEN')

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