"""
Modelo de Lecciones de Cursos - CODEXSOTO
==========================================
Sistema de lecciones estructurado para cursos online
Con tracking de progreso y contenido multimedia
"""

from app.extensions import db
from datetime import datetime
from enum import Enum


class LessonType(Enum):
    """Tipos de contenido de lección"""
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    DOWNLOAD = "download"
    LIVE = "live"


class CourseSection(db.Model):
    """
    Secciones/Módulos de un curso
    Agrupa lecciones relacionadas
    """
    __tablename__ = 'course_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con curso
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    # Contenido
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Orden
    order = db.Column(db.Integer, default=0)
    
    # Estado
    is_published = db.Column(db.Boolean, default=True)
    is_preview = db.Column(db.Boolean, default=False)  # Disponible sin inscripción
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    course = db.relationship('Course', backref=db.backref('sections', order_by='CourseSection.order'))
    lessons = db.relationship('Lesson', back_populates='section', order_by='Lesson.order')
    
    def get_duration(self):
        """Calcula duración total de la sección en minutos"""
        return sum(l.duration or 0 for l in self.lessons if l.is_published)
    
    def get_lessons_count(self):
        """Cuenta lecciones publicadas"""
        return len([l for l in self.lessons if l.is_published])
    
    def to_dict(self, include_lessons=True):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'order': self.order,
            'duration': self.get_duration(),
            'lessons_count': self.get_lessons_count(),
            'is_preview': self.is_preview
        }
        
        if include_lessons:
            data['lessons'] = [l.to_dict() for l in self.lessons if l.is_published]
        
        return data
    
    def __repr__(self):
        return f'<CourseSection {self.title}>'


class Lesson(db.Model):
    """
    Lección individual de un curso
    """
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relaciones
    section_id = db.Column(db.Integer, db.ForeignKey('course_sections.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    # Contenido básico
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)  # Contenido en Markdown/HTML
    
    # Tipo de lección
    lesson_type = db.Column(db.Enum(LessonType), default=LessonType.VIDEO)
    
    # Video
    video_url = db.Column(db.String(500))  # URL de video (YouTube, Vimeo, etc.)
    video_provider = db.Column(db.String(50))  # youtube, vimeo, cloudinary, etc.
    video_id = db.Column(db.String(100))  # ID del video en el proveedor
    
    # Duración y orden
    duration = db.Column(db.Integer)  # Duración en minutos
    order = db.Column(db.Integer, default=0)
    
    # Recursos descargables
    resources = db.Column(db.Text)  # JSON con archivos adjuntos
    
    # Acceso
    is_published = db.Column(db.Boolean, default=False)
    is_preview = db.Column(db.Boolean, default=False)  # Disponible sin pago
    is_premium = db.Column(db.Boolean, default=True)  # Requiere suscripción/compra
    
    # Quiz (si es tipo quiz)
    quiz_data = db.Column(db.Text)  # JSON con preguntas y respuestas
    passing_score = db.Column(db.Integer, default=70)  # Porcentaje para aprobar
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice único para slug dentro del curso
    __table_args__ = (
        db.UniqueConstraint('course_id', 'slug', name='unique_lesson_slug_per_course'),
    )
    
    # Relaciones
    section = db.relationship('CourseSection', back_populates='lessons')
    course = db.relationship('Course', backref=db.backref('lessons', order_by='Lesson.order'))
    
    def get_video_embed_url(self):
        """Genera URL de embed para el video"""
        if not self.video_url:
            return None
        
        if 'youtube.com' in self.video_url or 'youtu.be' in self.video_url:
            # Extraer ID de YouTube
            if 'youtu.be' in self.video_url:
                video_id = self.video_url.split('/')[-1].split('?')[0]
            else:
                import re
                match = re.search(r'v=([^&]+)', self.video_url)
                video_id = match.group(1) if match else None
            
            if video_id:
                return f'https://www.youtube.com/embed/{video_id}'
        
        elif 'vimeo.com' in self.video_url:
            video_id = self.video_url.split('/')[-1]
            return f'https://player.vimeo.com/video/{video_id}'
        
        return self.video_url
    
    def get_type_display(self):
        """Retorna nombre legible del tipo"""
        type_names = {
            LessonType.VIDEO: 'Video',
            LessonType.TEXT: 'Texto',
            LessonType.QUIZ: 'Quiz',
            LessonType.ASSIGNMENT: 'Tarea',
            LessonType.DOWNLOAD: 'Descarga',
            LessonType.LIVE: 'En Vivo'
        }
        return type_names.get(self.lesson_type, 'Lección')
    
    def get_type_icon(self):
        """Retorna icono del tipo de lección"""
        type_icons = {
            LessonType.VIDEO: 'bi-play-circle',
            LessonType.TEXT: 'bi-file-text',
            LessonType.QUIZ: 'bi-question-circle',
            LessonType.ASSIGNMENT: 'bi-pencil-square',
            LessonType.DOWNLOAD: 'bi-download',
            LessonType.LIVE: 'bi-broadcast'
        }
        return type_icons.get(self.lesson_type, 'bi-book')
    
    def can_access(self, user, enrollment=None):
        """Verifica si el usuario puede acceder a la lección"""
        # Lecciones de preview siempre accesibles
        if self.is_preview:
            return True
        
        # Si no está autenticado y no es preview
        if not user or not user.is_authenticated:
            return False
        
        # Admin siempre tiene acceso
        if user.is_admin:
            return True
        
        # Verificar inscripción activa
        if enrollment and enrollment.can_access_course():
            return True
        
        # Verificar suscripción premium
        if hasattr(user, 'subscription') and user.subscription:
            if user.subscription.is_premium():
                return True
        
        return False
    
    def get_resources_list(self):
        """Retorna lista de recursos"""
        import json
        if self.resources:
            return json.loads(self.resources)
        return []
    
    def to_dict(self, include_content=False):
        """Serializa la lección"""
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'lesson_type': self.lesson_type.value,
            'type_display': self.get_type_display(),
            'type_icon': self.get_type_icon(),
            'duration': self.duration,
            'order': self.order,
            'is_preview': self.is_preview,
            'is_premium': self.is_premium,
            'section_id': self.section_id
        }
        
        if include_content:
            data['content'] = self.content
            data['video_url'] = self.video_url
            data['video_embed_url'] = self.get_video_embed_url()
            data['resources'] = self.get_resources_list()
        
        return data
    
    def __repr__(self):
        return f'<Lesson {self.title}>'


