# server/routes/model/job_routes.py

from flask import request, jsonify, current_app
from flask_cors import cross_origin
import logging

from . import model_bp
from routes.auth import token_required
from services.queue import JobType
from models import TrainedModel
from routes import (
    get_job_queue,
    get_worker_service
)

logger = logging.getLogger(__name__)

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