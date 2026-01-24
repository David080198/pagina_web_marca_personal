from app.extensions import db
from datetime import datetime

class Like(db.Model):
    """Modelo para gestionar likes en contenido (blogs, proyectos, cursos)"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Usuario que dio like
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Contenido polimórfico
    content_type = db.Column(db.String(20), nullable=False)  # 'blog', 'course', 'project'
    content_id = db.Column(db.Integer, nullable=False)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con usuario
    user = db.relationship('User', backref=db.backref('likes', lazy='dynamic'))
    
    # Índice único para evitar duplicados
    __table_args__ = (
        db.UniqueConstraint('user_id', 'content_type', 'content_id', name='unique_like'),
    )
    
    def get_content_object(self):
        """Retorna el objeto al que pertenece el like"""
        if self.content_type == 'blog':
            from app.models.blog import BlogPost
            return BlogPost.query.get(self.content_id)
        elif self.content_type == 'course':
            from app.models.course import Course
            return Course.query.get(self.content_id)
        elif self.content_type == 'project':
            from app.models.project import Project
            return Project.query.get(self.content_id)
        return None
    
    def _get_content_url(self, content):
        """Genera la URL del contenido"""
        from flask import url_for
        if self.content_type == 'blog':
            return url_for('main.blog_post', slug=content.slug)
        elif self.content_type == 'course':
            return url_for('main.course_detail', slug=content.slug)
        elif self.content_type == 'project':
            return url_for('main.project_detail', slug=content.slug)
        return '#'
    
    @staticmethod
    def get_likes_count(content_type, content_id):
        """Obtiene el número de likes para un contenido"""
        return Like.query.filter_by(
            content_type=content_type,
            content_id=content_id
        ).count()
    
    @staticmethod
    def user_has_liked(user_id, content_type, content_id):
        """Verifica si un usuario ha dado like a un contenido"""
        return Like.query.filter_by(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id
        ).first() is not None
    
    @staticmethod
    def toggle_like(user_id, content_type, content_id):
        """Alterna el like de un usuario en un contenido"""
        existing = Like.query.filter_by(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return False  # Like removido
        else:
            new_like = Like(
                user_id=user_id,
                content_type=content_type,
                content_id=content_id
            )
            db.session.add(new_like)
            db.session.commit()
            return True  # Like agregado
    
    def __repr__(self):
        return f'<Like user={self.user_id} {self.content_type}={self.content_id}>'
