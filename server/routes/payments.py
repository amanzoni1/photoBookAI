# server/routes/payments.py 

from flask import request, jsonify, current_app
from flask_cors import cross_origin
import logging

from . import payments_bp
from .auth import token_required
from . import get_payment_service, get_email_service
from app import db
from models import User

logger = logging.getLogger(__name__)

@payments_bp.route('/create-checkout-session', methods=['POST'])
@cross_origin()
@token_required
def create_checkout_session(current_user):
    """
    Create a Stripe Checkout session for purchasing a product/bundle.
    Expects JSON: { "product_id": "BUNDLE_MODEL_1_2PS" }
    Returns JSON: { "url": "<stripeCheckoutURL>" }
    """
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        if not product_id:
            return jsonify({'message': 'product_id is required'}), 400

        payment_service = get_payment_service()
        session_url, error = payment_service.create_checkout_session(
            user=current_user,
            product_id=product_id
        )
        if error:
            return jsonify({'message': error}), 400

        return jsonify({'url': session_url}), 200

    except Exception as e:
        logger.error("Error creating checkout session: %s", e, exc_info=True)
        return jsonify({'message': 'Failed to create checkout session'}), 500


@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe's webhook events, e.g. 'checkout.session.completed'.
    This is where we finalize the purchase and add credits to the user.
    """
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')

        payment_service = get_payment_service()
        email_service = get_email_service()

        event_data, error = payment_service.handle_webhook(
            payload=payload,
            signature=sig_header,
            email_service=email_service
        )
        if error:
            logger.error("Webhook error: %s", error)
            return jsonify({'message': error}), 400

        # If it's a completed checkout
        if event_data and event_data.get('type') == 'checkout.session.completed':
            user_id = event_data['user_id']
            product_id = event_data['product_id']
            payment_intent_id = event_data['payment_intent_id']
            credits_list = event_data['credits'] 

            # Fetch user from DB
            user = User.query.get(user_id)
            if not user:
                logger.error("Webhook: user %s not found in DB.", user_id)
                return jsonify({'message': 'User not found'}), 200

            # Award each credit item
            credit_service = current_app.config['credit_service']
            for cinfo in credits_list:
                try:
                    credit_service.add_credits(
                        user=user,
                        credit_type=cinfo['type'],
                        amount=cinfo['quantity'],
                        payment_id=payment_intent_id,
                        price=None,  # or parse from the session if desired
                        metadata={'product_id': product_id}
                    )
                except Exception as e:
                    logger.error("Error awarding credits via webhook: %s", e, exc_info=True)

            logger.info("Successfully awarded credits for user %s, product=%s", user_id, product_id)

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        logger.error("Webhook processing error: %s", e, exc_info=True)
        return jsonify({'message': 'Webhook processing failed'}), 500


@payments_bp.route('/products', methods=['GET'])
@cross_origin()
def list_products():
    """
    Return the list of available products/bundles so the frontend can show them.
    """
    payment_service = get_payment_service()
    all_products = payment_service.get_product_list()
    return jsonify(all_products), 200