# server/routes/model.py

from flask import request, jsonify, current_app
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from datetime import datetime
import logging
import shutil
from PIL import Image 

from . import model_bp
from .auth import token_required
from app import db
from models import TrainedModel, JobStatus, GeneratedImage, PhotoBook, CreditType
from services.queue import JobType
from config import IMAGES_PER_PHOTOBOOK
from . import (
    get_storage_service,
    get_model_cache,
    get_job_queue,
    get_credit_service,
    get_worker_service,
    get_temp_manager  
)

logger = logging.getLogger(__name__)

def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@model_bp.route('/training', methods=['POST'])
@cross_origin()
@token_required
def create_model(current_user):
    """Create model from uploaded training images"""
    credit_service = get_credit_service()
    job_queue = get_job_queue()
    temp_manager = get_temp_manager()
    temp_dir = None
    
    try:
        # Get request data
        data = request.form
        files = request.files.getlist('files')
        name = data.get('name')
        age_years = data.get('ageYears')
        age_months = data.get('ageMonths')

        if not name:
            return jsonify({'message': 'Name is required'}), 400
        if not age_years and not age_months:
            return jsonify({'message': 'Please provide either age in years or months'}), 400
        if not files:
            return jsonify({'message': 'No files provided'}), 400

        # Create temporary directory for this job
        temp_dir = temp_manager.create_temp_dir() 
        
        with db.session.begin_nested():
            # Check and deduct credits
            if not credit_service.use_credits(current_user, CreditType.MODEL):
                return jsonify({'message': 'Insufficient credits for model training'}), 403

            file_info = []
            for file in files:
                if file and allowed_file(file.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
                    filename = secure_filename(file.filename)
                    temp_path = temp_dir / filename
                    file.save(temp_path)
                    
                    with Image.open(temp_path) as img:
                        file_info.append({
                            'path': str(temp_path),
                            'original_filename': filename,
                            'width': img.width,
                            'height': img.height,
                            'format': img.format
                        })
                else:
                    raise ValueError('Invalid file type')

            # Create model record
            model = TrainedModel(
                user_id=current_user.id,
                name=name,
                version='1.0',
                status=JobStatus.PENDING,
                config={
                    'age_years': age_years,
                    'age_months': age_months,
                    'training_images': len(file_info)
                }
            )
            db.session.add(model)

        db.session.commit()

        # Enqueue job
        job_id = job_queue.enqueue_job(
            JobType.MODEL_TRAINING,
            current_user.id,
            {
                'model_id': model.id,
                'file_info': file_info,
                'name': name,
                'config': model.config,
                'temp_dir': str(temp_dir)  # Pass the temp directory path
            }
        )

        logger.info(f"Queued training job {job_id} for user {current_user.id}, model {model.id}")

        return jsonify({
            'message': 'Model training started successfully',
            'model_id': model.id,
            'job_id': job_id,
            'training_images': len(file_info)
        }), 200

    except Exception as e:
        # Cleanup temp directory in case of error
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup temp directory {temp_dir}: {cleanup_error}")
                
        db.session.rollback()
        logger.error(f"Model creation error: {str(e)}")
        return jsonify({'message': f'Model creation failed: {str(e)}'}), 500
    
@model_bp.route('/<int:model_id>/photobook', methods=['POST'])
@cross_origin()
@token_required
def create_photobook(current_user, model_id: int):
    """Create a new photobook with batch image generation"""
    try:
        # Get model and verify ownership
        model = TrainedModel.query.get_or_404(model_id)
        if model.user_id != current_user.id:
            return jsonify({'message': 'Unauthorized'}), 403

        # Check if model is ready
        is_ready, message = model.is_ready_for_generation()
        if not is_ready:
            return jsonify({'message': message}), 400

        # Check credits for photobook
        credit_service = get_credit_service()
        if not credit_service.use_credits(current_user, CreditType.IMAGE, amount=IMAGES_PER_PHOTOBOOK):
            return jsonify({'message': 'Insufficient credits for photobook generation'}), 403

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        name = data.get('name')
        prompt = data.get('prompt')
        style_config = data.get('style_config', {})

        if not name or not prompt:
            return jsonify({'message': 'Name and prompt are required'}), 400

        # Create photobook record
        photobook = PhotoBook(
            user_id=current_user.id,
            model_id=model_id,
            name=name,
            prompt=prompt,
            style_config=style_config,
            status=JobStatus.PENDING
        )
        
        db.session.add(photobook)
        db.session.commit()

        # Enqueue batch generation job
        job_queue = get_job_queue()
        job_id = job_queue.enqueue_job(
            JobType.PHOTOBOOK_GENERATION,
            current_user.id,
            {
                'photobook_id': photobook.id,
                'model_id': model_id,
                'prompt': prompt,
                'style_config': style_config,
                'num_images': IMAGES_PER_PHOTOBOOK
            }
        )

        logger.info(f"Queued photobook generation {job_id} for user {current_user.id}, model {model_id}")

        return jsonify({
            'message': 'Photobook generation started',
            'photobook_id': photobook.id,
            'job_id': job_id
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Photobook creation error: {str(e)}")
        return jsonify({'message': f'Photobook creation failed: {str(e)}'}), 500


@model_bp.route('/photobook/<int:photobook_id>', methods=['GET'])
@cross_origin()
@token_required
def get_photobook(current_user, photobook_id: int):
    """Get photobook details and images"""
    try:
        photobook = PhotoBook.query.get_or_404(photobook_id)
        if photobook.user_id != current_user.id:
            return jsonify({'message': 'Unauthorized'}), 403

        storage_service = get_storage_service()
        
        # Get all images with their URLs
        photobook_data = photobook.to_dict()
        photobook_data['images'] = [{
            'id': img.id,
            'url': storage_service.get_public_url(img.storage_location),
            'prompt': img.prompt,
            'created_at': img.created_at.isoformat()
        } for img in photobook.images]

        return jsonify(photobook_data), 200

    except Exception as e:
        logger.error(f"Error fetching photobook: {str(e)}")
        return jsonify({'message': str(e)}), 500
    
@model_bp.route('/<int:model_id>/generate', methods=['POST'])
@cross_origin()
@token_required
def generate_images(current_user, model_id: int): 
    """Generate images using a trained model"""
    try:
        # Check credits
        credit_service = get_credit_service()
        if not credit_service.use_credits(current_user, CreditType.IMAGE):
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

@model_bp.route('/models', methods=['GET'])
@cross_origin()
@token_required
def list_models(current_user):
    """List user's trained models"""
    try:
        models = TrainedModel.query.filter_by(
            user_id=current_user.id
            ).order_by(TrainedModel.created_at.desc()).all()
        
        return jsonify({
            'models': [model.to_dict() for model in models]
        }), 200

    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return jsonify({'message': str(e)}), 500

@model_bp.route('/photobooks', methods=['GET'])
@cross_origin()
@token_required
def list_photobooks(current_user):
    """List all photobooks for current user"""
    try:
        photobooks = PhotoBook.query.filter_by(
            user_id=current_user.id
        ).order_by(PhotoBook.created_at.desc()).all()

        return jsonify({
            'photobooks': [pb.to_dict() for pb in photobooks]
        }), 200

    except Exception as e:
        logger.error(f"Error listing photobooks: {str(e)}")
        return jsonify({'message': str(e)}), 500

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