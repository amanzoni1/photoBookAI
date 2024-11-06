# server/services/storage.py

import os
import boto3
from botocore.exceptions import ClientError
from typing import BinaryIO, Dict, Any, Tuple
from datetime import datetime
import mimetypes
from PIL import Image
import io
import hashlib
import logging

from models import StorageLocation, StorageType
from app import db

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = boto3.client(
            's3',
            endpoint_url=config['STORAGE_ENDPOINT'],
            aws_access_key_id=config['STORAGE_ACCESS_KEY'],
            aws_secret_access_key=config['STORAGE_SECRET_KEY'],
            region_name=config.get('STORAGE_REGION', 'nyc3')
        )
        self.bucket = config['STORAGE_BUCKET']
        self.cdn_endpoint = config.get('DO_SPACES_CDN_ENDPOINT', config['STORAGE_ENDPOINT']).rstrip('/')

    def _get_file_path(self, user_id: int, file_type: str, filename: str) -> str:
        """Generate storage path based on file type"""
        date_path = datetime.utcnow().strftime('%Y/%m/%d')
        
        if file_type == 'training':
            return f"users/{user_id}/training_images/{date_path}/{filename}"
        elif file_type == 'model':
            return f"users/{user_id}/models/{filename}"
        elif file_type == 'photobook': 
            return f"users/{user_id}/photobooks/{filename}"
        elif file_type == 'generated':
            return f"users/{user_id}/generated/{filename}"
        else:
            raise ValueError(f"Invalid file type: {file_type}")

    def _calculate_checksum(self, file_obj: BinaryIO) -> str:
        """Calculate SHA256 checksum of the file"""
        sha256_hash = hashlib.sha256()
        for byte_block in iter(lambda: file_obj.read(4096), b""):
            sha256_hash.update(byte_block)
        file_obj.seek(0)
        return sha256_hash.hexdigest()

    def upload_training_image(self, 
                              user_id: int,
                              image_file: BinaryIO,
                              filename: str,
                              quality_preset: str = 'high') -> Tuple[StorageLocation, Dict[str, Any]]:
        """Upload a training image"""
        destination = self._get_file_path(user_id, 'training', filename)
        
        try:
            # Process and optimize image
            img = Image.open(image_file)
            buffer = io.BytesIO()
            
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Apply quality preset and set format accordingly
            if quality_preset == 'high':
                img_format = 'PNG'
                img.save(buffer, format=img_format, optimize=True)
            else:
                img_format = 'JPEG'
                img.save(buffer, format=img_format, quality=85, optimize=True)
                
            buffer.seek(0)
            file_size = buffer.getbuffer().nbytes
            checksum = self._calculate_checksum(buffer)
            buffer.seek(0)
            
            # Create storage location
            location = StorageLocation(
                storage_type=StorageType.DO_SPACES,
                bucket=self.bucket,
                path=destination,
                file_size=file_size,
                content_type=f"image/{img_format.lower()}",
                checksum=checksum,
                metadata_json={'quality_preset': quality_preset}
            )
            
            # Upload file to storage
            self.client.upload_fileobj(
                buffer,
                self.bucket,
                destination,
                ExtraArgs={
                    'ContentType': location.content_type,
                    'ACL': 'public-read'
                }
            )
            
            # Add to the session (commit handled externally)
            db.session.add(location)
            
            # Prepare image info
            image_info = {
                'width': img.width,
                'height': img.height,
                'format': img_format,  # Explicitly set format
                'file_size': file_size
            }
            
            logger.debug(f"Uploaded training image: {filename}, Format: {img_format}, Size: {file_size} bytes")
            
            return location, image_info

        except Exception as e:
            logger.error(f"Failed to upload training image {filename}: {str(e)}")
            raise

    def upload_model_weights(self,
                           user_id: int,
                           model_id: int,
                           weights_file: BinaryIO,
                           version: str = '1.0') -> StorageLocation:
        """Upload model weights file"""
        filename = f"{model_id}/model-{version}.safetensors"
        destination = self._get_file_path(user_id, 'model', filename)
        
        # Calculate size and checksum
        file_size = weights_file.seek(0, 2)
        weights_file.seek(0)
        checksum = self._calculate_checksum(weights_file)
        weights_file.seek(0)
        
        location = StorageLocation(
            storage_type=StorageType.DO_SPACES,
            bucket=self.bucket,
            path=destination,
            file_size=file_size,
            content_type='application/octet-stream',
            checksum=checksum,
            metadata_json={'version': version}
        )
        
        # Upload with multipart for large files
        self.client.upload_fileobj(
            weights_file,
            self.bucket,
            destination,
            ExtraArgs={
                'ContentType': location.content_type,
                'ACL': 'private'
            }
        )
        
        db.session.add(location)
        
        return location
    
    def save_photobook_image(self,
                           user_id: int,
                           photobook_id: int,
                           image_data: bytes,
                           image_number: int) -> StorageLocation:
        """Save a photobook image"""
        filename = f"{photobook_id}/image_{image_number:02d}.png"
        destination = self._get_file_path(user_id, 'photobook', filename)
        
        # Create file-like object from bytes
        buffer = io.BytesIO(image_data)
        file_size = len(image_data)
        checksum = hashlib.sha256(image_data).hexdigest()
        
        location = StorageLocation(
            storage_type=StorageType.DO_SPACES,
            bucket=self.bucket,
            path=destination,
            file_size=file_size,
            content_type='image/png',
            checksum=checksum,
            metadata_json={
                'photobook_id': photobook_id,
                'image_number': image_number
            }
        )
        
        self.client.upload_fileobj(
            buffer,
            self.bucket,
            destination,
            ExtraArgs={
                'ContentType': 'image/png',
                'ACL': 'public-read'
            }
        )
        
        db.session.add(location)
        
        return location

    def save_generated_image(self,
                           user_id: int,
                           model_id: int,
                           image_data: bytes,
                           filename: str) -> StorageLocation:
        """Save a generated image"""
        destination = self._get_file_path(user_id, 'generated', f"{model_id}/{filename}")
        
        # Create file-like object from bytes
        buffer = io.BytesIO(image_data)
        file_size = len(image_data)
        checksum = hashlib.sha256(image_data).hexdigest()
        
        # Determine content type
        content_type = mimetypes.guess_type(filename)[0] or 'image/png'
        
        location = StorageLocation(
            storage_type=StorageType.DO_SPACES,
            bucket=self.bucket,
            path=destination,
            file_size=file_size,
            content_type=content_type,
            checksum=checksum,
            metadata_json={'generated': True}
        )
        
        self.client.upload_fileobj(
            buffer,
            self.bucket,
            destination,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read'
            }
        )
        
        db.session.add(location)
        
        return location

    def get_download_url(self, location: StorageLocation, expires_in: int = 3600) -> str:
        """Get a presigned URL for downloading private files"""
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

    def get_public_url(self, location: StorageLocation) -> str:
        """Get public URL for publicly accessible files"""
        return f"{self.cdn_endpoint}/{location.path}"

    def delete_file(self, location: StorageLocation) -> bool:
        """Delete a file from storage"""
        try:
            self.client.delete_object(
                Bucket=location.bucket,
                Key=location.path
            )
            db.session.delete(location)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            db.session.rollback()
            return False
        
    def get_file_data(self, location: StorageLocation) -> bytes:
        """Download file data from storage."""
        try:
            response = self.client.get_object(
                Bucket=location.bucket,
                Key=location.path
            )
            file_data = response['Body'].read()
            return file_data
        except Exception as e:
            logger.error(f"Error downloading file data: {str(e)}")
            raise