class LessonProgress(db.Model):
    """
    Progreso del usuario en una lección
    """
    __tablename__ = 'lesson_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relaciones
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('course_enrollment.id'))
    
    # Progreso
    is_completed = db.Column(db.Boolean, default=False)
    progress_percent = db.Column(db.Float, default=0.0)  # 0-100
    
    # Para videos: posición actual
    video_position = db.Column(db.Integer, default=0)  # Segundos
    video_duration = db.Column(db.Integer)  # Duración total
    
    # Para quizzes
    quiz_score = db.Column(db.Float)  # Puntuación obtenida
    quiz_attempts = db.Column(db.Integer, default=0)
    quiz_passed = db.Column(db.Boolean, default=False)
    quiz_answers = db.Column(db.Text)  # JSON con respuestas
    
    # Notas del estudiante
    notes = db.Column(db.Text)
    
    # Tiempo dedicado (en segundos)
    time_spent = db.Column(db.Integer, default=0)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    last_accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice único
    __table_args__ = (
        db.UniqueConstraint('user_id', 'lesson_id', name='unique_user_lesson_progress'),
    )
    
    # Relaciones
    user = db.relationship('User', backref='lesson_progress')
    lesson = db.relationship('Lesson', backref='user_progress')
    enrollment = db.relationship('CourseEnrollment', backref='lesson_progress')
    
    def complete(self):
        """Marca la lección como completada"""
        self.is_completed = True
        self.progress_percent = 100.0
        self.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Actualizar progreso del curso
        if self.enrollment:
            self._update_course_progress()
    
    def update_video_progress(self, position, duration=None):
        """Actualiza progreso de video"""
        self.video_position = position
        if duration:
            self.video_duration = duration
        
        if self.video_duration and self.video_duration > 0:
            self.progress_percent = min(100, (position / self.video_duration) * 100)
            
            # Marcar como completado si vio más del 90%
            if self.progress_percent >= 90:
                self.complete()
        
        self.last_accessed_at = datetime.utcnow()
        db.session.commit()
    
    def submit_quiz(self, answers, score):
        """Registra intento de quiz"""
        import json
        self.quiz_attempts += 1
        self.quiz_score = score
        self.quiz_answers = json.dumps(answers)
        
        if score >= self.lesson.passing_score:
            self.quiz_passed = True
            self.complete()
        
        db.session.commit()
    
    def add_time_spent(self, seconds):
        """Agrega tiempo dedicado"""
        self.time_spent += seconds
        self.last_accessed_at = datetime.utcnow()
        db.session.commit()
    
    def _update_course_progress(self):
        """Actualiza el progreso general del curso"""
        if not self.enrollment:
            return
        
        # Contar lecciones completadas vs totales
        total_lessons = Lesson.query.filter_by(
            course_id=self.enrollment.course_id,
            is_published=True
        ).count()
        
        if total_lessons == 0:
            return
        
        completed_lessons = LessonProgress.query.filter_by(
            enrollment_id=self.enrollment.id,
            is_completed=True
        ).count()
        
        progress = (completed_lessons / total_lessons) * 100
        self.enrollment.update_progress(progress)
    
    @staticmethod
    def get_or_create(user_id, lesson_id, enrollment_id=None):
        """Obtiene o crea registro de progreso"""
        progress = LessonProgress.query.filter_by(
            user_id=user_id,
            lesson_id=lesson_id
        ).first()
        
        if not progress:
            progress = LessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                enrollment_id=enrollment_id
            )
            db.session.add(progress)
            db.session.commit()
        
        return progress
    
    def to_dict(self):
        return {
            'lesson_id': self.lesson_id,
            'is_completed': self.is_completed,
            'progress_percent': self.progress_percent,
            'video_position': self.video_position,
            'quiz_score': self.quiz_score,
            'quiz_passed': self.quiz_passed,
            'time_spent': self.time_spent,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None
        }
    
    def __repr__(self):
        return f'<LessonProgress User:{self.user_id} Lesson:{self.lesson_id}>'
