# server/routes/photoshoot.py

from flask import request, jsonify
from flask_cors import cross_origin
import logging

from . import photoshoot_bp
from .auth import token_required
from app import db
from models import TrainedModel, PhotoBook, JobStatus, CreditType, GeneratedImage
from . import get_storage_service

logger = logging.getLogger(__name__)


@photoshoot_bp.route("/photobooks", methods=["GET"])
@cross_origin()
@token_required
def list_photobooks(current_user):
    """
    List all photobooks for current user.
    Images won't be returned unless the photobook is unlocked,
    but you can see the top-level data.
    """
    try:
        photobooks = (
            PhotoBook.query.filter_by(user_id=current_user.id)
            .order_by(PhotoBook.created_at.desc())
            .all()
        )

        return jsonify({"photobooks": [pb.to_dict() for pb in photobooks]}), 200

    except Exception as e:
        logger.error(f"Error listing photobooks: {str(e)}")
        return jsonify({"message": str(e)}), 500


@photoshoot_bp.route("/model/<int:model_id>/photobooks", methods=["GET"])
@cross_origin()
@token_required
def list_photobooks_for_model(current_user, model_id: int):
    """
    Return all photobooks for the given model, ensuring it belongs to current_user.
    """
    try:
        model = TrainedModel.query.get_or_404(model_id)
        if model.user_id != current_user.id:
            return jsonify({"message": "Unauthorized"}), 403

        photobooks = (
            PhotoBook.query.filter_by(user_id=current_user.id, model_id=model_id)
            .order_by(PhotoBook.created_at.desc())
            .all()
        )

        return jsonify({"photobooks": [pb.to_dict() for pb in photobooks]}), 200

    except Exception as e:
        logger.error(f"Error listing photobooks for model {model_id}: {str(e)}")
        return jsonify({"message": str(e)}), 500


@photoshoot_bp.route("/photobooks/<int:photobook_id>", methods=["GET"])
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
            return jsonify({"message": "Unauthorized"}), 403

        return jsonify(photobook.to_dict()), 200

    except Exception as e:
        logger.error(f"Error fetching photobook: {str(e)}")
        return jsonify({"message": str(e)}), 500


