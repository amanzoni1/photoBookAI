# server/dev.py

import click
import os
import subprocess
from pathlib import Path

@click.group()
def cli():
    """Development helper commands"""
    pass

@cli.command()
def setup():
    """Set up development environment"""
    # Create cache directories
    cache_dir = Path(__file__).parent / 'cache' / 'models'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create uploads directory
    uploads_dir = Path(__file__).parent / 'uploads'
    uploads_dir.mkdir(exist_ok=True)
    
    click.echo("Created cache and uploads directories")

@cli.command()
def clean():
    """Clean cache and temporary files"""
    cache_dir = Path(__file__).parent / 'cache'
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True)
    click.echo("Cleaned cache directory")

@cli.command()
@click.option('--message', '-m', required=True, help='Migration message')
def migrate(message):
    """Create and apply database migration"""
    # Create migration
    subprocess.run(['flask', 'db', 'migrate', '-m', message])
    
    # Apply migration
    subprocess.run(['flask', 'db', 'upgrade'])
    
    click.echo("Migration complete")

@cli.command()
def reset_db():
    """Reset the database (WARNING: destroys all data)"""
    if click.confirm('This will delete all data. Continue?'):
        subprocess.run(['flask', 'db', 'downgrade', 'base'])
        subprocess.run(['flask', 'db', 'upgrade'])
        click.echo("Database reset complete")

if __name__ == '__main__':
    cli()