# server/services/auth.py

from datetime import datetime, timedelta
import jwt
import redis
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TokenManager:
    def __init__(self, config):
        self.config = config
        self.redis_client = redis.Redis(
            host=config.get('REDIS_HOST', 'localhost'),
            port=config.get('REDIS_PORT', 6379),
            db=config.get('REDIS_DB', 0)
        )
        self.token_expiry = config.get('TOKEN_EXPIRY_HOURS', 1)
        self.refresh_expiry = config.get('REFRESH_TOKEN_DAYS', 30)
        self.secret_key = config['SECRET_KEY']

    def create_token(self, user_id: int) -> Dict[str, str]:
        """Create a new token pair (access and refresh tokens)"""
        try:
            access_token_exp = datetime.utcnow() + timedelta(hours=self.token_expiry)
            refresh_token_exp = datetime.utcnow() + timedelta(days=self.refresh_expiry)
            
            access_token = jwt.encode(
                {
                    'user_id': user_id,
                    'exp': access_token_exp,
                    'type': 'access'
                },
                self.secret_key,
                algorithm='HS256'
            )
            
            refresh_token = jwt.encode(
                {
                    'user_id': user_id,
                    'exp': refresh_token_exp,
                    'type': 'refresh'
                },
                self.secret_key,
                algorithm='HS256'
            )
            
            # Store refresh token in Redis
            self.redis_client.setex(
                f"refresh_token:{user_id}",
                timedelta(days=self.refresh_expiry),
                refresh_token
            )
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': self.token_expiry * 3600
            }
        except Exception as e:
            logger.error(f"Error creating tokens: {str(e)}")
            raise

    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict]:
        """Verify a token and return its payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            if payload.get('type') != token_type:
                return None
            
            if token_type == 'refresh':
                stored_token = self.redis_client.get(f"refresh_token:{payload['user_id']}")
                if not stored_token or stored_token.decode() != token:
                    return None
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.info("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None

    def revoke_tokens(self, user_id: int) -> bool:
        """Revoke all tokens for a user"""
        try:
            self.redis_client.delete(f"refresh_token:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Error revoking tokens: {str(e)}")
            return False

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Create new access token using refresh token"""
        try:
            payload = self.verify_token(refresh_token, 'refresh')
            if payload:
                return self.create_token(payload['user_id'])
            return None
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None