@photoshoot_bp.route("/photobooks/<int:photobook_id>/images", methods=["GET"])
@cross_origin()
@token_required
def get_photobook_images(current_user, photobook_id: int):
    """
    Return an array of images with presigned URLs
    for the photobook, if it is COMPLETED & unlocked.
    """
    try:
        photobook = PhotoBook.query.get_or_404(photobook_id)

        # Ensure ownership
        if photobook.user_id != current_user.id:
            return jsonify({"message": "Unauthorized"}), 403

        # Ensure photobook is completed/unlocked
        if photobook.status != JobStatus.COMPLETED or not photobook.is_unlocked:
            return jsonify({"message": "Photobook not available"}), 403

        storage_service = get_storage_service()

        # Build array of presigned URLs
        images = []
        for img in photobook.images:
            presigned_url = storage_service.get_download_url(
                img.storage_location, expires_in=3600  # 1 hour (adjust as needed)
            )
            images.append({"id": img.id, "url": presigned_url, "prompt": img.prompt})

        return (
            jsonify(
                {
                    "photobook_id": photobook_id,
                    "photobook_name": photobook.name,
                    "images": images,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching photobook images: {str(e)}")
        return jsonify({"message": str(e)}), 500


@photoshoot_bp.route("/photobooks/<int:photobook_id>/unlock", methods=["POST"])
@cross_origin()
@token_required
def unlock_photobook(current_user, photobook_id: int):
    """
    Unlock a locked photobook, if user has enough photoshoot credits.
    Deduct 1 photoshoot credit from user and set photobook.is_unlocked = True.
    """
    try:
        photobook = PhotoBook.query.get_or_404(photobook_id)

        # Check ownership
        if photobook.user_id != current_user.id:
            return jsonify({"message": "Unauthorized"}), 403

        # If already unlocked, no need to do anything
        if photobook.is_unlocked:
            return jsonify({"message": "Photobook already unlocked"}), 200

        # If not enough credits, return error
        from . import get_credit_service

        credit_service = get_credit_service()
        if not credit_service.use_credits(current_user, CreditType.PHOTOSHOOT, 1):
            return jsonify({"message": "Insufficient photoshoot credits"}), 403

        # Now set unlocked
        photobook.is_unlocked = True
        db.session.commit()

        return jsonify({"message": "Photobook unlocked successfully"}), 200

    except Exception as e:
        logger.error(f"Error unlocking photobook {photobook_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"message": "Failed to unlock photobook"}), 500


@photoshoot_bp.route("/photobooks/<int:photobook_id>", methods=["DELETE"])
@cross_origin()
@token_required
def delete_photobook(current_user, photobook_id: int):
    """
    Delete a photobook along with all associated generated images.
    """
    try:
        photobook = PhotoBook.query.get_or_404(photobook_id)
        if photobook.user_id != current_user.id:
            return jsonify({"message": "Unauthorized"}), 403

        storage_service = get_storage_service()

        # Retrieve and cache the storage locations for each image.
        image_storage_locations = [img.storage_location for img in photobook.images]

        # Delete all associated generated image records.
        for image in list(photobook.images):
            db.session.delete(image)
        db.session.commit()

        # Now delete each storage location from storage and the DB.
        for location in image_storage_locations:
            storage_service.delete_file(location)

        # Finally, delete the photobook record.
        db.session.delete(photobook)
        db.session.commit()

        return jsonify({"message": "Photobook deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting photobook {photobook_id}: {str(e)}")
        return jsonify({"message": "Failed to delete photobook"}), 500


@photoshoot_bp.route(
    "/photobooks/<int:photobook_id>/images/<int:image_id>", methods=["DELETE"]
)
@cross_origin()
@token_required
def delete_photobook_image(current_user, photobook_id: int, image_id: int):
    """
    Delete a single image from a photobook.
    """
    try:
        photobook = PhotoBook.query.get_or_404(photobook_id)
        if photobook.user_id != current_user.id:
            return jsonify({"message": "Unauthorized"}), 403

        # Query the image and cache its storage location
        image = GeneratedImage.query.filter_by(
            id=image_id, photobook_id=photobook_id
        ).first_or_404()
        storage_location = image.storage_location

        # Delete the image record first and commit.
        db.session.delete(image)
        db.session.commit()

        # Now delete the associated file and its storage location record.
        storage_service = get_storage_service()
        storage_service.delete_file(storage_location)

        return jsonify({"message": "Image deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Error deleting image {image_id} in photobook {photobook_id}: {str(e)}"
        )
        return jsonify({"message": "Failed to delete image"}), 500


# @photoshoot_bp.route('/model/<int:model_id>/photobooks', methods=['POST'])
# @cross_origin()
# @token_required
# def create_photobook(current_user, model_id: int):
#     """
#     Create a new themed photobook (photoshoot) for a given model.
#     """
#     try:
#         # Get model and verify ownership
#         model = TrainedModel.query.get_or_404(model_id)
#         if model.user_id != current_user.id:
#             return jsonify({'message': 'Unauthorized'}), 403

#         # Check if model is ready
#         is_ready, message = model.is_ready_for_generation()
#         if not is_ready:
#             return jsonify({'message': message}), 400

#         # Get request data
#         data = request.get_json()
#         if not data:
#             return jsonify({'message': 'No data provided'}), 400

#         # Validate theme name
#         theme_name = data.get('theme_name')
#         if not theme_name:
#             return jsonify({'message': 'Theme name is required'}), 400

#         # Verify theme exists
#         if theme_name not in PHOTOSHOOT_THEMES:
#             return jsonify({
#                 'message': 'Invalid theme',
#                 'available_themes': list(PHOTOSHOOT_THEMES.keys())
#             }), 400

#         # Check credits (Assuming you're using CreditType.PHOTOSHOOT or IMAGE)
#         credit_service = get_credit_service()
#         if not credit_service.use_credits(current_user, CreditType.PHOTOSHOOT, amount=IMAGES_PER_THEME):
#             return jsonify({'message': 'Insufficient credits for photoshoot generation'}), 403

#         # Create photobook record
#         photobook = PhotoBook(
#             user_id=current_user.id,
#             model_id=model_id,
#             name=f"Photoshoot - {theme_name}",
#             theme_name=theme_name,
#             status=JobStatus.PENDING,
#             is_unlocked=False  # Will be unlocked after generation or payment
#         )

#         db.session.add(photobook)
#         db.session.commit()

#         # Get theme prompts
#         theme_prompts = PHOTOSHOOT_THEMES[theme_name]

#         # Enqueue generation job
#         job_queue = get_job_queue()
#         job_id = job_queue.enqueue_job(
#             JobType.PHOTOBOOK_GENERATION,
#             current_user.id,
#             {
#                 'photobook_id': photobook.id,
#                 'model_id': model_id,
#                 'theme_name': theme_name,
#                 'prompts': theme_prompts,
#                 'model_weights_path': model.weights_location.path
#             }
#         )

#         return jsonify({
#             'message': 'Photoshoot generation started',
#             'photobook_id': photobook.id,
#             'job_id': job_id,
#             'theme': theme_name,
#             'num_images': IMAGES_PER_THEME
#         }), 200

#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Photoshoot creation error: {str(e)}")
#         return jsonify({'message': f'Photoshoot creation failed: {str(e)}'}), 500
