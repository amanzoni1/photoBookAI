# server/routes/credits.py
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import logging

from . import credits_bp
from .auth import token_required
from models import CreditType
from app import db
from . import get_credit_service
from config import PRICES

logger = logging.getLogger(__name__)

@credits_bp.route('/balance', methods=['GET'])
@cross_origin()
@token_required
def get_credit_balance(current_user):
    """Get user's credit balance"""
    credit_service = get_credit_service()
    balances = credit_service.get_user_credits(current_user)
    return jsonify(balances), 200

@credits_bp.route('/purchase', methods=['POST'])
@cross_origin()
@token_required
def purchase_credits(current_user):
    """Purchase credits"""
    try:
        data = request.get_json()
        purchase_type = data.get('type')  
        quantity = int(data.get('quantity', 1))
        payment_id = data['payment_id']

        if purchase_type not in ['MODEL', 'PHOTOSHOOT']:
            return jsonify({'message': 'Invalid purchase type'}), 400

        credit_type = CreditType[purchase_type]
        price = PRICES[purchase_type] * quantity

        credit_service = get_credit_service()
        if not credit_service:
            return jsonify({'message': 'Service unavailable'}), 503

        # Add debug logging
        logger.debug(f"Adding credits with type: {credit_type}, enum value: {credit_type.value}")

        transaction = credit_service.add_credits(
            user=current_user,
            credit_type=credit_type,  
            amount=quantity,
            payment_id=payment_id,
            price=price,
            metadata={
                'purchase_type': purchase_type,
                'quantity': quantity
            }
        )

        return jsonify({
            'message': 'Purchase successful',
            'transaction_id': transaction.id,
            'new_balance': credit_service.get_user_credits(current_user),
            'amount_paid': price
        }), 200

    except Exception as e:
        logger.error(f"Purchase error: {str(e)}")
        db.session.rollback()
        return jsonify({'message': 'Purchase failed. Please try again.'}), 500