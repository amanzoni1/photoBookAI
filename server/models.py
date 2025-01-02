# server/models.py

from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSONB
from enum import Enum as PyEnum
from typing import Optional, Dict, List
from config import IMAGES_PER_PHOTOBOOK
from sqlalchemy.types import Enum as SAEnum

class CreditType(PyEnum):
    MODEL = "MODEL"     
    PHOTOSHOOT = "PHOTOSHOOT"

class StorageType(PyEnum):
    DO_SPACES = "do_spaces"
    LOCAL = "local"

class JobStatus(PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

JobStatusEnum = SAEnum(
    JobStatus,
    name='jobstatus',
    create_type=False 
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class User(db.Model, UserMixin, TimestampMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Credit balances
    model_credits = db.Column(db.Integer, default=0)
    photoshoot_credits = db.Column(db.Integer, default=0)
    
    # Relationships
    uploaded_images = db.relationship('UserImage', backref='user', lazy=True)
    trained_models = db.relationship('TrainedModel', backref='user', lazy=True)
    generation_jobs = db.relationship('GenerationJob', backref='user', lazy=True)
    credit_transactions = db.relationship('CreditTransaction', backref='user', lazy=True)
    photobooks = db.relationship('PhotoBook', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_credits(self, credit_type: CreditType, amount: int = 1) -> bool:
        """Check if user has enough credits"""
        if credit_type == CreditType.MODEL:
            return self.model_credits >= amount
        elif credit_type == CreditType.PHOTOSHOOT:
            return self.photoshoot_credits >= amount
        return False
    
    def use_credits(self, credit_type: CreditType, amount: int = 1) -> bool:
        """Use credits if available"""
        if not self.has_credits(credit_type, amount):
            return False
            
        if credit_type == CreditType.MODEL:
            self.model_credits -= amount
        elif credit_type == CreditType.PHOTOSHOOT:
            self.photoshoot_credits -= amount
            
        db.session.commit()
        return True
    
class CreditTransaction(db.Model, TimestampMixin):
    __tablename__ = 'credit_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    credit_type = db.Column(db.Enum(CreditType), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  
    price = db.Column(db.Float)  
    payment_id = db.Column(db.String(255)) 
    description = db.Column(db.String(255))
    metadata_json = db.Column(JSONB)

class StorageLocation(db.Model, TimestampMixin):
    __tablename__ = 'storage_locations'

    id = db.Column(db.Integer, primary_key=True)
    storage_type = db.Column(db.Enum(StorageType), nullable=False)
    bucket = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(1000), nullable=False)
    file_size = db.Column(db.BigInteger)  
    content_type = db.Column(db.String(100))
    checksum = db.Column(db.String(64), nullable=True)
    metadata_json = db.Column(JSONB)

    def to_dict(self):
        return {
            "id": self.id,
            "storage_type": self.storage_type.value,
            "bucket": self.bucket,
            "path": self.path,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "checksum": self.checksum,
            "metadata_json": self.metadata_json
        }
    
    @property
    def full_path(self):
        return f"{self.bucket}/{self.path}"

class UserImage(db.Model, TimestampMixin):
    """Training images uploaded by users"""
    __tablename__ = 'user_images'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    storage_location_id = db.Column(db.Integer, db.ForeignKey('storage_locations.id'), nullable=False)
    
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    
    # Relationship to storage
    storage_location = db.relationship('StorageLocation', lazy=True)
    
    # Relationship to models this image was used to train
    trained_models = db.relationship(
        'TrainedModel',
        secondary='model_training_images',
        back_populates='training_images'
    )

class TrainedModel(db.Model, TimestampMixin):
    __tablename__ = 'trained_models'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)  
    version = db.Column(db.String(50), default='1.0') 
    
    # Model file (.safetensors) storage
    weights_location_id = db.Column(db.Integer, db.ForeignKey('storage_locations.id'))
    status = db.Column(JobStatusEnum, default=JobStatus.PENDING.value)
    
    # Training metadata
    training_started_at = db.Column(db.DateTime(timezone=True))
    training_completed_at = db.Column(db.DateTime(timezone=True))
    error_message = db.Column(db.Text)
    config = db.Column(JSONB)
    metrics = db.Column(JSONB)
    
    # Relationships
    weights_location = db.relationship('StorageLocation', lazy=True)
    training_images = db.relationship(
        'UserImage',
        secondary='model_training_images',
        back_populates='trained_models'
    )
    generated_images = db.relationship('GeneratedImage', backref='model', lazy=True)

    def is_ready_for_generation(self) -> tuple[bool, str]:
        """Check if model is ready for generation"""
        if self.status != JobStatus.COMPLETED:
            return False, f"Model is not ready (status: {self.status.value})"
        if not self.weights_location:
            return False, "Model files not found"
        if not self.training_completed_at:
            return False, "Training not completed"
        return True, "Model is ready"

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'training_started_at': self.training_started_at.isoformat() if self.training_started_at else None,
            'training_completed_at': self.training_completed_at.isoformat() if self.training_completed_at else None,
            'config': self.config,
            'metrics': self.metrics,
            'error_message': self.error_message
        }
    
class PhotoBook(db.Model, TimestampMixin):
    """Collection of themed images generated together"""
    __tablename__ = 'photobooks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('trained_models.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(JobStatusEnum, default=JobStatus.PENDING.value)
    theme_name = db.Column(db.String(100), nullable=False)
    is_unlocked = db.Column(db.Boolean, default=False)
    
    # Relationships
    model = db.relationship('TrainedModel', lazy=True)
    images = db.relationship('GeneratedImage', backref='photobook', lazy='joined')

    def to_dict(self) -> Dict:
        """Convert photobook to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'theme_name': self.theme_name,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'is_unlocked': self.is_unlocked
        }
        
        # Only include images if photobook is unlocked
        if self.is_unlocked:
            data['images'] = [{
                'id': img.id,
                'storage_path': img.storage_location.full_path,
                'prompt': img.prompt
            } for img in self.images]
        else:
            data['images'] = []  # Empty list for locked photobooks
            
        return data

    @property
    def theme_prompts(self) -> List[str]:
        """Get prompts for this theme from config"""
        from config import PHOTOSHOOT_THEMES
        return PHOTOSHOOT_THEMES.get(self.theme_name, [])
    
class GeneratedImage(db.Model, TimestampMixin):
    """Images generated using trained models"""
    __tablename__ = 'generated_images'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('trained_models.id'), nullable=False)
    photobook_id = db.Column(db.Integer, db.ForeignKey('photobooks.id'), nullable=True)
    storage_location_id = db.Column(db.Integer, db.ForeignKey('storage_locations.id'), nullable=False)
    generation_job_id = db.Column(db.Integer, db.ForeignKey('generation_jobs.id'), nullable=True)
    
    generation_params = db.Column(JSONB)
    prompt = db.Column(db.Text)
    
    # Relationships
    storage_location = db.relationship('StorageLocation', lazy=True)
    generation_job = db.relationship('GenerationJob', back_populates='generated_images')

class GenerationJob(db.Model, TimestampMixin):
    __tablename__ = 'generation_jobs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('trained_models.id'), nullable=False)
    
    prompt = db.Column(db.Text, nullable=False)
    status = db.Column(JobStatusEnum, default=JobStatus.PENDING.value)
    
    started_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))
    error_message = db.Column(db.Text)
    
    # Generation parameters
    parameters = db.Column(JSONB)
    
    # Relationships
    trained_model = db.relationship('TrainedModel', lazy=True)
    generated_images = db.relationship('GeneratedImage', back_populates='generation_job', lazy=True)


# Association tables
model_training_images = db.Table('model_training_images',
    db.Column('model_id', db.Integer, db.ForeignKey('trained_models.id'), primary_key=True),
    db.Column('image_id', db.Integer, db.ForeignKey('user_images.id'), primary_key=True),
    db.Column('created_at', db.DateTime(timezone=True), default=datetime.utcnow)
)


# Create indexes
db.Index('idx_user_images_user_id', UserImage.user_id)
db.Index('idx_trained_models_user_id', TrainedModel.user_id)
db.Index('idx_generation_jobs_user_id', GenerationJob.user_id)
db.Index('idx_generation_jobs_status', GenerationJob.status)
db.Index('idx_storage_locations_path', StorageLocation.path)
db.Index('idx_generated_images_model', GeneratedImage.model_id)
db.Index('idx_generated_images_user', GeneratedImage.user_id)
db.Index('idx_generated_images_photobook', GeneratedImage.photobook_id)
db.Index('idx_photobooks_model', PhotoBook.model_id)