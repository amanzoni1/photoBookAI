# server/services/auth.py

from datetime import datetime, timedelta
import jwt
from flask import current_app
from typing import Dict, Optional
import redis
from functools import wraps
from flask import request, jsonify

class TokenManager:
    def __init__(self, app=None):
        self.redis_client = redis.Redis(
            host=app.config.get('REDIS_HOST', 'localhost'),
            port=app.config.get('REDIS_PORT', 6379),
            db=app.config.get('REDIS_DB', 0)
        )
        self.token_expiry = app.config.get('TOKEN_EXPIRY_HOURS', 1)
        self.secret_key = app.config['SECRET_KEY']

    def create_token(self, user_id: int) -> Dict[str, str]:
        """Create a new token pair (access and refresh tokens)"""
        access_token_exp = datetime.utcnow() + timedelta(hours=self.token_expiry)
        refresh_token_exp = datetime.utcnow() + timedelta(days=30)
        
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
            timedelta(days=30),
            refresh_token
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': self.token_expiry * 3600
        }

    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict]:
        """Verify a token and return its payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check token type
            if payload.get('type') != token_type:
                return None
            
            # For refresh tokens, verify against Redis
            if token_type == 'refresh':
                stored_token = self.redis_client.get(f"refresh_token:{payload['user_id']}")
                if not stored_token or stored_token.decode() != token:
                    return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def revoke_tokens(self, user_id: int):
        """Revoke all tokens for a user"""
        self.redis_client.delete(f"refresh_token:{user_id}")

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Create new access token using refresh token"""
        payload = self.verify_token(refresh_token, 'refresh')
        if payload:
            return self.create_token(payload['user_id'])
        return None

def token_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        # Verify token
        token_manager = current_app.token_manager
        payload = token_manager.verify_token(token)
        
        if not payload:
            return jsonify({'message': 'Invalid or expired token'}), 401
        
        # Add user to request context
        from models import User
        current_user = User.query.get(payload['user_id'])
        
        if not current_user:
            return jsonify({'message': 'User not found'}), 401
        
        return f(current_user, *args, **kwargs)
        
    return decorated