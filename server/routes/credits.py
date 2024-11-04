# server/routes/credits.py
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import logging

from . import credits_bp
from .auth import token_required
from models import CreditType
from app import db
from . import get_credit_service
from config import IMAGES_PER_PHOTOBOOK, PRICES

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
        purchase_type = data.get('type')  # 'model' or 'photobook'
        quantity = int(data.get('quantity', 1))
        payment_id = data['payment_id']

        if purchase_type not in ['model', 'photobook']:
            return jsonify({'message': 'Invalid purchase type'}), 400

        credit_service = get_credit_service()
        if not credit_service:
            return jsonify({'message': 'Service unavailable'}), 503

        # Calculate price based on purchase type and quantity
        if purchase_type == 'model':
            credit_type = CreditType.MODEL
            price = PRICES['MODEL'] * quantity
            amount = quantity  
        else:  # photobook
            credit_type = CreditType.IMAGE
            price = PRICES['PHOTOBOOK'] * quantity
            amount = IMAGES_PER_PHOTOBOOK * quantity  

        transaction = credit_service.add_credits(
            current_user,
            credit_type,
            amount,
            payment_id,
            price,
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

    except KeyError as e:
        return jsonify({'message': f'Missing required field: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'message': f'Invalid value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Purchase error: {str(e)}")
        return jsonify({'message': str(e)}), 500