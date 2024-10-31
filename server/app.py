# server/app.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config

# Initialize Flask extensions
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
    CORS(app, 
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        # expose_headers=["Content-Range", "X-Content-Range"]
    )

    with app.app_context():
        # Initialize services first
        from routes import init_services
        init_services(app)
        
        # Then register blueprints
        from routes import init_app as init_routes
        init_routes(app)
        
        # Verify services
        if not app.config.get('storage_service'):
            app.logger.error("Storage service not initialized!")
        if not app.config.get('model_cache'):
            app.logger.error("Model cache not initialized!")
        if not app.config.get('storage_monitor'):
            app.logger.error("Storage monitor not initialized!")

    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)