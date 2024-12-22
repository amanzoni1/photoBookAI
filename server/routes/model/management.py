# server/routes/model/management.py

from flask import jsonify
from flask_cors import cross_origin
import logging

from . import model_bp
from routes.auth import token_required
from models import TrainedModel
from routes import get_model_cache

logger = logging.getLogger(__name__)

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

