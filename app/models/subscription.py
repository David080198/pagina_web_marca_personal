"""
Modelo de Suscripciones Premium - CODEXSOTO
============================================
Sistema de suscripciones con planes mensual/anual
Beneficios: Acceso a cursos premium, artículos exclusivos, etc.
"""

from app.extensions import db
from datetime import datetime, timedelta
from enum import Enum
import secrets


class SubscriptionPlan(Enum):
    """Planes de suscripción disponibles"""
    FREE = "free"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    LIFETIME = "lifetime"


class SubscriptionStatus(Enum):
    """Estados posibles de una suscripción"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"
    TRIAL = "trial"


class Subscription(db.Model):
    """
    Modelo de Suscripción Premium
    Maneja planes de suscripción con períodos de facturación
    """
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con usuario
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Plan y estado
    plan = db.Column(db.Enum(SubscriptionPlan), default=SubscriptionPlan.FREE)
    status = db.Column(db.Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING)
    
    # Precios (en USD)
    price_paid = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    
    # Períodos
    started_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Trial
    trial_ends_at = db.Column(db.DateTime)
    has_used_trial = db.Column(db.Boolean, default=False)
    
    # Renovación automática
    auto_renew = db.Column(db.Boolean, default=True)
    
    # Información de pago
    payment_method = db.Column(db.String(50))  # stripe, paypal, bank_transfer
    external_subscription_id = db.Column(db.String(255))  # ID de Stripe/PayPal
    
    # Historial
    renewal_count = db.Column(db.Integer, default=0)
    last_payment_at = db.Column(db.DateTime)
    next_billing_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', backref=db.backref('subscription', uselist=False))
    payments = db.relationship('SubscriptionPayment', back_populates='subscription', lazy='dynamic')
    
    # Configuración de planes (precios y duración)
    PLAN_CONFIG = {
        SubscriptionPlan.FREE: {
            'price': 0,
            'duration_days': None,
            'name': 'Gratuito',
            'features': ['Acceso a cursos gratuitos', 'Blog público', 'Newsletter básica']
        },
        SubscriptionPlan.MONTHLY: {
            'price': 9.99,
            'duration_days': 30,
            'name': 'Mensual',
            'features': [
                'Todos los beneficios Free',
                'Acceso a cursos premium',
                'Artículos técnicos exclusivos',
                'Descuentos en cursos',
                'Soporte prioritario'
            ]
        },
        SubscriptionPlan.ANNUAL: {
            'price': 89.99,
            'duration_days': 365,
            'name': 'Anual',
            'features': [
                'Todos los beneficios Mensual',
                '2 meses gratis',
                'Acceso anticipado a nuevos cursos',
                'Certificados verificados',
                'Mentorías grupales'
            ]
        },
        SubscriptionPlan.LIFETIME: {
            'price': 299.99,
            'duration_days': None,
            'name': 'Vitalicio',
            'features': [
                'Acceso de por vida',
                'Todos los cursos presentes y futuros',
                'Mentorías 1:1 mensuales',
                'Comunidad VIP',
                'Proyectos reales con feedback'
            ]
        }
    }
    
    def is_active(self):
        """Verifica si la suscripción está activa"""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        
        if self.plan == SubscriptionPlan.LIFETIME:
            return True
            
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
            
        return True
    
    def is_premium(self):
        """Verifica si es una suscripción premium (no free)"""
        return self.plan != SubscriptionPlan.FREE and self.is_active()
    
    def is_trial_active(self):
        """Verifica si está en período de prueba"""
        if self.status != SubscriptionStatus.TRIAL:
            return False
        return self.trial_ends_at and self.trial_ends_at > datetime.utcnow()
    
    def days_remaining(self):
        """Calcula los días restantes de suscripción"""
        if not self.expires_at:
            return None if self.plan == SubscriptionPlan.LIFETIME else 0
        
        remaining = (self.expires_at - datetime.utcnow()).days
        return max(0, remaining)
    
    def activate(self, plan, price=None):
        """Activa una suscripción con el plan especificado"""
        self.plan = plan
        self.status = SubscriptionStatus.ACTIVE
        self.started_at = datetime.utcnow()
        self.price_paid = price or self.PLAN_CONFIG[plan]['price']
        
        duration = self.PLAN_CONFIG[plan]['duration_days']
        if duration:
            self.expires_at = datetime.utcnow() + timedelta(days=duration)
            self.next_billing_at = self.expires_at
        else:
            self.expires_at = None
            self.next_billing_at = None
        
        self.last_payment_at = datetime.utcnow()
        db.session.commit()
    
    def start_trial(self, days=7):
        """Inicia un período de prueba"""
        if self.has_used_trial:
            return False
        
        self.status = SubscriptionStatus.TRIAL
        self.plan = SubscriptionPlan.MONTHLY
        self.trial_ends_at = datetime.utcnow() + timedelta(days=days)
        self.expires_at = self.trial_ends_at
        self.has_used_trial = True
        db.session.commit()
        return True
    
    def cancel(self):
        """Cancela la suscripción (mantiene acceso hasta expiración)"""
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.auto_renew = False
        db.session.commit()
    
    def renew(self):
        """Renueva la suscripción por otro período"""
        if self.plan == SubscriptionPlan.FREE or self.plan == SubscriptionPlan.LIFETIME:
            return False
        
        duration = self.PLAN_CONFIG[self.plan]['duration_days']
        self.expires_at = datetime.utcnow() + timedelta(days=duration)
        self.status = SubscriptionStatus.ACTIVE
        self.renewal_count += 1
        self.last_payment_at = datetime.utcnow()
        self.next_billing_at = self.expires_at
        db.session.commit()
        return True
    
    def expire(self):
        """Expira la suscripción"""
        self.status = SubscriptionStatus.EXPIRED
        db.session.commit()
    
    def upgrade(self, new_plan):
        """Actualiza a un plan superior"""
        if new_plan.value <= self.plan.value:
            return False
        
        # Calcular crédito por días no usados
        if self.days_remaining() and self.plan != SubscriptionPlan.FREE:
            daily_rate = self.PLAN_CONFIG[self.plan]['price'] / self.PLAN_CONFIG[self.plan]['duration_days']
            credit = daily_rate * self.days_remaining()
        else:
            credit = 0
        
        new_price = self.PLAN_CONFIG[new_plan]['price'] - credit
        self.activate(new_plan, max(0, new_price))
        return True
    
    def get_features(self):
        """Obtiene las características del plan actual"""
        return self.PLAN_CONFIG[self.plan]['features']
    
    def get_plan_name(self):
        """Obtiene el nombre legible del plan"""
        return self.PLAN_CONFIG[self.plan]['name']
    
    def get_status_display(self):
        """Retorna el estado en formato legible"""
        status_names = {
            SubscriptionStatus.ACTIVE: 'Activa',
            SubscriptionStatus.CANCELLED: 'Cancelada',
            SubscriptionStatus.EXPIRED: 'Expirada',
            SubscriptionStatus.PENDING: 'Pendiente',
            SubscriptionStatus.TRIAL: 'Período de Prueba'
        }
        return status_names.get(self.status, 'Desconocido')
    
    def get_status_badge_class(self):
        """Retorna la clase CSS para badges"""
        status_classes = {
            SubscriptionStatus.ACTIVE: 'success',
            SubscriptionStatus.CANCELLED: 'warning',
            SubscriptionStatus.EXPIRED: 'danger',
            SubscriptionStatus.PENDING: 'secondary',
            SubscriptionStatus.TRIAL: 'info'
        }
        return status_classes.get(self.status, 'secondary')
    
    def to_dict(self):
        """Serializa la suscripción para APIs"""
        return {
            'id': self.id,
            'plan': self.plan.value,
            'plan_name': self.get_plan_name(),
            'status': self.status.value,
            'status_display': self.get_status_display(),
            'is_active': self.is_active(),
            'is_premium': self.is_premium(),
            'days_remaining': self.days_remaining(),
            'features': self.get_features(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'auto_renew': self.auto_renew,
            'price': self.PLAN_CONFIG[self.plan]['price']
        }
    
    def __repr__(self):
        return f'<Subscription {self.user.username} - {self.plan.value}>'


class SubscriptionPayment(db.Model):
    """
    Historial de pagos de suscripciones
    """
    __tablename__ = 'subscription_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    
    # Información del pago
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    payment_method = db.Column(db.String(50))
    
    # Estado
    status = db.Column(db.String(20), default='completed')  # completed, failed, refunded
    
    # Referencias externas
    external_payment_id = db.Column(db.String(255))
    invoice_number = db.Column(db.String(100))
    
    # Descripción
    description = db.Column(db.String(255))
    
    # Timestamps
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    subscription = db.relationship('Subscription', back_populates='payments')
    
    def __repr__(self):
        return f'<SubscriptionPayment {self.id} - ${self.amount}>'
