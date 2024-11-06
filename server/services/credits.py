# server/services/credits.py

from typing import Optional, Dict, Any
import logging
from datetime import datetime

from app import db
from models import User, CreditTransaction, CreditType
from config import IMAGES_PER_PHOTOBOOK

logger = logging.getLogger(__name__)

class CreditService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.images_per_photobook = config.get('IMAGES_PER_PHOTOBOOK', 15)
        self.prices = config.get('PRICES', {
            'MODEL': 24.99,
            'PHOTOBOOK': 3.99
        })
    
    def add_credits(self, 
                user: User, 
                credit_type: CreditType,  
                amount: int, 
                payment_id: str,
                price: float,
                metadata: Optional[Dict] = None) -> CreditTransaction:
        """Add credits to user account"""
        try:
            if not isinstance(credit_type, CreditType):
                raise ValueError(f"Invalid credit type: {credit_type}")

            logger.debug(f"Creating transaction with credit_type: {credit_type}, value: {credit_type.value}")
            
            transaction = CreditTransaction(
                user_id=user.id,
                credit_type=credit_type,  
                amount=amount,
                price=price,
                payment_id=payment_id,
                description=self._get_purchase_description(credit_type, amount),
                metadata_json=metadata
            )
            
            if credit_type == CreditType.MODEL:
                user.model_credits += amount
                user.image_credits += 2 * self.images_per_photobook  # Bonus images
            elif credit_type == CreditType.IMAGE:
                user.image_credits += amount
            
            db.session.add(transaction)
            db.session.commit()
            db.session.refresh(user) 
            
            logger.info(f"Added {amount} {credit_type.value} credits to user {user.id}")
            return transaction
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding credits: {str(e)}")
            raise
    
    def use_credits(self, user: User, credit_type: CreditType, amount: int = 1, metadata: Optional[Dict] = None) -> bool:
        """Use credits for a service"""
        try:
            logger.debug(f"User {user.id} before deduction: {user.model_credits} model credits, {user.image_credits} image credits")
            
            if not user.has_credits(credit_type, amount):
                logger.debug(f"User {user.id} has insufficient credits for {credit_type.value}")
                return False
            
            # Deduct credits
            transaction = CreditTransaction(
                user_id=user.id,
                credit_type=credit_type,
                amount=-amount,  # Negative for deduction
                description=self._get_usage_description(credit_type, amount),
                metadata_json=metadata
            )
            
            if credit_type == CreditType.MODEL:
                user.model_credits -= amount
            elif credit_type == CreditType.IMAGE:
                user.image_credits -= amount
            
            db.session.add(transaction)
            
            logger.debug(f"User {user.id} after deduction: {user.model_credits} model credits, {user.image_credits} image credits")
            logger.info(f"Used {amount} {credit_type.value} credits for user {user.id}")
            return True
                
        except Exception as e:
            logger.error(f"Error using credits: {str(e)}")
            return False
    
    def _get_purchase_description(self, credit_type: CreditType, amount: int) -> str:
        """Get descriptive message for purchase"""
        if credit_type == CreditType.MODEL:
            return f"Purchase of {amount} model credit(s) with {2 * IMAGES_PER_PHOTOBOOK} bonus images"
        elif credit_type == CreditType.IMAGE:
            photobooks = amount // IMAGES_PER_PHOTOBOOK
            remaining = amount % IMAGES_PER_PHOTOBOOK
            if remaining == 0:
                return f"Purchase of {photobooks} photobook credit(s)"
            return f"Purchase of {amount} image credits"

    def _get_usage_description(self, credit_type: CreditType, amount: int) -> str:
        """Get descriptive message for usage"""
        if credit_type == CreditType.MODEL:
            return f"Used {amount} model credit(s)"
        elif credit_type == CreditType.IMAGE:
            if amount == IMAGES_PER_PHOTOBOOK:
                return "Generated 1 photobook"
            return f"Generated {amount} image(s)"
    
    def get_user_credits(self, user: User) -> Dict[str, int]:
        """Get user's credit balances"""
        return {
            'model_credits': user.model_credits,
            'image_credits': user.image_credits,
            'available_photobooks': user.available_photobooks
        }
    