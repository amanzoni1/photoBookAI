# server/routes/model/__init__.py

from flask import Blueprint

model_bp = Blueprint('model', __name__, url_prefix='/api/model')

from .model_training import *
from .photobook import *
from .single_img import *
from .job_routes import *
from .management import *