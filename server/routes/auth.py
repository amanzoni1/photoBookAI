# server/routes/auth.py

from flask import request, jsonify
from flask_cors import cross_origin
from functools import wraps
from . import auth_bp, get_token_manager
from app import db
from models import User


def token_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        token_manager = get_token_manager()
        payload = token_manager.verify_token(token)
        
        if not payload:
            return jsonify({'message': 'Invalid or expired token'}), 401
        
        current_user = User.query.get(payload['user_id'])
        if not current_user:
            return jsonify({'message': 'User not found'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


@auth_bp.route('/register', methods=['POST'])
@cross_origin()
def register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400

    user = User(email=email, username=username)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
@cross_origin()
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()

    if user and user.check_password(data.get('password')):
        token_manager = get_token_manager()
        tokens = token_manager.create_token(user.id)
        return jsonify(tokens), 200
    
    return jsonify({'message': 'Invalid email or password'}), 401

@auth_bp.route('/refresh', methods=['POST'])
@cross_origin()
def refresh_token():
    refresh_token = request.json.get('refresh_token')
    if not refresh_token:
        return jsonify({'message': 'Refresh token required'}), 400
    
    token_manager = get_token_manager()
    new_tokens = token_manager.refresh_access_token(refresh_token)
    
    if new_tokens:
        return jsonify(new_tokens), 200
    return jsonify({'message': 'Invalid refresh token'}), 401

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    token_manager = get_token_manager()
    token_manager.revoke_tokens(current_user.id)
    return jsonify({'message': 'Logged out successfully'}), 200