# server/services/storage.py

import os
import boto3
from botocore.exceptions import ClientError
from typing import BinaryIO, Optional, Dict, Any, Tuple
from datetime import datetime
import mimetypes
from PIL import Image
import io
import math
import logging

from models import StorageLocation, StorageType
from app import db

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = boto3.client('s3',
            endpoint_url=config['STORAGE_ENDPOINT'],
            aws_access_key_id=config['STORAGE_ACCESS_KEY'],
            aws_secret_access_key=config['STORAGE_SECRET_KEY'],
            region_name=config.get('STORAGE_REGION', 'nyc3')
        )
        self.bucket = config['STORAGE_BUCKET']
        
        # Endpoint configuration
        self.endpoint = config['STORAGE_ENDPOINT'].rstrip('/')
        self.cdn_endpoint = config.get('CDN_ENDPOINT', self.endpoint).rstrip('/')
        
        # Upload configurations
        self.multipart_threshold = 100 * 1024 * 1024  # 100MB
        self.multipart_chunksize = 50 * 1024 * 1024   # 50MB

    def get_public_url(self, storage_location: StorageLocation) -> str:
        """Get public URL for a storage location"""
        try:
            if storage_location.metadata_json and storage_location.metadata_json.get('public'):
                return f"{self.cdn_endpoint}/{storage_location.path}"
            return self.get_download_url(storage_location)
        except Exception as e:
            logger.error(f"Error generating URL: {str(e)}")
            return ""

    def get_download_url(self, location: StorageLocation, expires_in: int = 3600) -> str:
        """Get a presigned URL for downloading a private file"""
        try:
            return self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': location.bucket,
                    'Key': location.path
                },
                ExpiresIn=expires_in
            )
        except Exception as e:
            logger.error(f"Error generating download URL: {str(e)}")
            raise

    def upload_image(self, 
                    image_file: BinaryIO, 
                    destination: str,
                    quality_preset: str = 'high') -> Tuple[StorageLocation, Dict[str, int]]:
        """Upload an image with quality presets"""
        try:
            presets = {
                'high': {
                    'max_size': 4096,
                    'quality': 95,
                    'format': 'PNG'
                },
                'medium': {
                    'max_size': 2048,
                    'quality': 90,
                    'format': 'JPEG'
                },
                'low': {
                    'max_size': 1024,
                    'quality': 85,
                    'format': 'JPEG'
                }
            }
            
            preset = presets[quality_preset]
            
            # Process image
            img = Image.open(image_file)
            original_size = img.size
            
            # Convert RGBA to RGB if needed
            if preset['format'] == 'JPEG' and img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Resize if needed
            if max(img.size) > preset['max_size']:
                ratio = preset['max_size'] / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.LANCZOS)
            
            # Save to buffer
            buffer = io.BytesIO()
            if preset['format'] == 'PNG':
                img.save(buffer, format='PNG', optimize=True)
            else:
                img.save(buffer, 
                        format='JPEG', 
                        quality=preset['quality'], 
                        optimize=True,
                        progressive=True)
            
            buffer.seek(0)
            file_size = buffer.getbuffer().nbytes
            
            # Upload to storage
            location = self.upload_file(
                buffer,
                destination,
                content_type=f'image/{preset["format"].lower()}',
                public=True
            )
            
            image_info = {
                'width': img.size[0],
                'height': img.size[1],
                'original_width': original_size[0],
                'original_height': original_size[1],
                'file_size': file_size,
                'format': preset['format']
            }
            
            return location, image_info

        except Exception as e:
            logger.error(f"Image processing error: {str(e)}")
            raise

    def upload_file(self, 
                   file_obj: BinaryIO, 
                   destination: str, 
                   content_type: Optional[str] = None,
                   public: bool = False) -> StorageLocation:
        """Upload a file to object storage"""
        try:
            if not content_type:
                content_type = mimetypes.guess_type(destination)[0] or 'application/octet-stream'

            extra_args = {
                'ContentType': content_type,
                'ACL': 'public-read' if public else 'private'
            }

            self.client.upload_fileobj(
                file_obj,
                self.bucket,
                destination,
                ExtraArgs=extra_args
            )

            location = StorageLocation(
                storage_type=StorageType.DO_SPACES,
                bucket=self.bucket,
                path=destination,
                metadata_json={
                    'content_type': content_type,
                    'public': public
                }
            )
            
            db.session.add(location)
            db.session.commit()

            return location

        except Exception as e:
            logger.error(f"Storage error: {str(e)}")
            db.session.rollback()
            raise