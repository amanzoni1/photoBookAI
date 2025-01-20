# server/config.py

import os
from pathlib import Path
import tempfile
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')



# Update PHOTOSHOOT_THEMES
PHOTOSHOOT_THEMES = {
    "kids_christmas": [
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, in Santa hat smiling in studio",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, wearing reindeer antlers, smiling in studio",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, in festive sweater in studio",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, smiling holding gift by decorated Christmas tree",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, holding ornament by decorated Christmas tree",
            "count": 4
        }
    ],
    "kids_dream_jobs": [
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, dressed as firefighter smiling in studio",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, wearing pilot uniform smiling in studio",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, dressed as doctor with stethoscope in studio",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, dressed as astronaut smiling with stars backdrop",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, dressed as chef holding whisk in kitchen setting",
            "count": 4
        }
    ],
    "kids_superhero": [
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, in superhero costume posing heroically in studio",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, wearing cape and mask smiling in studio",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, dressed as superhero with arms crossed, city backdrop",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, in superhero outfit in flying pose in studio",
            "count": 4
        },
        {
            "prompt": "Professional portrait of p3r5onTr1g, 4years old kid, as superhero with shield in outdoor park setting",
            "count": 4
        }
    ]
}

    

class Config:
    # Base directory for the application
    BASE_DIR = Path(__file__).parent.parent

    # Temporary files configuration
    TEMP_FILES_DIR = os.getenv('TEMP_FILES_DIR', Path(tempfile.gettempdir()) / 'ai_training')
    TEMP_FILES_MAX_AGE = 24 * 3600  # 24 hours in seconds

    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'

    # Stripe configuration
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    PRICING = {
        # 1) Single Model + 2 free photoshoots for $19.99
        "BUNDLE_MODEL_1_2PS": {
            "label": "1 Model + 2 Photoshoot Credits",
            "price_cents": 1999,  # $19.99
            "credits": [
                {"type": "MODEL", "quantity": 1},
                {"type": "PHOTOSHOOT", "quantity": 2}
            ]
        },
        # 2) Double Model + 5 photoshoots for $34.99
        "BUNDLE_MODEL_2_5PS": {
            "label": "2 Models + 5 Photoshoot Credits",
            "price_cents": 3499,  # $34.99
            "credits": [
                {"type": "MODEL", "quantity": 2},
                {"type": "PHOTOSHOOT", "quantity": 5}
            ]
        },
        # 3) Single Photoshoot credit for $2.49
        "PS_SINGLE": {
            "label": "1 Photoshoot Credit",
            "price_cents": 249,   # $2.49
            "credits": [
                {"type": "PHOTOSHOOT", "quantity": 1}
            ]
        },
        # 4) 3-pack of photoshoot credits for $4.99
        "PS_3PACK": {
            "label": "3 Photoshoot Credits",
            "price_cents": 499,   # $4.99
            "credits": [
                {"type": "PHOTOSHOOT", "quantity": 3}
            ]
        }
    }

    # Social Auth
    # FRONTEND_URL = ''  ADD HERE for proper auth
    # BASE_URL = ''  ADD HERE for proper payment
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_CALLBACK_URL = "http://localhost:5001/api/auth/google/callback"
    FACEBOOK_CLIENT_ID = os.environ.get('FACEBOOK_CLIENT_ID')
    FACEBOOK_CLIENT_SECRET = os.environ.get('FACEBOOK_CLIENT_SECRET')
    FACEBOOK_CALLBACK_URL = 'http://localhost:5001/api/auth/facebook/callback'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + str(basedir / 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage configuration
    STORAGE_ENDPOINT = os.environ.get('STORAGE_ENDPOINT', 'https://nyc3.digitalocean.com')
    STORAGE_REGION = os.environ.get('STORAGE_REGION', 'nyc3')
    STORAGE_ACCESS_KEY = os.environ.get('STORAGE_ACCESS_KEY')
    STORAGE_SECRET_KEY = os.environ.get('STORAGE_SECRET_KEY')
    STORAGE_BUCKET = os.environ.get('STORAGE_BUCKET')

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