from app.extensions import db
from datetime import datetime

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # Referencia al usuario (la relación está definida en User con backref='author')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Acceder al usuario vía self.author (definido en User.comments)
    
    # Comentario polimórfico (puede ser en blog, curso o proyecto)
    content_type = db.Column(db.String(20), nullable=False)  # 'blog', 'course', 'project'
    content_id = db.Column(db.Integer, nullable=False)
    
    # Comentarios anidados (respuestas)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    # Estado del comentario
    is_approved = db.Column(db.Boolean, default=True)
    is_pinned = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_content_object(self):
        """Retorna el objeto al que pertenece el comentario"""
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
    
    def _get_content_url(self, content=None):
        """Genera la URL del contenido asociado al comentario"""
        from flask import url_for
        if content is None:
            content = self.get_content_object()
        if content is None:
            return '#'
        
        if self.content_type == 'blog':
            return url_for('main.blog_post', slug=content.slug)
        elif self.content_type == 'course':
            return url_for('main.course_detail', slug=content.slug)
        elif self.content_type == 'project':
            return url_for('main.project_detail', slug=content.slug)
        return '#'
    
    def get_replies_count(self):
        """Cuenta las respuestas a este comentario"""
        return self.replies.filter_by(is_approved=True).count()
    
    def is_reply(self):
        """Verifica si este comentario es una respuesta"""
        return self.parent_id is not None
    
    def can_edit(self, user):
        """Verifica si el usuario puede editar este comentario"""
        return user.is_authenticated and (user.id == self.user_id or user.is_admin)
    
    def can_delete(self, user):
        """Verifica si el usuario puede eliminar este comentario"""
        return user.is_authenticated and (user.id == self.user_id or user.is_admin)
    
    def to_dict(self):
        """Convierte el comentario a diccionario"""
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author.display_name,
            'author_avatar': self.author.get_avatar_url(50),
            'content_type': self.content_type,
            'content_id': self.content_id,
            'parent_id': self.parent_id,
            'is_reply': self.is_reply(),
            'replies_count': self.get_replies_count(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at != self.created_at else None
        }
    
    def __repr__(self):
        return f'<Comment {self.id} by user_id={self.user_id}>'
