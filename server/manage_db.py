# server/manage_db.py

import click
from flask.cli import FlaskGroup
from app import create_app, db
from models import User, StorageLocation, UserImage, TrainedModel, GenerationJob, GeneratedImage
import os
from pathlib import Path
import shutil

cli = FlaskGroup(create_app=create_app)

@cli.command("reset-db")
def reset_db():
    """Reset database and migrations"""
    if click.confirm('This will delete all data and migrations. Continue?', abort=True):
        # Remove migrations directory
        migrations_dir = Path('./migrations')
        if migrations_dir.exists():
            shutil.rmtree(migrations_dir)
            click.echo("Removed migrations directory")
        
        # Drop and recreate database
        db.drop_all()
        db.create_all()
        click.echo("Reset database tables")
        
        # Initialize migrations
        os.system('flask db init')
        click.echo("Initialized new migrations directory")
        
        # Create initial migration
        os.system('flask db migrate -m "Initial migration"')
        click.echo("Created initial migration")
        
        # Apply migration
        os.system('flask db upgrade')
        click.echo("Applied migration")

@cli.command("clean-migrate")
def clean_migrate():
    """Create a new migration after cleaning compiled Python files"""
    # Remove *.pyc files
    os.system('find . -type f -name "*.pyc" -delete')
    os.system('find . -type d -name "__pycache__" -delete')
    
    # Create new migration
    message = click.prompt('Enter migration message', default='Update models')
    os.system(f'flask db migrate -m "{message}"')
    
    # Show generated migration
    latest_migration = max(Path('./migrations/versions').glob('*.py'))
    click.echo(f"\nGenerated migration: {latest_migration}")
    
    # Ask to apply
    if click.confirm('Would you like to apply this migration?', default=True):
        os.system('flask db upgrade')
        click.echo("Migration applied successfully")

@cli.command("show-models")
def show_models():
    """Show current database models"""
    click.echo("\nCurrent Models:")
    for model in [User, StorageLocation, UserImage, TrainedModel, 
                 GenerationJob, GeneratedImage]:
        click.echo(f"\n{model.__name__}:")
        for column in model.__table__.columns:
            click.echo(f"  - {column.name}: {column.type}")

@cli.command("verify-migrations")
def verify_migrations():
    """Verify migrations match current models"""
    from flask_migrate import current
    from alembic.migration import MigrationContext
    from sqlalchemy import inspect
    
    # Get current database tables
    inspector = inspect(db.engine)
    db_tables = inspector.get_table_names()
    
    # Get model tables
    model_tables = db.Model.metadata.tables.keys()
    
    # Compare
    click.echo("\nChecking database status:")
    click.echo(f"Current migration: {current()}")
    click.echo("\nTables in models but not in database:")
    for table in set(model_tables) - set(db_tables):
        click.echo(f"  - {table}")
    
    click.echo("\nTables in database but not in models:")
    for table in set(db_tables) - set(model_tables):
        click.echo(f"  - {table}")

if __name__ == '__main__':
    cli()