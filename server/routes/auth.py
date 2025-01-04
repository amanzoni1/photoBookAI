# server/routes/auth.py

from flask import request, jsonify, current_app, redirect
from flask_cors import cross_origin
from functools import wraps
from . import auth_bp, get_token_manager, get_oauth_service
from app import db
from models import User
import logging

logger = logging.getLogger(__name__)

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

@auth_bp.route('/google')
@cross_origin()
def google_auth():
    oauth = get_oauth_service().get_google_oauth()
    return oauth.authorize_redirect(current_app.config['GOOGLE_CALLBACK_URL'])

@auth_bp.route('/google/callback')
@cross_origin()
def google_callback():
    try:
        oauth = get_oauth_service().get_google_oauth()
        token = oauth.authorize_access_token()
        resp = oauth.get('https://www.googleapis.com/oauth2/v3/userinfo')
        user_info = resp.json()
        
        email = user_info.get('email')
        user = User.query.filter_by(email=email).first()
        if not user:
            # Use part before @ as default username, or do something else
            user = User(email=email, username=email.split('@')[0])
            db.session.add(user)
            db.session.commit()

        token_manager = get_token_manager()
        tokens = token_manager.create_token(user.id)

        # Redirect to front-end with tokens in query string
        front_end_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3001')
        return redirect(f"{front_end_url}/login?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}")
    except Exception as e:
        logger.error(f"Google callback error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/facebook')
@cross_origin()
def facebook_auth():
    oauth = get_oauth_service().get_facebook_oauth()
    return oauth.authorize_redirect(current_app.config['FACEBOOK_CALLBACK_URL'])

@auth_bp.route('/facebook/callback')
@cross_origin()
def facebook_callback():
    try:
        oauth = get_oauth_service().get_facebook_oauth()
        token = oauth.authorize_access_token()
        # Now fetch user profile
        resp = oauth.get('me?fields=id,name,email')
        user_info = resp.json()

        email = user_info.get('email')
        if not email:
            email = f"{user_info['id']}@facebook-oauth.local"

        user = User.query.filter_by(email=email).first()
        if not user:
            # Use FB name or id if you prefer
            username = user_info.get('name') or user_info['id']
            user = User(email=email, username=username)
            db.session.add(user)
            db.session.commit()

        token_manager = get_token_manager()
        tokens = token_manager.create_token(user.id)

        front_end_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3001')
        return redirect(f"{front_end_url}/login?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}")
    except Exception as e:
        logger.error(f"Facebook callback error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# # ----------------------------
# # APPLE
# # ----------------------------
# @auth_bp.route('/apple')
# @cross_origin()
# def apple_auth():
#     oauth = get_oauth_service().get_apple_oauth()
#     return oauth.authorize_redirect(current_app.config['APPLE_CALLBACK_URL'])

# @auth_bp.route('/apple/callback')
# @cross_origin()
# def apple_callback():
#     try:
#         oauth = get_oauth_service().get_apple_oauth()
#         token = oauth.authorize_access_token()
#         # Apple user info
#         resp = oauth.get('userinfo')
#         user_info = resp.json()

#         email = user_info.get('email')
#         if not email:
#             # Apple might not always provide email unless user consents
#             email = f"{user_info['sub']}@apple-oauth.local"

#         user = User.query.filter_by(email=email).first()
#         if not user:
#             username = user_info.get('sub')  # Or any other fallback
#             user = User(email=email, username=username)
#             db.session.add(user)
#             db.session.commit()

#         token_manager = get_token_manager()
#         tokens = token_manager.create_token(user.id)

#         front_end_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
#         return redirect(f"{front_end_url}/login?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}")
#     except Exception as e:
#         logger.error(f"Apple callback error: {str(e)}")
#         return jsonify({'error': str(e)}), 500