# server/routes/model/single_img.py

from flask import request, jsonify, current_app
from flask_cors import cross_origin
import logging

from . import model_bp
from routes.auth import token_required
from app import db
from models import TrainedModel, GeneratedImage, CreditType
from services.queue import JobType
from routes import (
    get_storage_service,
    get_job_queue,
    get_credit_service
)

logger = logging.getLogger(__name__)

@model_bp.route('/<int:model_id>/generate', methods=['POST'])
@cross_origin()
@token_required
def generate_image(current_user, model_id: int): 
    """Generate a single image using a trained model"""
    try:
        # Check single image credit
        credit_service = get_credit_service()
        if not credit_service.use_credits(current_user, CreditType.IMAGE, amount=1):
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

        prompt = data.get('prompt')
        if not prompt or not isinstance(prompt, str):
            return jsonify({'message': 'Valid prompt is required'}), 400

        # Optional generation parameters (like guidance_scale, steps, etc.)
        parameters = data.get('parameters', {})

        # Enqueue single image generation job
        job_queue = get_job_queue()
        job_id = job_queue.enqueue_job(
            JobType.IMAGE_GENERATION,
            current_user.id,
            {
                'model_id': model.id,
                'model_weights_path': model.weights_location.path,
                'num_images': 1,  # Always 1 for single image generation
                'prompt': prompt,
                'parameters': parameters
            }
        )

        return jsonify({
            'message': 'Image generation started',
            'job_id': job_id,
            'model_id': model.id
        }), 200

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