"""
Servicio de Suscripciones - CODEXSOTO
======================================
Lógica de negocio para suscripciones premium
"""

from datetime import datetime, timedelta
from app.extensions import db
from app.models.subscription import Subscription, SubscriptionPayment, SubscriptionPlan, SubscriptionStatus
from app.models.user import User
from .email_service import EmailService


class SubscriptionService:
    """Servicio para gestión de suscripciones"""
    
    @staticmethod
    def get_or_create_subscription(user_id):
        """Obtiene o crea una suscripción para el usuario"""
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        
        if not subscription:
            subscription = Subscription(
                user_id=user_id,
                plan=SubscriptionPlan.FREE,
                status=SubscriptionStatus.ACTIVE
            )
            db.session.add(subscription)
            db.session.commit()
        
        return subscription
    
    @staticmethod
    def check_and_update_expired():
        """Verifica y actualiza suscripciones expiradas"""
        now = datetime.utcnow()
        
        # Buscar suscripciones activas que han expirado
        expired = Subscription.query.filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at < now,
            Subscription.plan != SubscriptionPlan.LIFETIME
        ).all()
        
        count = 0
        for sub in expired:
            sub.expire()
            count += 1
            
            # Notificar al usuario
            try:
                EmailService.send_email(
                    to=sub.user.email,
                    subject='Tu suscripción ha expirado',
                    html_content=f'''
                    <h2>Hola {sub.user.first_name or sub.user.username},</h2>
                    <p>Tu suscripción {sub.get_plan_name()} ha expirado.</p>
                    <p>Renueva ahora para mantener acceso a todo el contenido premium.</p>
                    <p><a href="#" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Renovar Suscripción</a></p>
                    '''
                )
            except Exception:
                pass
        
        return count
    
    @staticmethod
    def check_expiring_soon(days=7):
        """Encuentra suscripciones que expiran pronto"""
        now = datetime.utcnow()
        threshold = now + timedelta(days=days)
        
        expiring = Subscription.query.filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at <= threshold,
            Subscription.expires_at > now,
            Subscription.plan != SubscriptionPlan.LIFETIME
        ).all()
        
        return expiring
    
    @staticmethod
    def send_expiring_reminders():
        """Envía recordatorios de suscripciones por expirar"""
        expiring = SubscriptionService.check_expiring_soon(days=7)
        
        for sub in expiring:
            days_left = (sub.expires_at - datetime.utcnow()).days
            
            try:
                EmailService.send_email(
                    to=sub.user.email,
                    subject=f'Tu suscripción expira en {days_left} días',
                    html_content=f'''
                    <h2>Hola {sub.user.first_name or sub.user.username},</h2>
                    <p>Tu suscripción {sub.get_plan_name()} expira en <strong>{days_left} días</strong>.</p>
                    <p>Renueva ahora para no perder acceso a:</p>
                    <ul>
                        {''.join(f'<li>{f}</li>' for f in sub.get_features())}
                    </ul>
                    <p><a href="#" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Renovar Ahora</a></p>
                    '''
                )
            except Exception:
                pass
        
        return len(expiring)
    
    @staticmethod
    def process_payment(subscription, amount, payment_method, reference=None):
        """Procesa un pago de suscripción"""
        payment = SubscriptionPayment(
            subscription_id=subscription.id,
            amount=amount,
            payment_method=payment_method,
            status='completed',
            external_payment_id=reference,
            description=f'Pago {subscription.get_plan_name()}'
        )
        
        db.session.add(payment)
        
        # Activar o renovar suscripción
        if subscription.is_active():
            subscription.renew()
        else:
            subscription.activate(subscription.plan, amount)
        
        # Actualizar rol del usuario
        if subscription.is_premium():
            subscription.user.role = 'premium'
            db.session.commit()
        
        # Enviar confirmación
        EmailService.send_subscription_confirmation(subscription)
        
        return payment
    
    @staticmethod
    def upgrade_subscription(user_id, new_plan):
        """Actualiza la suscripción a un plan superior"""
        subscription = SubscriptionService.get_or_create_subscription(user_id)
        
        if subscription.upgrade(new_plan):
            # Actualizar rol
            if subscription.is_premium():
                subscription.user.role = 'premium'
            
            db.session.commit()
            EmailService.send_subscription_confirmation(subscription)
            return True
        
        return False
    
    @staticmethod
    def cancel_subscription(user_id):
        """Cancela la suscripción de un usuario"""
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        
        if not subscription:
            return False
        
        subscription.cancel()
        
        # No degradar rol inmediatamente si aún tiene tiempo
        if not subscription.is_active():
            subscription.user.role = 'user'
            db.session.commit()
        
        return True
    
    @staticmethod
    def get_statistics():
        """Obtiene estadísticas de suscripciones"""
        total = Subscription.query.count()
        
        active = Subscription.query.filter_by(status=SubscriptionStatus.ACTIVE).count()
        
        premium = Subscription.query.filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.plan != SubscriptionPlan.FREE
        ).count()
        
        by_plan = {}
        for plan in SubscriptionPlan:
            by_plan[plan.value] = Subscription.query.filter_by(plan=plan).count()
        
        # Ingresos del mes actual
        from sqlalchemy import func
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_revenue = db.session.query(
            func.sum(SubscriptionPayment.amount)
        ).filter(
            SubscriptionPayment.paid_at >= month_start,
            SubscriptionPayment.status == 'completed'
        ).scalar() or 0
        
        return {
            'total_subscriptions': total,
            'active_subscriptions': active,
            'premium_subscriptions': premium,
            'by_plan': by_plan,
            'monthly_revenue': float(monthly_revenue),
            'conversion_rate': round((premium / total * 100) if total > 0 else 0, 2)
        }
    
    @staticmethod
    def has_access_to_premium_content(user):
        """Verifica si el usuario tiene acceso a contenido premium"""
        if not user or not user.is_authenticated:
            return False
        
        if user.is_admin:
            return True
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if not subscription:
            return False
        
        return subscription.is_premium() or subscription.is_trial_active()
