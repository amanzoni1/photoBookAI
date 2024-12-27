# server/app.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config
import logging

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()

logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Configure CORS
    CORS(app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    with app.app_context():
        # Initialize services first
        from routes import init_services
        init_services(app)

        # Then register blueprints
        from routes import init_app as init_routes
        init_routes(app)

        # Verify all services
        required_services = [
            'temp_manager',
            'storage_service',
            'storage_monitor',
            'credit_service',
            'token_manager',
            'job_queue',
            'worker_service',
            'job_monitor',
            'alert_service'
        ]

        for service in required_services:
            if not app.config.get(service):
                logger.error(f"{service} not initialized!")
                raise RuntimeError(f"{service} failed to initialize")
            else:
                logger.info(f"{service} initialized successfully")

    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)