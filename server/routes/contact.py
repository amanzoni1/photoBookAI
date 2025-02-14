# server/routes/contact.py

from flask import request, jsonify, current_app
from flask_cors import cross_origin
import logging
from . import contact_bp
from . import get_email_service

logger = logging.getLogger(__name__)


@contact_bp.route("", methods=["POST"])
@cross_origin()
def contact():
    """
    Accepts JSON with { "name": "User Name", "email": "user@example.com", "message": "Your message here" }
    Processes the contact message (e.g., sends an email to support)
    """
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not name or not email or not message:
        return jsonify({"message": "All fields are required."}), 400

    try:
        email_service = get_email_service()
        email_service.send_email(
            to_email="a.manzoni1@proton.me",
            subject="New Contact Message",
            template_name="contact",
            context={"name": name, "email": email, "message": message},
        )
        logger.info(f"Contact message received from {email}")
        return jsonify({"message": "Your message has been sent. Thank you!"}), 200
    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}", exc_info=True)
        return (
            jsonify(
                {"message": "Failed to send your message. Please try again later."}
            ),
            500,
        )
