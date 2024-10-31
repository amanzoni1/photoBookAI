# server/routes/model.py

from flask import request, jsonify, current_app
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

from . import model_bp
from .auth import token_required
from app import db
from models import TrainedModel, UserImage, JobStatus
from . import get_storage_service, get_model_cache

logger = logging.getLogger(__name__)

def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@model_bp.route('/create', methods=['POST'])
@cross_origin()
@token_required
def create_model(current_user):
    try:
        if 'files' not in request.files:
            return jsonify({'message': 'No files provided'}), 400

        files = request.files.getlist('files')
        name = request.form.get('name')
        age_years = request.form.get('ageYears')
        age_months = request.form.get('ageMonths')

        if not name:
            return jsonify({'message': 'Name is required'}), 400

        if not age_years and not age_months:
            return jsonify({'message': 'Please provide either age in years or months'}), 400

        # Upload training images
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
                filename = secure_filename(file.filename)
                destination = f"users/{current_user.id}/training_images/{datetime.utcnow().strftime('%Y/%m/%d')}/{filename}"
                
                storage_service = get_storage_service()
                location, image_info = storage_service.upload_image(
                    file,
                    destination,
                    quality_preset='high'
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
                uploaded_files.append(image)
            else:
                return jsonify({'message': 'Invalid file type'}), 400

        # Create model record
        model = TrainedModel(
            user_id=current_user.id,
            name=name,
            version='1.0',
            status=JobStatus.PENDING,
            config={
                'age_years': age_years,
                'age_months': age_months
            }
        )
        
        db.session.add(model)
        db.session.commit()

        # Queue training job (implementation pending)
        logger.info(f"Started AI training for user {current_user.id}, model {model.id}")

        return jsonify({
            'message': 'Model training started successfully',
            'model_id': model.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Model creation error: {str(e)}")
        return jsonify({'message': f'Model creation failed: {str(e)}'}), 500

@model_bp.route('/<int:model_id>/cache', methods=['POST'])
@token_required
def cache_model(current_user, model_id):
    """Cache a model for faster inference"""
    try:
        model = TrainedModel.query.get_or_404(model_id)
        
        if model.user_id != current_user.id:
            return jsonify({'message': 'Unauthorized'}), 403
        
        model_cache = get_model_cache()    
        model_path = model_cache.get_or_cache(model.storage_location)
        
        return jsonify({
            'message': 'Model cached successfully',
            'cache_path': model_path
        }), 200
        
    except Exception as e:
        logger.error(f"Caching error: {str(e)}")
        return jsonify({'message': f'Caching failed: {str(e)}'}), 500

@model_bp.route('/list', methods=['GET'])
@cross_origin()
@token_required
def list_models(current_user):
    """List user's trained models"""
    models = TrainedModel.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'models': [{
            'id': model.id,
            'name': model.name,
            'version': model.version,
            'status': model.status.value,
            'created_at': model.created_at.isoformat(),
            'config': model.config
        } for model in models]
    }), 200