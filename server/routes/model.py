# server/routes/model.py

from flask import request, jsonify, current_app
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
import shutil
from PIL import Image
import logging

from . import model_bp
from .auth import token_required
from app import db
from models import TrainedModel, JobStatus, CreditType
from services.queue import JobType
from . import get_storage_service, get_job_queue, get_credit_service, get_temp_manager

logger = logging.getLogger(__name__)


def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """(Use same allowed_file logic)"""
    if allowed_extensions is None:
        allowed_extensions = {"png", "jpg", "jpeg"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@model_bp.route("/training", methods=["POST"])
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
        files = request.files.getlist("files")
        name = data.get("name")
        age_years = data.get("ageYears")
        age_months = data.get("ageMonths")
        sex = data.get("sex")

        if not name:
            return jsonify({"message": "Name is required"}), 400
        if not sex:
            return jsonify({"message": "Sex is required"}), 400
        if not age_years and not age_months:
            return (
                jsonify({"message": "Please provide either age in years or months"}),
                400,
            )
        if not files:
            return jsonify({"message": "No files provided"}), 400

        # Create temporary directory for this job
        temp_dir = temp_manager.create_temp_dir()

        with db.session.begin_nested():
            # Check and deduct credits
            if not credit_service.use_credits(current_user, CreditType.MODEL):
                return (
                    jsonify({"message": "Insufficient credits for model training"}),
                    403,
                )

            file_info = []
            for file in files:
                if file and allowed_file(
                    file.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
                ):
                    filename = secure_filename(file.filename)
                    temp_path = temp_dir / filename
                    file.save(temp_path)

                    with Image.open(temp_path) as img:
                        file_info.append(
                            {
                                "path": str(temp_path),
                                "original_filename": filename,
                                "width": img.width,
                                "height": img.height,
                                "format": img.format,
                            }
                        )
                else:
                    raise ValueError("Invalid file type")

            # Create model record
            model = TrainedModel(
                user_id=current_user.id,
                name=name,
                version="1.0",
                status=JobStatus.PENDING,
                config={
                    "age_years": age_years,
                    "age_months": age_months,
                    "sex": sex,
                    "training_images": len(file_info),
                },
            )
            db.session.add(model)

        db.session.commit()

        # Enqueue job
        job_id = job_queue.enqueue_job(
            JobType.MODEL_TRAINING,
            current_user.id,
            {
                "model_id": model.id,
                "file_info": file_info,
                "name": name,
                "config": model.config,
                "temp_dir": str(temp_dir),
            },
        )

        logger.info(
            f"Queued training job {job_id} for user {current_user.id}, model {model.id}"
        )

        return (
            jsonify(
                {
                    "message": "Model training started successfully",
                    "model_id": model.id,
                    "job_id": job_id,
                    "training_images": len(file_info),
                }
            ),
            200,
        )

    except Exception as e:
        # Cleanup temp directory in case of error
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.error(
                    f"Failed to cleanup temp directory {temp_dir}: {cleanup_error}"
                )

        db.session.rollback()
        logger.error(f"Model creation error: {str(e)}")
        return jsonify({"message": f"Model creation failed: {str(e)}"}), 500


@model_bp.route("/<int:model_id>/cleanup", methods=["POST"])
@token_required
def cleanup_training_images(current_user, model_id):
    """Delete training images after successful model training"""
    model = TrainedModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403

    if model.status != JobStatus.COMPLETED:
        return jsonify({"message": "Cannot cleanup incomplete model"}), 400

    storage_service = get_storage_service()
    for image in model.training_images:
        storage_service.delete_file(image.storage_location)

    return jsonify({"message": "Training images cleaned up"}), 200


@model_bp.route("/models", methods=["GET"])
@cross_origin()
@token_required
def list_models(current_user):
    """List user's trained models"""
    try:
        models = (
            TrainedModel.query.filter_by(user_id=current_user.id)
            .order_by(TrainedModel.created_at.desc())
            .all()
        )

        return jsonify({"models": [model.to_dict() for model in models]}), 200

    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return jsonify({"message": str(e)}), 500


@model_bp.route("/<int:model_id>", methods=["GET"])
@cross_origin()
@token_required
def get_model(current_user, model_id):
    """Fetch a single model by ID (ensuring it belongs to current_user)."""
    model = TrainedModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403
    return jsonify(model.to_dict()), 200
