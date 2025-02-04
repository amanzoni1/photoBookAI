# server/routes/user.py

from flask import jsonify
from flask_cors import cross_origin
from . import user_bp
from .auth import token_required
from . import get_storage_monitor


@user_bp.route("/profile", methods=["GET"])
@cross_origin()
@token_required
def get_user_profile(current_user):
    """Get current user's profile"""
    return (
        jsonify(
            {
                "user": {
                    "id": current_user.id,
                    "email": current_user.email,
                    "username": current_user.username,
                }
            }
        ),
        200,
    )


@user_bp.route("/stats", methods=["GET"])
@cross_origin()
@token_required
def get_user_stats(current_user):
    """Get user's usage statistics"""

    try:
        storage_monitor = get_storage_monitor()
        stats = storage_monitor.get_user_stats(current_user.id)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
