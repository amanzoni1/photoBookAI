# server/app.py

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}}, 
         supports_credentials=True, 
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])


    # Import and register blueprints
    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)