# server/services/credits.py

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from app import db
from models import User, CreditTransaction, CreditType

logger = logging.getLogger(__name__)

class CreditService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Credit package configurations
        self.credit_packages = {
            CreditType.MODEL_TRAINING.value: [  # Use .value for dict keys
                {'credits': 1, 'price': 9.99},
                {'credits': 5, 'price': 39.99},
                {'credits': 10, 'price': 69.99}
            ],
            CreditType.SINGLE_IMAGE.value: [
                {'credits': 10, 'price': 4.99},
                {'credits': 50, 'price': 19.99},
                {'credits': 100, 'price': 34.99}
            ],
            CreditType.PHOTOBOOK.value: [
                {'credits': 1, 'price': 14.99},
                {'credits': 3, 'price': 39.99},
                {'credits': 5, 'price': 59.99}
            ]
        }
    
    def add_credits(self, 
                   user: User, 
                   credit_type: CreditType, 
                   amount: int, 
                   payment_id: str,
                   price: float,
                   metadata: Optional[Dict] = None) -> CreditTransaction:
        """Add credits to user account"""
        try:
            # Create transaction record
            transaction = CreditTransaction(
                user_id=user.id,
                credit_type=credit_type,
                amount=amount,
                price=price,
                payment_id=payment_id,
                description=f"Purchase of {amount} {credit_type.value} credits",
                metadata_json=metadata
            )
            
            # Update user credits
            if credit_type == CreditType.MODEL_TRAINING:
                user.model_credits += amount
            elif credit_type == CreditType.SINGLE_IMAGE:
                user.image_credits += amount
            elif credit_type == CreditType.PHOTOBOOK:
                user.photobook_credits += amount
            
            db.session.add(transaction)
            db.session.commit()
            
            logger.info(f"Added {amount} {credit_type.value} credits to user {user.id}")
            return transaction
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding credits: {str(e)}")
            raise
    
    def use_credits(self,
                   user: User,
                   credit_type: CreditType,
                   amount: int = 1,
                   metadata: Optional[Dict] = None) -> bool:
        """Use credits for a service"""
        try:
            if not user.has_credits(credit_type, amount):
                return False
            
            # Create usage transaction
            transaction = CreditTransaction(
                user_id=user.id,
                credit_type=credit_type,
                amount=-amount,  # Negative amount for usage
                description=f"Used {amount} {credit_type.value} credits",
                metadata_json=metadata
            )
            
            # Update user credits
            if not user.use_credits(credit_type, amount):
                return False
            
            db.session.add(transaction)
            db.session.commit()
            
            logger.info(f"Used {amount} {credit_type.value} credits for user {user.id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error using credits: {str(e)}")
            return False
    
    def get_user_credits(self, user: User) -> Dict[str, int]:
        """Get user's credit balances"""
        return {
            'model_credits': user.model_credits,
            'image_credits': user.image_credits,
            'photobook_credits': user.photobook_credits
        }
    
    def get_credit_packages(self, credit_type: Optional[CreditType] = None) -> Dict[str, List[Dict]]:
        """Get available credit packages"""
        if credit_type:
            packages = self.credit_packages.get(credit_type.value, [])
            return {credit_type.value: packages}
            
        # Return all packages with string keys
        return {
            credit_type: packages 
            for credit_type, packages in self.credit_packages.items()
        }