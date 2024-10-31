# server/routes/credits.py

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import logging

from . import credits_bp
from .auth import token_required
from models import CreditType
from app import db
from . import get_credit_service

logger = logging.getLogger(__name__)

@credits_bp.route('/balance', methods=['GET'])
@cross_origin()
@token_required
def get_credit_balance(current_user):
    """Get user's credit balance"""
    credit_service = get_credit_service()
    balances = credit_service.get_user_credits(current_user)
    return jsonify(balances), 200

@credits_bp.route('/packages', methods=['GET'])
@cross_origin()
def get_credit_packages():
    """Get available credit packages"""
    credit_service = get_credit_service()
    if not credit_service:
        return jsonify({'message': 'Service unavailable'}), 503
        
    credit_type = request.args.get('type')
    
    try:
        if credit_type:
            # Always convert to uppercase for enum matching
            credit_type_enum = CreditType[credit_type.upper()]
            packages = credit_service.get_credit_packages(credit_type_enum)
        else:
            packages = credit_service.get_credit_packages()
        
        return jsonify(packages), 200
        
    except KeyError:
        return jsonify({'message': 'Invalid credit type'}), 400
    except Exception as e:
        logger.error(f"Error getting packages: {str(e)}")
        return jsonify({'message': str(e)}), 500

@credits_bp.route('/purchase', methods=['POST'])
@cross_origin()
@token_required
def purchase_credits(current_user):
    """Purchase credits"""
    try:
        data = request.get_json()
        # Convert credit_type to uppercase for enum matching
        credit_type = CreditType[data['credit_type'].upper()]
        amount = int(data['amount'])
        payment_id = data['payment_id']
        price = float(data['price'])
        
        credit_service = get_credit_service()
        if not credit_service:
            return jsonify({'message': 'Service unavailable'}), 503

        transaction = credit_service.add_credits(
            current_user,
            credit_type,
            amount,
            payment_id,
            price,
            metadata=data.get('metadata')
        )
        
        return jsonify({
            'message': 'Credits purchased successfully',
            'transaction_id': transaction.id,
            'new_balance': credit_service.get_user_credits(current_user)
        }), 200
        
    except KeyError as e:
        return jsonify({'message': f'Missing or invalid field: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'message': f'Invalid value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Purchase error: {str(e)}")
        return jsonify({'message': str(e)}), 500