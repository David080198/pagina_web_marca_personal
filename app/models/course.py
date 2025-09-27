from app.extensions import db
from datetime import datetime

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text)  # Contenido detallado del curso
    price = db.Column(db.Float, default=0.0)
    duration = db.Column(db.Integer)  # Duración en horas
    level = db.Column(db.String(50))  # Principiante, Intermedio, Avanzado
    language = db.Column(db.String(10), default='es')  # es, en
    image_url = db.Column(db.String(255))  # Cambiado de featured_image a image_url
    video_url = db.Column(db.String(255))  # URL del video promocional
    published = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Course {self.title}>'
