from app.extensions import db
from datetime import datetime
from enum import Enum

class EnrollmentStatus(Enum):
    PENDING_PAYMENT = "pending_payment"
    PAYMENT_PENDING_APPROVAL = "payment_pending_approval"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class PaymentMethod(Enum):
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    CREDIT_CARD = "credit_card"
    FREE = "free"

class PaymentStatus(Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class CourseEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Relaciones
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    # Estado de la inscripción
    status = db.Column(db.Enum(EnrollmentStatus), default=EnrollmentStatus.PENDING_PAYMENT)
    
    # Información del curso al momento de inscripción
    enrolled_price = db.Column(db.Float, nullable=False, default=0.0)  # Precio al momento de inscripción
    
    # Información adicional del estudiante
    phone = db.Column(db.String(20))  # Teléfono de contacto
    student_notes = db.Column(db.Text)  # Comentarios del estudiante
    
    # Progreso del curso
    progress_percentage = db.Column(db.Float, default=0.0)
    completed_lessons = db.Column(db.Text)  # JSON con lecciones completadas
    
    # Fechas
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    activated_at = db.Column(db.DateTime)  # Cuando se aprobó el pago
    completed_at = db.Column(db.DateTime)  # Cuando completó el curso
    expires_at = db.Column(db.DateTime)  # Fecha de expiración si aplica
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')
    payments = db.relationship('Payment', back_populates='enrollment')
    course = db.relationship('Course', backref='enrollments')
    payment = db.relationship('Payment', backref='enrollment', uselist=False)
    
    # Índice único para evitar inscripciones duplicadas
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='unique_user_course_enrollment'),)
    
    def is_active(self):
        """Verifica si la inscripción está activa"""
        return self.status == EnrollmentStatus.ACTIVE
    
    def is_completed(self):
        """Verifica si el usuario completó el curso"""
        return self.status == EnrollmentStatus.COMPLETED
    
    @property
    def payment(self):
        """Obtiene el pago más reciente de esta inscripción"""
        if self.payments:
            return self.payments[-1]  # El más reciente
        return None
    
    def can_access_course(self):
        """Verifica si el usuario puede acceder al contenido del curso"""
        return self.status in [EnrollmentStatus.ACTIVE, EnrollmentStatus.COMPLETED]
    
    def update_progress(self, percentage):
        """Actualiza el progreso del curso"""
        self.progress_percentage = min(100.0, max(0.0, percentage))
        if self.progress_percentage >= 100.0 and self.status == EnrollmentStatus.ACTIVE:
            self.status = EnrollmentStatus.COMPLETED
            self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def activate(self):
        """Activa la inscripción después del pago aprobado"""
        self.status = EnrollmentStatus.ACTIVE
        self.activated_at = datetime.utcnow()
        db.session.commit()
    
    def cancel(self):
        """Cancela la inscripción"""
        self.status = EnrollmentStatus.CANCELLED
        db.session.commit()
    
    def get_status_display(self):
        """Retorna el nombre legible del estado de inscripción"""
        status_names = {
            EnrollmentStatus.PENDING_PAYMENT: 'Pendiente de Pago',
            EnrollmentStatus.PAYMENT_PENDING_APPROVAL: 'Validando Pago',
            EnrollmentStatus.ACTIVE: 'Activo',
            EnrollmentStatus.COMPLETED: 'Completado',
            EnrollmentStatus.CANCELLED: 'Cancelado',
            EnrollmentStatus.EXPIRED: 'Expirado'
        }
        return status_names.get(self.status, 'Desconocido')
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge de estado"""
        status_classes = {
            EnrollmentStatus.PENDING_PAYMENT: 'warning',
            EnrollmentStatus.PAYMENT_PENDING_APPROVAL: 'info',
            EnrollmentStatus.ACTIVE: 'success',
            EnrollmentStatus.COMPLETED: 'primary',
            EnrollmentStatus.CANCELLED: 'danger',
            EnrollmentStatus.EXPIRED: 'secondary'
        }
        return status_classes.get(self.status, 'secondary')
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_title': self.course.title,
            'course_slug': self.course.slug,
            'status': self.status.value,
            'progress_percentage': self.progress_percentage,
            'enrolled_price': self.enrolled_price,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self):
        return f'<CourseEnrollment {self.user.username} -> {self.course.title}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Información del pago
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    
    # Estado del pago
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING_APPROVAL)
    
    # Información del comprobante
    proof_of_payment_path = db.Column(db.String(255))  # Ruta del comprobante subido
    
    # Información bancaria (para transferencias)
    bank_account_used = db.Column(db.String(100))  # Cuenta bancaria utilizada
    transaction_reference = db.Column(db.String(100))  # Referencia/ID de transacción
    
    # Campos adicionales para transferencias bancarias
    transfer_sender_name = db.Column(db.String(100))  # Nombre de quien hizo la transferencia
    transfer_reference = db.Column(db.String(100))  # Referencia de la transferencia
    transfer_amount = db.Column(db.Float)  # Monto transferido
    payment_receipt_path = db.Column(db.String(255))  # Ruta del comprobante
    additional_notes = db.Column(db.Text)  # Notas adicionales del usuario
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notas administrativas
    admin_notes = db.Column(db.Text)  # Notas del administrador
    rejection_reason = db.Column(db.Text)  # Razón de rechazo si aplica
    
    # Relación con inscripción
    enrollment_id = db.Column(db.Integer, db.ForeignKey('course_enrollment.id'), nullable=False)
    
    # Notas del usuario
    payment_notes = db.Column(db.Text)  # Notas adicionales del usuario
    
    # Fechas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)  # Cuando fue enviado el comprobante
    processed_at = db.Column(db.DateTime)  # Cuando fue procesado por admin
    processed_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin que procesó
    
    # Relaciones
    enrollment = db.relationship('CourseEnrollment', back_populates='payments')
    processor = db.relationship('User', foreign_keys=[processed_by])
    
    def approve(self, admin_user_id, notes=None):
        """Aprobar el pago"""
        self.status = PaymentStatus.APPROVED
        self.processed_at = datetime.utcnow()
        self.processed_by = admin_user_id
        if notes:
            self.admin_notes = notes
        
        # Activar la inscripción asociada
        if self.enrollment:
            self.enrollment.activate()
    
    def reject(self, admin_user_id, reason, notes=None):
        """Rechazar el pago"""
        self.status = PaymentStatus.REJECTED
        self.processed_at = datetime.utcnow()
        self.processed_by = admin_user_id
        self.rejection_reason = reason
        if notes:
            self.admin_notes = notes
        
        # Cancelar la inscripción asociada
        if self.enrollment:
            self.enrollment.cancel()
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge de estado"""
        status_classes = {
            PaymentStatus.PENDING_APPROVAL: 'warning',
            PaymentStatus.APPROVED: 'success',
            PaymentStatus.REJECTED: 'danger',
            PaymentStatus.CANCELLED: 'secondary'
        }
        return status_classes.get(self.status, 'secondary')
    
    def get_method_display(self):
        """Retorna el nombre legible del método de pago"""
        method_names = {
            PaymentMethod.BANK_TRANSFER: 'Transferencia Bancaria',
            PaymentMethod.PAYPAL: 'PayPal',
            PaymentMethod.CREDIT_CARD: 'Tarjeta de Crédito',
            PaymentMethod.FREE: 'Gratuito'
        }
        return method_names.get(self.payment_method, 'Desconocido')
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'method': self.payment_method.value,
            'method_display': self.get_method_display(),
            'status': self.status,
            'status_badge_class': self.get_status_badge_class(),
            'transaction_reference': self.transaction_reference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    def __repr__(self):
        return f'<Payment ${self.amount} {self.payment_method.value} - {self.status}>'
