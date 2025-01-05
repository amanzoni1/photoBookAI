# server/routes/photoshoot.py

from flask import request, jsonify
from flask_cors import cross_origin
import logging

from . import photoshoot_bp
from .auth import token_required
from app import db
from models import TrainedModel, PhotoBook, JobStatus, CreditType
from services.queue import JobType
from config import PHOTOSHOOT_THEMES, IMAGES_PER_THEME
from . import (
    get_job_queue,
    get_credit_service
)

logger = logging.getLogger(__name__)


@photoshoot_bp.route('/photobooks', methods=['GET'])
@cross_origin()
@token_required
def list_photobooks(current_user):
    """
    List all photobooks for current user.
    Images won't be returned unless the photobook is unlocked,
    but you can see the top-level data.
    """
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


@photoshoot_bp.route('/model/<int:model_id>/photobooks', methods=['GET'])
@cross_origin()
@token_required
def list_photobooks_for_model(current_user, model_id: int):
    """
    Return all photobooks for the given model, ensuring it belongs to current_user.
    """
    try:
        model = TrainedModel.query.get_or_404(model_id)
        if model.user_id != current_user.id:
            return jsonify({'message': 'Unauthorized'}), 403

        photobooks = PhotoBook.query.filter_by(
            user_id=current_user.id,
            model_id=model_id
        ).order_by(PhotoBook.created_at.desc()).all()
        
        return jsonify({
            'photobooks': [pb.to_dict() for pb in photobooks]
        }), 200

    except Exception as e:
        logger.error(f"Error listing photobooks for model {model_id}: {str(e)}")
        return jsonify({'message': str(e)}), 500


@photoshoot_bp.route('/model/<int:model_id>/photobooks', methods=['POST'])
@cross_origin()
@token_required
def create_photobook(current_user, model_id: int):
    """
    Create a new themed photobook (photoshoot) for a given model.
    """
    try:
        # Get model and verify ownership
        model = TrainedModel.query.get_or_404(model_id)
        if model.user_id != current_user.id:
            return jsonify({'message': 'Unauthorized'}), 403

        # Check if model is ready
        is_ready, message = model.is_ready_for_generation()
        if not is_ready:
            return jsonify({'message': message}), 400

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        # Validate theme name
        theme_name = data.get('theme_name')
        if not theme_name:
            return jsonify({'message': 'Theme name is required'}), 400
            
        # Verify theme exists
        if theme_name not in PHOTOSHOOT_THEMES:
            return jsonify({
                'message': 'Invalid theme',
                'available_themes': list(PHOTOSHOOT_THEMES.keys())
            }), 400

        # Check credits (Assuming you're using CreditType.PHOTOSHOOT or IMAGE)
        credit_service = get_credit_service()
        if not credit_service.use_credits(current_user, CreditType.PHOTOSHOOT, amount=IMAGES_PER_THEME):
            return jsonify({'message': 'Insufficient credits for photoshoot generation'}), 403

        # Create photobook record
        photobook = PhotoBook(
            user_id=current_user.id,
            model_id=model_id,
            name=f"Photoshoot - {theme_name}",
            theme_name=theme_name,
            status=JobStatus.PENDING,
            is_unlocked=False  # Will be unlocked after generation or payment
        )
        
        db.session.add(photobook)
        db.session.commit()

        # Get theme prompts
        theme_prompts = PHOTOSHOOT_THEMES[theme_name]

        # Enqueue generation job
        job_queue = get_job_queue()
        job_id = job_queue.enqueue_job(
            JobType.PHOTOBOOK_GENERATION,
            current_user.id,
            {
                'photobook_id': photobook.id,
                'model_id': model_id,
                'theme_name': theme_name,
                'prompts': theme_prompts,
                'model_weights_path': model.weights_location.path
            }
        )

        return jsonify({
            'message': 'Photoshoot generation started',
            'photobook_id': photobook.id,
            'job_id': job_id,
            'theme': theme_name,
            'num_images': IMAGES_PER_THEME
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Photoshoot creation error: {str(e)}")
        return jsonify({'message': f'Photoshoot creation failed: {str(e)}'}), 500


@photoshoot_bp.route('/photobooks/<int:photobook_id>', methods=['GET'])
@cross_origin()
@token_required
def get_photobook(current_user, photobook_id: int):
    """
    Get details (and possibly images) of a single photobook.
    If photobook.is_unlocked == True, images are included in 'to_dict()'.
    """
    try:
        photobook = PhotoBook.query.get_or_404(photobook_id)
        if photobook.user_id != current_user.id:
            return jsonify({'message': 'Unauthorized'}), 403
        
        return jsonify(photobook.to_dict()), 200

    except Exception as e:
        logger.error(f"Error fetching photobook: {str(e)}")
        return jsonify({'message': str(e)}), 500