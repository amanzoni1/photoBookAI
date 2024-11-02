# server/routes/model.py

from flask import request, jsonify, current_app
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

from . import model_bp
from .auth import token_required
from app import db
from models import TrainedModel, UserImage, JobStatus, GeneratedImage
from services.queue import JobType
from . import (
    get_storage_service,
    get_model_cache,
    get_job_queue,
    get_credit_service,
    get_worker_service
)

logger = logging.getLogger(__name__)

def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@model_bp.route('/training', methods=['POST'])
@cross_origin()
@token_required
def create_model(current_user):
    """Create model from uploaded training images"""
    try:
        # Check credits first
        credit_service = get_credit_service()
        if not credit_service.use_credits(current_user, 'MODEL_TRAINING'):
            return jsonify({'message': 'Insufficient credits for model training'}), 403

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

        # Upload training images using improved storage service
        storage_service = get_storage_service()
        uploaded_files = []
        
        for file in files:
            if file and allowed_file(file.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
                filename = secure_filename(file.filename)
                
                # Use improved storage service for upload
                location, image_info = storage_service.upload_training_image(
                    current_user.id,
                    file,
                    filename,
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
                'age_months': age_months,
                'training_images': len(uploaded_files)
            }
        )
        
        # Associate training images with model
        model.training_images.extend(uploaded_files)
        
        db.session.add(model)
        db.session.commit()

        # Enqueue training job
        job_queue = get_job_queue()
        job_id = job_queue.enqueue_job(
            JobType.MODEL_TRAINING,
            current_user.id,
            {
                'model_id': model.id,
                'image_ids': [img.id for img in uploaded_files],
                'name': name,
                'config': model.config
            }
        )

        logger.info(f"Queued training job {job_id} for user {current_user.id}, model {model.id}")

        return jsonify({
            'message': 'Model training started successfully',
            'model_id': model.id,
            'job_id': job_id,
            'training_images': len(uploaded_files)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Model creation error: {str(e)}")
        return jsonify({'message': f'Model creation failed: {str(e)}'}), 500
    
@model_bp.route('/<int:model_id>/generate', methods=['POST'])
@cross_origin()
@token_required
def generate_images(current_user, model_id: int): 
    """Generate images using a trained model"""
    try:
        # Check credits
        credit_service = get_credit_service()
        if not credit_service.use_credits(current_user, 'IMAGE_GENERATION'):
            return jsonify({'message': 'Insufficient credits for image generation'}), 403

        # Get model and verify ownership
        model = TrainedModel.query.get_or_404(model_id)
        if model.user_id != current_user.id:
            return jsonify({'message': 'Unauthorized'}), 403

        # Check if model is ready
        is_ready, message = model.is_ready_for_generation()
        if not is_ready:
            return jsonify({'message': message}), 400

        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        num_images = int(data.get('num_images', 1))
        if num_images < 1 or num_images > 15:  
            return jsonify({'message': 'Invalid number of images requested'}), 400

        prompt = data.get('prompt')
        if not prompt or not isinstance(prompt, str):
            return jsonify({'message': 'Valid prompt is required'}), 400

        # Enqueue generation job
        job_queue = get_job_queue()
        job_id = job_queue.enqueue_job(
            JobType.IMAGE_GENERATION,
            current_user.id,
            {
                'model_id': model.id,
                'model_version': model.version,
                'model_weights_path': model.weights_location.path,
                'num_images': num_images,
                'prompt': prompt,
                'parameters': data.get('parameters', {}),
            }
        )

        return jsonify({
            'message': 'Image generation started',
            'job_id': job_id,
            'model_id': model.id,
            'num_images': num_images
        }), 200

    except ValueError as e:
        logger.error(f"Invalid input: {str(e)}")
        return jsonify({'message': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
    
@model_bp.route('/<int:model_id>/images', methods=['GET'])
@cross_origin()
@token_required
def get_model_images(current_user, model_id: int):
    """Get all generated images for a model"""
    try:
        model = TrainedModel.query.get_or_404(model_id)
        if model.user_id != current_user.id:
            return jsonify({'message': 'Unauthorized'}), 403

        storage_service = get_storage_service()
        
        generated_images = GeneratedImage.query.filter_by(
            model_id=model_id,
            user_id=current_user.id
        ).order_by(GeneratedImage.created_at.desc()).all()

        return jsonify({
            'images': [{
                'id': img.id,
                'url': storage_service.get_public_url(img.storage_location),
                'prompt': img.prompt,
                'created_at': img.created_at.isoformat(),
                'parameters': img.generation_params
            } for img in generated_images]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching generated images: {str(e)}")
        return jsonify({'message': str(e)}), 500

@model_bp.route('/job/<job_id>/status', methods=['GET'])
@cross_origin()
@token_required
def get_job_status(current_user, job_id):
    """Get job status"""
    try:
        job_queue = get_job_queue()
        status = job_queue.get_job_status(job_id)
        
        if not status:
            return jsonify({'message': 'Job not found'}), 404
            
        if str(status['user_id']) != str(current_user.id):
            return jsonify({'message': 'Unauthorized'}), 403
            
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return jsonify({'message': str(e)}), 500

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
        'models': [model.to_dict() for model in models]
    }), 200

@model_bp.route('/stats', methods=['GET'])
@cross_origin()
@token_required
def get_job_stats(current_user):
    """Get job statistics for current user"""
    try:
        job_monitor = current_app.job_monitor
        stats = job_monitor.get_job_stats(current_user.id)
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting job stats: {str(e)}")
        return jsonify({'message': str(e)}), 500

@model_bp.route('/metrics', methods=['GET'])
@cross_origin()
@token_required
def get_job_metrics(current_user):
    """Get overall job metrics (admin only)"""
    try:
        # Add admin check here if needed
        job_monitor = current_app.job_monitor
        metrics = job_monitor.get_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'message': str(e)}), 500
    
@model_bp.route('/worker-status', methods=['GET'])
@cross_origin()
@token_required
def get_worker_status(current_user):
    """Get worker service status"""
    try:
        worker_service = get_worker_service()
        status = worker_service.get_status()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting worker status: {str(e)}")
        return jsonify({'message': str(e)}), 500
    
@model_bp.route('/<int:model_id>/cleanup', methods=['POST'])
@token_required
def cleanup_training_images(current_user, model_id):
    """Delete training images after successful model training"""
    model = TrainedModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
        
    if model.status != JobStatus.COMPLETED:
        return jsonify({'message': 'Cannot cleanup incomplete model'}), 400
        
    storage_service = get_storage_service()
    for image in model.training_images:
        storage_service.delete_file(image.storage_location)
        
    return jsonify({'message': 'Training images cleaned up'}), 200