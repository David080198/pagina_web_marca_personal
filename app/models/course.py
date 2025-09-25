from app.extensions import db
from datetime import datetime

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(500))
    price = db.Column(db.Float, default=0.0)
    duration = db.Column(db.String(50))  # ej: "4 semanas", "20 horas"
    level = db.Column(db.String(50))  # Principiante, Intermedio, Avanzado
    featured_image = db.Column(db.String(255))
    syllabus = db.Column(db.Text)  # JSON con el contenido del curso
    published = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Course {self.title}>'
