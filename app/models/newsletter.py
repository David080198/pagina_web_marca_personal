"""
Sistema de Newsletter - CODEXSOTO
==================================
Suscripciones a newsletter, campañas y automatización
"""

from app.extensions import db
from datetime import datetime
import secrets
import hashlib


class NewsletterSubscriber(db.Model):
    """
    Suscriptores a la newsletter
    Puede ser usuario registrado o solo email
    """
    __tablename__ = 'newsletter_subscribers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Email (único identificador)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    # Datos opcionales
    name = db.Column(db.String(100))
    
    # Relación con usuario (opcional)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Estado
    is_active = db.Column(db.Boolean, default=True)
    is_confirmed = db.Column(db.Boolean, default=False)
    
    # Token de confirmación/desuscripción
    confirmation_token = db.Column(db.String(100), unique=True)
    unsubscribe_token = db.Column(db.String(100), unique=True)
    
    # Preferencias
    frequency = db.Column(db.String(20), default='weekly')  # daily, weekly, monthly
    interests = db.Column(db.Text)  # JSON con categorías de interés
    
    # Tipo de suscripción
    subscription_type = db.Column(db.String(20), default='free')  # free, premium
    
    # Fuente de suscripción
    source = db.Column(db.String(50))  # homepage, article, course, popup, etc.
    ip_address = db.Column(db.String(45))
    
    # Estadísticas
    emails_received = db.Column(db.Integer, default=0)
    emails_opened = db.Column(db.Integer, default=0)
    links_clicked = db.Column(db.Integer, default=0)
    last_opened_at = db.Column(db.DateTime)
    last_clicked_at = db.Column(db.DateTime)
    
    # Timestamps
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    unsubscribed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación
    user = db.relationship('User', backref='newsletter_subscription')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.generate_tokens()
    
    def generate_tokens(self):
        """Genera tokens únicos para confirmación y desuscripción"""
        self.confirmation_token = secrets.token_urlsafe(32)
        self.unsubscribe_token = secrets.token_urlsafe(32)
    
    def confirm(self):
        """Confirma la suscripción"""
        self.is_confirmed = True
        self.confirmed_at = datetime.utcnow()
        db.session.commit()
    
    def unsubscribe(self):
        """Cancela la suscripción"""
        self.is_active = False
        self.unsubscribed_at = datetime.utcnow()
        db.session.commit()
    
    def resubscribe(self):
        """Reactiva la suscripción"""
        self.is_active = True
        self.unsubscribed_at = None
        self.generate_tokens()
        db.session.commit()
    
    def record_open(self):
        """Registra apertura de email"""
        self.emails_opened += 1
        self.last_opened_at = datetime.utcnow()
        db.session.commit()
    
    def record_click(self):
        """Registra clic en enlace"""
        self.links_clicked += 1
        self.last_clicked_at = datetime.utcnow()
        db.session.commit()
    
    @property
    def open_rate(self):
        """Calcula tasa de apertura"""
        if self.emails_received == 0:
            return 0
        return round((self.emails_opened / self.emails_received) * 100, 2)
    
    @property
    def click_rate(self):
        """Calcula tasa de clics"""
        if self.emails_opened == 0:
            return 0
        return round((self.links_clicked / self.emails_opened) * 100, 2)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_active': self.is_active,
            'is_confirmed': self.is_confirmed,
            'frequency': self.frequency,
            'subscription_type': self.subscription_type,
            'subscribed_at': self.subscribed_at.isoformat() if self.subscribed_at else None,
            'open_rate': self.open_rate,
            'click_rate': self.click_rate
        }
    
    @staticmethod
    def get_active_subscribers(subscription_type=None):
        """Obtiene suscriptores activos y confirmados"""
        query = NewsletterSubscriber.query.filter_by(is_active=True, is_confirmed=True)
        if subscription_type:
            query = query.filter_by(subscription_type=subscription_type)
        return query.all()
    
    @staticmethod
    def subscribe(email, name=None, source='website', user_id=None):
        """Crea o actualiza una suscripción"""
        subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
        
        if subscriber:
            if not subscriber.is_active:
                subscriber.resubscribe()
            return subscriber, False  # Existente
        
        subscriber = NewsletterSubscriber(
            email=email,
            name=name,
            source=source,
            user_id=user_id
        )
        db.session.add(subscriber)
        db.session.commit()
        return subscriber, True  # Nuevo
    
    def __repr__(self):
        return f'<NewsletterSubscriber {self.email}>'


