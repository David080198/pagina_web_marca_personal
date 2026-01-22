"""
Modelo de Artículos Técnicos - CODEXSOTO
=========================================
Sistema de artículos técnicos separado del blog
Con categorías, dificultad, tiempo de lectura, etc.
"""

from app.extensions import db
from datetime import datetime
from enum import Enum
import re


class ArticleDifficulty(Enum):
    """Niveles de dificultad de artículos"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ArticleCategory(db.Model):
    """
    Categorías para artículos técnicos
    """
    __tablename__ = 'article_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # Clase de icono (ej: 'bi-code-slash')
    color = db.Column(db.String(7), default='#3b82f6')  # Color hex
    
    # SEO
    meta_title = db.Column(db.String(70))
    meta_description = db.Column(db.String(160))
    
    # Orden y visibilidad
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    articles = db.relationship('Article', back_populates='category', lazy='dynamic')
    
    def article_count(self):
        """Cuenta artículos publicados en esta categoría"""
        return self.articles.filter_by(published=True).count()
    
    def __repr__(self):
        return f'<ArticleCategory {self.name}>'


class Article(db.Model):
    """
    Modelo de Artículo Técnico
    Contenido educativo estructurado y profundo
    """
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Contenido principal
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    subtitle = db.Column(db.String(300))
    summary = db.Column(db.Text)  # Resumen corto
    content = db.Column(db.Text, nullable=False)  # Contenido en Markdown
    
    # Categorización
    category_id = db.Column(db.Integer, db.ForeignKey('article_categories.id'))
    tags = db.Column(db.String(500))  # Tags separados por comas
    difficulty = db.Column(db.Enum(ArticleDifficulty), default=ArticleDifficulty.INTERMEDIATE)
    
    # Multimedia
    featured_image = db.Column(db.String(255))
    thumbnail = db.Column(db.String(255))
    video_url = db.Column(db.String(255))  # Video complementario
    
    # Metadatos de lectura
    reading_time = db.Column(db.Integer)  # Minutos estimados
    word_count = db.Column(db.Integer)
    
    # Acceso
    is_premium = db.Column(db.Boolean, default=False)  # Solo para suscriptores
    is_featured = db.Column(db.Boolean, default=False)  # Destacado en home
    published = db.Column(db.Boolean, default=False)
    
    # Autor
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Estadísticas
    views_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    
    # SEO
    meta_title = db.Column(db.String(70))
    meta_description = db.Column(db.String(160))
    meta_keywords = db.Column(db.String(255))
    canonical_url = db.Column(db.String(255))
    
    # Recursos adicionales
    github_repo = db.Column(db.String(255))  # Repo con código ejemplo
    resources = db.Column(db.Text)  # JSON con recursos adicionales
    
    # Relacionados
    related_articles = db.Column(db.Text)  # JSON con IDs de artículos relacionados
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    # Relaciones
    category = db.relationship('ArticleCategory', back_populates='articles')
    author = db.relationship('User', backref='articles')
    
    def calculate_reading_time(self):
        """Calcula tiempo de lectura basado en palabras (200 wpm)"""
        if self.content:
            # Remover HTML/Markdown
            clean_content = re.sub(r'<[^>]+>', '', self.content)
            clean_content = re.sub(r'[#*_`\[\]()]', '', clean_content)
            words = len(clean_content.split())
            self.word_count = words
            self.reading_time = max(1, words // 200)
        return self.reading_time
    
    def increment_views(self):
        """Incrementa contador de vistas"""
        self.views_count += 1
        db.session.commit()
    
    def publish(self):
        """Publica el artículo"""
        self.published = True
        self.published_at = datetime.utcnow()
        self.calculate_reading_time()
        db.session.commit()
    
    def unpublish(self):
        """Despublica el artículo"""
        self.published = False
        db.session.commit()
    
    def get_tags_list(self):
        """Retorna lista de tags"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def set_tags_from_list(self, tags_list):
        """Establece tags desde una lista"""
        self.tags = ', '.join(tags_list)
    
    def get_difficulty_display(self):
        """Retorna nombre legible de dificultad"""
        difficulty_names = {
            ArticleDifficulty.BEGINNER: 'Principiante',
            ArticleDifficulty.INTERMEDIATE: 'Intermedio',
            ArticleDifficulty.ADVANCED: 'Avanzado',
            ArticleDifficulty.EXPERT: 'Experto'
        }
        return difficulty_names.get(self.difficulty, 'Intermedio')
    
    def get_difficulty_badge_class(self):
        """Retorna clase CSS para badge de dificultad"""
        classes = {
            ArticleDifficulty.BEGINNER: 'success',
            ArticleDifficulty.INTERMEDIATE: 'info',
            ArticleDifficulty.ADVANCED: 'warning',
            ArticleDifficulty.EXPERT: 'danger'
        }
        return classes.get(self.difficulty, 'secondary')
    
    def can_access(self, user):
        """Verifica si un usuario puede acceder al artículo"""
        if not self.is_premium:
            return True
        
        if not user or not user.is_authenticated:
            return False
        
        # Admin siempre tiene acceso
        if user.is_admin:
            return True
        
        # Verificar suscripción premium
        if hasattr(user, 'subscription') and user.subscription:
            return user.subscription.is_premium()
        
        return False
    
    def get_excerpt(self, length=200):
        """Retorna un extracto del contenido"""
        if self.summary:
            return self.summary[:length] + '...' if len(self.summary) > length else self.summary
        
        if self.content:
            clean = re.sub(r'<[^>]+>', '', self.content)
            clean = re.sub(r'[#*_`\[\]()]', '', clean)
            return clean[:length] + '...' if len(clean) > length else clean
        
        return ''
    
    def to_dict(self, include_content=False):
        """Serializa el artículo para APIs"""
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'subtitle': self.subtitle,
            'summary': self.summary,
            'excerpt': self.get_excerpt(),
            'category': self.category.name if self.category else None,
            'category_slug': self.category.slug if self.category else None,
            'tags': self.get_tags_list(),
            'difficulty': self.difficulty.value,
            'difficulty_display': self.get_difficulty_display(),
            'featured_image': self.featured_image,
            'reading_time': self.reading_time,
            'is_premium': self.is_premium,
            'is_featured': self.is_featured,
            'views_count': self.views_count,
            'likes_count': self.likes_count,
            'author': self.author.display_name if self.author else 'CodexSoto',
            'author_avatar': self.author.get_avatar_url() if self.author else None,
            'github_repo': self.github_repo,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat()
        }
        
        if include_content:
            data['content'] = self.content
            data['video_url'] = self.video_url
            data['resources'] = self.resources
        
        return data
    
    @staticmethod
    def get_popular(limit=5):
        """Obtiene artículos más populares"""
        return Article.query.filter_by(published=True)\
            .order_by(Article.views_count.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_featured(limit=3):
        """Obtiene artículos destacados"""
        return Article.query.filter_by(published=True, is_featured=True)\
            .order_by(Article.published_at.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_by_category(category_slug, limit=10):
        """Obtiene artículos por categoría"""
        category = ArticleCategory.query.filter_by(slug=category_slug).first()
        if not category:
            return []
        return Article.query.filter_by(published=True, category_id=category.id)\
            .order_by(Article.published_at.desc())\
            .limit(limit).all()
    
    @staticmethod
    def search(query, limit=20):
        """Búsqueda de artículos"""
        search_term = f'%{query}%'
        return Article.query.filter(
            Article.published == True,
            db.or_(
                Article.title.ilike(search_term),
                Article.summary.ilike(search_term),
                Article.tags.ilike(search_term),
                Article.content.ilike(search_term)
            )
        ).order_by(Article.published_at.desc()).limit(limit).all()
    
    def __repr__(self):
        return f'<Article {self.title}>'


class ArticleLike(db.Model):
    """
    Likes de artículos por usuario
    """
    __tablename__ = 'article_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Índice único
    __table_args__ = (db.UniqueConstraint('article_id', 'user_id', name='unique_article_like'),)
    
    # Relaciones
    article = db.relationship('Article', backref='likes')
    user = db.relationship('User', backref='article_likes')
