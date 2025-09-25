from app.extensions import db
from datetime import datetime

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(500))
    category = db.Column(db.String(50), nullable=False)  # 'research', 'automation'
    technologies = db.Column(db.String(500))  # Lista separada por comas
    github_url = db.Column(db.String(255))
    demo_url = db.Column(db.String(255))
    featured_image = db.Column(db.String(255))
    images = db.Column(db.Text)  # JSON con array de imágenes
    published = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Project {self.title}>'
