# server/routes.py

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from app import db, bcrypt
from models import User
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename

import os
import jwt
from datetime import datetime, timedelta
from config import Config
from functools import wraps

main = Blueprint('main', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # JWT is passed in the request header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]  # Assuming 'Bearer <token>'

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


@main.route('/api/register', methods=['POST'])
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

@main.route('/api/login', methods=['POST'])
@cross_origin()
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        # Generate JWT token
        token = jwt.encode(
            {
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=1)
            },
            Config.SECRET_KEY,
            algorithm='HS256'
        )
        return jsonify({'token': token}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

@main.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@main.route('/api/user', methods=['GET'])
@cross_origin()
@token_required
def get_user(current_user):
    user_data = {
        'id': current_user.id,
        'email': current_user.email,
        'username': current_user.username
    }
    return jsonify({'user': user_data}), 200



@main.route('/api/create-model', methods=['POST'])
@cross_origin()
@token_required
def create_model(current_user):
    if 'files' not in request.files:
        return jsonify({'message': 'No files part in the request'}), 400

    files = request.files.getlist('files')
    name = request.form.get('name')
    age_years = request.form.get('ageYears')
    age_months = request.form.get('ageMonths')

    if not name:
        return jsonify({'message': 'Name is required'}), 400

    if not age_years and not age_months:
        return jsonify({'message': 'Please provide either age in years or months'}), 400

    # Proceed with handling the files and other logic
    # Save files
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            saved_files.append(filepath)
        else:
            return jsonify({'message': 'Invalid file type'}), 400

    # Simulate AI training process
    print(f"Started AI training for user {current_user.id}")

    # Return success message
    return jsonify({'message': 'Model training started successfully'}), 200


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route('/api/generated-images', methods=['GET'])
@cross_origin()
@token_required
def get_generated_images(current_user):
    # For now, we'll return an empty list or some placeholder data
    images = [
        # {'id': 1, 'url': 'http://example.com/image1.jpg'},
        # Add actual image URLs after implementing storage
    ]
    return jsonify({'images': images}), 200