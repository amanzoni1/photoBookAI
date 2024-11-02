from flask import request, jsonify, current_app
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
import logging

from . import storage_bp
from .auth import token_required
from app import db
from models import UserImage, GeneratedImage, TrainedModel, JobStatus
from . import get_storage_service, get_storage_monitor

logger = logging.getLogger(__name__)

def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@storage_bp.route('/training-images/upload', methods=['POST'])
@cross_origin()
@token_required
def upload_training_images(current_user):
    """Upload images for model training"""
    try:
        storage_service = get_storage_service()
        if not storage_service:
            logger.error("Storage service not initialized")
            return jsonify({'message': 'Service unavailable'}), 503

        if 'files' not in request.files:
            return jsonify({'message': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        uploaded_images = []

        for file in files:
            if not file or not file.filename:
                continue

            if allowed_file(file.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
                try:
                    filename = secure_filename(file.filename)
                    
                    # Use improved storage service method
                    location, image_info = storage_service.upload_training_image(
                        current_user.id,
                        file,
                        filename,
                        quality_preset='high'  # Always high quality for training
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
                    logger.info(f"Successfully processed training image: {filename}")
                    
                except Exception as e:
                    logger.error(f"Error uploading training image {filename}: {str(e)}")
                    continue
            else:
                logger.warning(f"Invalid file type: {file.filename}")

        if not uploaded_images:
            return jsonify({'message': 'No valid images uploaded'}), 400

        db.session.commit()
        
        return jsonify({
            'message': 'Training images uploaded successfully',
            'images': [{
                'id': img.id,
                'filename': img.original_filename,
                'width': img.width,
                'height': img.height
            } for img in uploaded_images]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'message': f'Upload failed: {str(e)}'}), 500

@storage_bp.route('/status', methods=['GET'])
@cross_origin()
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