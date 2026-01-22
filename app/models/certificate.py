"""
Modelo de Certificados - CODEXSOTO
===================================
Sistema de certificados de finalización de cursos
Con verificación pública y generación PDF
"""

from app.extensions import db
from datetime import datetime
import secrets
import hashlib


class Certificate(db.Model):
    """
    Certificado de finalización de curso
    """
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Código único de verificación
    certificate_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Relaciones
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('course_enrollment.id'))
    
    # Información del certificado
    recipient_name = db.Column(db.String(200), nullable=False)  # Nombre en el certificado
    course_title = db.Column(db.String(200), nullable=False)  # Título del curso al momento
    
    # Información adicional
    instructor_name = db.Column(db.String(200), default='David Soto')
    course_duration = db.Column(db.Integer)  # Horas del curso
    completion_score = db.Column(db.Float)  # Puntuación final si aplica
    
    # Estado
    is_valid = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=True)  # Visible en perfil público
    
    # Archivo PDF
    pdf_path = db.Column(db.String(255))  # Ruta al PDF generado
    
    # Timestamps
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Opcional: fecha de expiración
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Datos adicionales
    extra_data = db.Column(db.Text)  # JSON con datos adicionales
    
    # Relaciones
    user = db.relationship('User', backref='certificates')
    course = db.relationship('Course', backref='certificates')
    enrollment = db.relationship('CourseEnrollment', backref='certificate')
    
    # Índice único para evitar duplicados
    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='unique_user_course_certificate'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.certificate_code:
            self.certificate_code = self._generate_code()
    
    def _generate_code(self):
        """Genera código único de verificación"""
        # Formato: CXST-XXXX-XXXX-XXXX
        random_part = secrets.token_hex(6).upper()
        return f"CXST-{random_part[:4]}-{random_part[4:8]}-{random_part[8:12]}"
    
    def get_verification_url(self):
        """Retorna URL de verificación pública"""
        return f"/certificate/verify/{self.certificate_code}"
    
    def get_public_url(self):
        """Retorna URL pública del certificado"""
        return f"/certificate/{self.certificate_code}"
    
    def invalidate(self, reason=None):
        """Invalida el certificado"""
        self.is_valid = False
        if reason:
            import json
            meta = json.loads(self.metadata or '{}')
            meta['invalidation_reason'] = reason
            meta['invalidated_at'] = datetime.utcnow().isoformat()
            self.metadata = json.dumps(meta)
        db.session.commit()
    
    def get_share_data(self):
        """Datos para compartir en redes sociales"""
        return {
            'title': f'Certificado: {self.course_title}',
            'description': f'{self.recipient_name} ha completado el curso "{self.course_title}" en CodexSoto',
            'url': self.get_public_url(),
            'image': '/static/images/certificate-preview.png'
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'certificate_code': self.certificate_code,
            'recipient_name': self.recipient_name,
            'course_title': self.course_title,
            'instructor_name': self.instructor_name,
            'course_duration': self.course_duration,
            'completion_score': self.completion_score,
            'is_valid': self.is_valid,
            'verification_url': self.get_verification_url(),
            'public_url': self.get_public_url(),
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @staticmethod
    def verify(code):
        """Verifica un certificado por su código"""
        certificate = Certificate.query.filter_by(certificate_code=code).first()
        
        if not certificate:
            return None, 'Certificado no encontrado'
        
        if not certificate.is_valid:
            return certificate, 'Este certificado ha sido invalidado'
        
        if certificate.expires_at and certificate.expires_at < datetime.utcnow():
            return certificate, 'Este certificado ha expirado'
        
        return certificate, 'Certificado válido'
    
    @staticmethod
    def issue_for_enrollment(enrollment):
        """Emite certificado para una inscripción completada"""
        # Verificar que no exista ya
        existing = Certificate.query.filter_by(
            user_id=enrollment.user_id,
            course_id=enrollment.course_id
        ).first()
        
        if existing:
            return existing
        
        certificate = Certificate(
            user_id=enrollment.user_id,
            course_id=enrollment.course_id,
            enrollment_id=enrollment.id,
            recipient_name=enrollment.user.full_name,
            course_title=enrollment.course.title,
            course_duration=enrollment.course.duration,
            completion_score=enrollment.progress_percentage
        )
        
        db.session.add(certificate)
        db.session.commit()
        
        return certificate
    
    def __repr__(self):
        return f'<Certificate {self.certificate_code}>'


class CertificateTemplate(db.Model):
    """
    Plantillas de certificados personalizables
    """
    __tablename__ = 'certificate_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Diseño
    background_image = db.Column(db.String(255))
    logo_position = db.Column(db.String(20), default='top')  # top, bottom, left, right
    
    # Colores
    primary_color = db.Column(db.String(7), default='#3b82f6')
    secondary_color = db.Column(db.String(7), default='#1e40af')
    text_color = db.Column(db.String(7), default='#1f2937')
    
    # Texto personalizable
    header_text = db.Column(db.String(200), default='CERTIFICADO DE FINALIZACIÓN')
    body_template = db.Column(db.Text)  # Template con placeholders
    footer_text = db.Column(db.Text)
    
    # Estado
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CertificateTemplate {self.name}>'
