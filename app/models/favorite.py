from app.extensions import db
from datetime import datetime

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencia al usuario
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Favorito polimórfico (puede ser blog, curso o proyecto)
    content_type = db.Column(db.String(20), nullable=False)  # 'blog', 'course', 'project'
    content_id = db.Column(db.Integer, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Índice único para evitar duplicados
    __table_args__ = (db.UniqueConstraint('user_id', 'content_type', 'content_id', name='unique_favorite'),)
    
    def get_content_object(self):
        """Retorna el objeto favorito"""
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
        """Genera la URL del contenido asociado al favorito"""
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
    
    @staticmethod
    def is_favorited_by_user(user_id, content_type, content_id):
        """Verifica si un contenido está en favoritos del usuario"""
        return Favorite.query.filter_by(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id
        ).first() is not None
    
    @staticmethod
    def toggle_favorite(user_id, content_type, content_id):
        """Alterna el estado de favorito (agregar/quitar)"""
        favorite = Favorite.query.filter_by(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if favorite:
            # Quitar de favoritos
            db.session.delete(favorite)
            db.session.commit()
            return False
        else:
            # Agregar a favoritos
            new_favorite = Favorite(
                user_id=user_id,
                content_type=content_type,
                content_id=content_id
            )
            db.session.add(new_favorite)
            db.session.commit()
            return True
    
    def to_dict(self):
        """Convierte el favorito a diccionario"""
        content_obj = self.get_content_object()
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'content_title': content_obj.title if content_obj else 'Unknown',
            'content_url': self._get_content_url(content_obj),
            'created_at': self.created_at.isoformat()
        }
    
    def _get_content_url(self, content_obj):
        """Genera la URL del contenido favorito"""
        if not content_obj:
            return '#'
        
        if self.content_type == 'blog':
            return f'/blog/{content_obj.slug}'
        elif self.content_type == 'course':
            return f'/courses/{content_obj.slug}'
        elif self.content_type == 'project':
            return f'/projects/{content_obj.slug}'
        return '#'
    
    def __repr__(self):
        return f'<Favorite {self.content_type}:{self.content_id} by User:{self.user_id}>'
