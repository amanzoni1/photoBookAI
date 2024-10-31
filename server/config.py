# server/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

class Config:
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
    MODEL_STORAGE_CLASS = os.environ.get('MODEL_STORAGE_CLASS', 'STANDARD')  # or 'REDUCED_REDUNDANCY'
    MODEL_CACHE_ENABLED = os.environ.get('MODEL_CACHE_ENABLED', 'True').lower() == 'true'
    MODEL_CACHE_PATH = os.environ.get('MODEL_CACHE_PATH', '/tmp/model_cache')
    
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