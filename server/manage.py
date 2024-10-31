# server/manage.py

from flask.cli import FlaskGroup
from app import create_app, db
from models import User, StorageLocation, UserImage, TrainedModel, GenerationJob, GeneratedImage

cli = FlaskGroup(create_app=create_app)

@cli.command("create_db")
def create_db():
    """Create the database tables."""
    db.create_all()

@cli.command("drop_db")
def drop_db():
    """Drop the database tables."""
    db.drop_all()

if __name__ == '__main__':
    cli()