class NewsletterCampaign(db.Model):
    """
    Campañas de newsletter
    """
    __tablename__ = 'newsletter_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Contenido
    subject = db.Column(db.String(200), nullable=False)
    preview_text = db.Column(db.String(150))
    content_html = db.Column(db.Text, nullable=False)
    content_text = db.Column(db.Text)  # Versión texto plano
    
    # Configuración
    sender_name = db.Column(db.String(100), default='CodexSoto')
    sender_email = db.Column(db.String(120))
    reply_to = db.Column(db.String(120))
    
    # Segmentación
    target_type = db.Column(db.String(20), default='all')  # all, free, premium
    target_interests = db.Column(db.Text)  # JSON con filtros
    
    # Estado
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, sending, sent, cancelled
    
    # Programación
    scheduled_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    
    # Estadísticas
    recipients_count = db.Column(db.Integer, default=0)
    delivered_count = db.Column(db.Integer, default=0)
    opened_count = db.Column(db.Integer, default=0)
    clicked_count = db.Column(db.Integer, default=0)
    bounced_count = db.Column(db.Integer, default=0)
    unsubscribed_count = db.Column(db.Integer, default=0)
    
    # Autor
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación
    creator = db.relationship('User', backref='campaigns')
    
    @property
    def open_rate(self):
        """Tasa de apertura"""
        if self.delivered_count == 0:
            return 0
        return round((self.opened_count / self.delivered_count) * 100, 2)
    
    @property
    def click_rate(self):
        """Tasa de clics"""
        if self.opened_count == 0:
            return 0
        return round((self.clicked_count / self.opened_count) * 100, 2)
    
    def schedule(self, send_at):
        """Programa el envío"""
        self.status = 'scheduled'
        self.scheduled_at = send_at
        db.session.commit()
    
    def cancel(self):
        """Cancela la campaña"""
        if self.status in ['draft', 'scheduled']:
            self.status = 'cancelled'
            db.session.commit()
    
    def mark_sent(self):
        """Marca como enviada"""
        self.status = 'sent'
        self.sent_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'preview_text': self.preview_text,
            'status': self.status,
            'target_type': self.target_type,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'recipients_count': self.recipients_count,
            'open_rate': self.open_rate,
            'click_rate': self.click_rate,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<NewsletterCampaign {self.subject}>'


class NewsletterSend(db.Model):
    """
    Registro de envíos individuales
    """
    __tablename__ = 'newsletter_sends'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias
    campaign_id = db.Column(db.Integer, db.ForeignKey('newsletter_campaigns.id'), nullable=False)
    subscriber_id = db.Column(db.Integer, db.ForeignKey('newsletter_subscribers.id'), nullable=False)
    
    # Estado
    status = db.Column(db.String(20), default='pending')  # pending, sent, bounced, failed
    
    # Tracking
    tracking_id = db.Column(db.String(64), unique=True)  # Para tracking de aperturas
    opened = db.Column(db.Boolean, default=False)
    opened_at = db.Column(db.DateTime)
    opened_count = db.Column(db.Integer, default=0)
    clicked = db.Column(db.Boolean, default=False)
    clicked_at = db.Column(db.DateTime)
    clicked_links = db.Column(db.Text)  # JSON con enlaces clickeados
    
    # Timestamps
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    campaign = db.relationship('NewsletterCampaign', backref='sends')
    subscriber = db.relationship('NewsletterSubscriber', backref='received_campaigns')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tracking_id = hashlib.sha256(
            f"{kwargs.get('campaign_id')}-{kwargs.get('subscriber_id')}-{secrets.token_hex(8)}".encode()
        ).hexdigest()[:64]
    
    def record_open(self):
        """Registra apertura"""
        if not self.opened:
            self.opened = True
            self.opened_at = datetime.utcnow()
            self.campaign.opened_count += 1
        self.opened_count += 1
        db.session.commit()
    
    def record_click(self, link_url):
        """Registra clic en enlace"""
        import json
        if not self.clicked:
            self.clicked = True
            self.clicked_at = datetime.utcnow()
            self.campaign.clicked_count += 1
        
        # Guardar enlace clickeado
        links = json.loads(self.clicked_links or '[]')
        links.append({'url': link_url, 'clicked_at': datetime.utcnow().isoformat()})
        self.clicked_links = json.dumps(links)
        db.session.commit()
