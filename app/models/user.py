from app.extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Información personal
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    location = db.Column(db.String(100))
    website = db.Column(db.String(255))
    
    # Sistema de roles
    role = db.Column(db.String(20), default='user')  # user, premium, admin
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Preferencias
    newsletter_subscribed = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    preferred_language = db.Column(db.String(10), default='es')
    theme_preference = db.Column(db.String(20), default='auto')  # light, dark, auto
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Retorna el nombre completo del usuario"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username
    
    @property
    def display_name(self):
        """Nombre para mostrar en la interfaz"""
        return self.full_name
    
    def is_premium(self):
        """Verifica si el usuario tiene rol premium o admin"""
        return self.role in ['premium', 'admin'] or self.is_admin
    
    def can_comment(self):
        """Verifica si el usuario puede comentar"""
        return self.is_active and self.email_verified
    
    def get_avatar_url(self, size=150):
        """Retorna URL del avatar o gravatar por defecto"""
        if self.avatar_url:
            return self.avatar_url
        
        # Gravatar como fallback
        import hashlib
        email_hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"
    
    def update_last_seen(self):
        """Actualiza la última vez que se vio al usuario"""
        self.last_seen = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convierte el usuario a diccionario para APIs"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'bio': self.bio,
            'avatar_url': self.get_avatar_url(),
            'location': self.location,
            'website': self.website,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
