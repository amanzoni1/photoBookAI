# server/routes/storage.py

from flask import request, jsonify, current_app
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

from . import storage_bp
from .auth import token_required
from app import db
from models import UserImage, GeneratedImage
from . import get_storage_service, get_storage_monitor

logger = logging.getLogger(__name__)

def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@storage_bp.route('/upload', methods=['POST'])
@cross_origin()
@token_required
def upload_images(current_user):
    try:
        storage_service = get_storage_service()
        if not storage_service:
            logger.error("Storage service not initialized")
            return jsonify({'message': 'Service unavailable'}), 503

        if 'files' not in request.files:
            return jsonify({'message': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        quality_preset = request.form.get('quality', 'high')
        uploaded_images = []

        for file in files:
            if not file or not file.filename:
                continue

            if allowed_file(file.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
                try:
                    filename = secure_filename(file.filename)
                    destination = f"users/{current_user.id}/images/{datetime.utcnow().strftime('%Y/%m/%d')}/{filename}"
                    
                    # Read file into memory
                    file_content = file.read()
                    file.seek(0)  # Reset file pointer
                    
                    location, image_info = storage_service.upload_image(
                        file,
                        destination,
                        quality_preset=quality_preset
                    )
                    
                    image = UserImage(
                        user_id=current_user.id,
                        storage_location_id=location.id,
                        original_filename=filename,
                        file_size=image_info['file_size'],
                        mime_type=f"image/{image_info['format'].lower()}",
                        width=image_info['width'],
                        height=image_info['height']
                    )
                    
                    db.session.add(image)
                    uploaded_images.append(image)
                    logger.info(f"Successfully processed image: {filename}")
                    
                except Exception as e:
                    logger.error(f"Error uploading file {filename}: {str(e)}")
                    continue
            else:
                logger.warning(f"Invalid file type: {file.filename}")

        if not uploaded_images:
            return jsonify({'message': 'No valid images uploaded'}), 400

        db.session.commit()
        
        response_images = [{
            'id': img.id,
            'url': storage_service.get_public_url(img.storage_location),
            'width': img.width,
            'height': img.height,
            'filename': img.original_filename
        } for img in uploaded_images]

        return jsonify({
            'message': 'Images uploaded successfully',
            'images': response_images
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'message': f'Upload failed: {str(e)}'}), 500

@storage_bp.route('/images', methods=['GET'])
@cross_origin()
@token_required
def get_user_images(current_user):
    """Get user's uploaded images"""
    try:
        storage_service = get_storage_service()
        if not storage_service:
            logger.error("Storage service not initialized")
            return jsonify({'message': 'Service unavailable'}), 503

        images = UserImage.query.filter_by(user_id=current_user.id).all()
        
        return jsonify({
            'images': [{
                'id': img.id,
                'filename': img.original_filename,
                'url': storage_service.get_public_url(img.storage_location),
                'width': img.width,
                'height': img.height,
                'created_at': img.created_at.isoformat()
            } for img in images]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching images: {str(e)}")
        return jsonify({'message': str(e)}), 500

@storage_bp.route('/status', methods=['GET'])
@token_required
def get_storage_status(current_user):
    """Get storage usage statistics"""
    try:
        storage_monitor = get_storage_monitor()
        if not storage_monitor:
            logger.error("Storage monitor not initialized")
            return jsonify({'message': 'Service unavailable'}), 503

        stats = storage_monitor.get_user_stats(current_user.id)
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Storage status error: {str(e)}")
        return jsonify({'message': str(e)}), 500