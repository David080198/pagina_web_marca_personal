"""
Blueprint de Suscripciones Premium - CODEXSOTO
===============================================
Gestión de planes de suscripción, pagos y beneficios
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.subscription import Subscription, SubscriptionPayment, SubscriptionPlan, SubscriptionStatus
from datetime import datetime, timedelta

subscriptions_bp = Blueprint('subscriptions', __name__)


@subscriptions_bp.route('/plans')
def plans():
    """Muestra los planes de suscripción disponibles"""
    # Obtener configuración de planes
    plans_data = []
    
    for plan in [SubscriptionPlan.FREE, SubscriptionPlan.MONTHLY, SubscriptionPlan.ANNUAL, SubscriptionPlan.LIFETIME]:
        config = Subscription.PLAN_CONFIG[plan]
        plans_data.append({
            'id': plan.value,
            'name': config['name'],
            'price': config['price'],
            'duration_days': config['duration_days'],
            'features': config['features'],
            'is_popular': plan == SubscriptionPlan.ANNUAL,  # Plan más popular
            'savings': None
        })
    
    # Calcular ahorro del plan anual
    monthly_yearly = Subscription.PLAN_CONFIG[SubscriptionPlan.MONTHLY]['price'] * 12
    annual_price = Subscription.PLAN_CONFIG[SubscriptionPlan.ANNUAL]['price']
    savings_percent = int(((monthly_yearly - annual_price) / monthly_yearly) * 100)
    
    for plan in plans_data:
        if plan['id'] == 'annual':
            plan['savings'] = f'{savings_percent}% de ahorro'
    
    # Suscripción actual del usuario
    current_subscription = None
    if current_user.is_authenticated:
        current_subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    return render_template('subscriptions/plans.html',
                          plans=plans_data,
                          current_subscription=current_subscription)


@subscriptions_bp.route('/subscribe/<plan_id>', methods=['GET', 'POST'])
@login_required
def subscribe(plan_id):
    """Proceso de suscripción a un plan"""
    try:
        plan = SubscriptionPlan(plan_id)
    except ValueError:
        flash('Plan de suscripción no válido', 'error')
        return redirect(url_for('subscriptions.plans'))
    
    if plan == SubscriptionPlan.FREE:
        flash('Ya tienes acceso al plan gratuito', 'info')
        return redirect(url_for('subscriptions.plans'))
    
    # Verificar si ya tiene suscripción activa
    existing = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if existing and existing.is_active() and existing.plan == plan:
        flash('Ya tienes una suscripción activa a este plan', 'info')
        return redirect(url_for('subscriptions.my_subscription'))
    
    plan_config = Subscription.PLAN_CONFIG[plan]
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'bank_transfer')
        
        # Crear o actualizar suscripción
        if not existing:
            subscription = Subscription(
                user_id=current_user.id,
                plan=plan,
                status=SubscriptionStatus.PENDING,
                payment_method=payment_method
            )
            db.session.add(subscription)
        else:
            subscription = existing
            subscription.plan = plan
            subscription.status = SubscriptionStatus.PENDING
            subscription.payment_method = payment_method
        
        db.session.commit()
        
        # Redirigir según método de pago
        if payment_method == 'bank_transfer':
            return redirect(url_for('subscriptions.payment_instructions', subscription_id=subscription.id))
        elif payment_method == 'stripe':
            return redirect(url_for('subscriptions.stripe_checkout', subscription_id=subscription.id))
        elif payment_method == 'paypal':
            return redirect(url_for('subscriptions.paypal_checkout', subscription_id=subscription.id))
        else:
            flash('Método de pago no disponible', 'error')
            return redirect(url_for('subscriptions.plans'))
    
    return render_template('subscriptions/checkout.html',
                          plan=plan,
                          plan_config=plan_config,
                          existing_subscription=existing)


@subscriptions_bp.route('/payment-instructions/<int:subscription_id>')
@login_required
def payment_instructions(subscription_id):
    """Instrucciones de pago por transferencia"""
    subscription = Subscription.query.get_or_404(subscription_id)
    
    if subscription.user_id != current_user.id:
        flash('No tienes permiso para ver esta página', 'error')
        return redirect(url_for('subscriptions.plans'))
    
    plan_config = Subscription.PLAN_CONFIG[subscription.plan]
    
    # Información bancaria (configurar según tu caso)
    bank_info = {
        'bank_name': 'Banco Example',
        'account_holder': 'David Soto / CodexSoto',
        'account_number': 'XXXX-XXXX-XXXX-1234',
        'routing_number': '123456789',
        'swift_code': 'EXAMPLEXXX',
        'reference': f'CXST-SUB-{subscription.id}'
    }
    
    return render_template('subscriptions/payment_instructions.html',
                          subscription=subscription,
                          plan_config=plan_config,
                          bank_info=bank_info)


@subscriptions_bp.route('/submit-payment/<int:subscription_id>', methods=['POST'])
@login_required
def submit_payment(subscription_id):
    """Enviar comprobante de pago"""
    subscription = Subscription.query.get_or_404(subscription_id)
    
    if subscription.user_id != current_user.id:
        flash('No tienes permiso para esta acción', 'error')
        return redirect(url_for('subscriptions.plans'))
    
    # Obtener datos del formulario
    transfer_reference = request.form.get('transfer_reference')
    transfer_amount = request.form.get('transfer_amount', type=float)
    notes = request.form.get('notes')
    
    # Manejar archivo de comprobante
    proof_file = request.files.get('proof_file')
    proof_path = None
    
    if proof_file and proof_file.filename:
        from app.utils.file_upload import save_uploaded_file
        try:
            proof_path = save_uploaded_file(proof_file, 'uploads/subscription_proofs')
        except ValueError as e:
            flash(f'Error con el archivo: {str(e)}', 'error')
            return redirect(url_for('subscriptions.payment_instructions', subscription_id=subscription_id))
    
    # Crear registro de pago
    plan_config = Subscription.PLAN_CONFIG[subscription.plan]
    
    payment = SubscriptionPayment(
        subscription_id=subscription.id,
        amount=transfer_amount or plan_config['price'],
        payment_method='bank_transfer',
        status='pending',
        external_payment_id=transfer_reference,
        description=f'Suscripción {plan_config["name"]} - {notes or ""}'
    )
    
    db.session.add(payment)
    
    # Actualizar estado de suscripción
    subscription.status = SubscriptionStatus.PENDING
    
    db.session.commit()
    
    flash('Comprobante enviado correctamente. Te notificaremos cuando sea verificado.', 'success')
    return redirect(url_for('subscriptions.my_subscription'))


@subscriptions_bp.route('/my-subscription')
@login_required
def my_subscription():
    """Ver mi suscripción actual"""
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    # Historial de pagos
    payments = []
    if subscription:
        payments = subscription.payments.order_by(SubscriptionPayment.created_at.desc()).limit(10).all()
    
    return render_template('subscriptions/my_subscription.html',
                          subscription=subscription,
                          payments=payments)


@subscriptions_bp.route('/cancel', methods=['POST'])
@login_required
def cancel():
    """Cancelar suscripción"""
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription:
        flash('No tienes una suscripción activa', 'error')
        return redirect(url_for('subscriptions.plans'))
    
    if subscription.plan == SubscriptionPlan.FREE:
        flash('No puedes cancelar el plan gratuito', 'info')
        return redirect(url_for('subscriptions.my_subscription'))
    
    # Cancelar pero mantener acceso hasta la fecha de expiración
    subscription.cancel()
    
    if subscription.expires_at:
        flash(f'Tu suscripción ha sido cancelada. Mantendrás acceso hasta {subscription.expires_at.strftime("%d/%m/%Y")}.', 'warning')
    else:
        flash('Tu suscripción ha sido cancelada.', 'warning')
    
    return redirect(url_for('subscriptions.my_subscription'))


@subscriptions_bp.route('/start-trial', methods=['POST'])
@login_required
def start_trial():
    """Iniciar período de prueba"""
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription:
        subscription = Subscription(user_id=current_user.id)
        db.session.add(subscription)
    
    if subscription.has_used_trial:
        flash('Ya has utilizado tu período de prueba gratuito', 'warning')
        return redirect(url_for('subscriptions.plans'))
    
    if subscription.start_trial(days=7):
        flash('¡Bienvenido! Tienes 7 días de acceso premium gratuito.', 'success')
    else:
        flash('No se pudo iniciar el período de prueba', 'error')
    
    return redirect(url_for('subscriptions.my_subscription'))


# ========== Pasarelas de Pago (Placeholders) ==========

@subscriptions_bp.route('/stripe-checkout/<int:subscription_id>')
@login_required
def stripe_checkout(subscription_id):
    """Checkout con Stripe (placeholder)"""
    # TODO: Implementar integración con Stripe
    flash('Pago con tarjeta próximamente disponible. Por favor, usa transferencia bancaria.', 'info')
    return redirect(url_for('subscriptions.payment_instructions', subscription_id=subscription_id))


@subscriptions_bp.route('/paypal-checkout/<int:subscription_id>')
@login_required
def paypal_checkout(subscription_id):
    """Checkout con PayPal (placeholder)"""
    # TODO: Implementar integración con PayPal
    flash('Pago con PayPal próximamente disponible. Por favor, usa transferencia bancaria.', 'info')
    return redirect(url_for('subscriptions.payment_instructions', subscription_id=subscription_id))


# ========== Webhooks (para pasarelas de pago) ==========

@subscriptions_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Webhook de Stripe para eventos de pago"""
    # TODO: Implementar manejo de webhooks de Stripe
    return jsonify({'status': 'ok'})


@subscriptions_bp.route('/webhook/paypal', methods=['POST'])
def paypal_webhook():
    """Webhook de PayPal para eventos de pago"""
    # TODO: Implementar manejo de webhooks de PayPal
    return jsonify({'status': 'ok'})


# ========== API Endpoints ==========

@subscriptions_bp.route('/api/status')
@login_required
def api_status():
    """API: Estado de suscripción del usuario"""
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription:
        return jsonify({
            'has_subscription': False,
            'is_premium': False,
            'plan': 'free'
        })
    
    return jsonify({
        'has_subscription': True,
        'is_premium': subscription.is_premium(),
        'is_active': subscription.is_active(),
        'plan': subscription.plan.value,
        'plan_name': subscription.get_plan_name(),
        'status': subscription.status.value,
        'days_remaining': subscription.days_remaining(),
        'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
        'features': subscription.get_features()
    })


@subscriptions_bp.route('/api/plans')
def api_plans():
    """API: Lista de planes disponibles"""
    plans = []
    
    for plan in SubscriptionPlan:
        config = Subscription.PLAN_CONFIG[plan]
        plans.append({
            'id': plan.value,
            'name': config['name'],
            'price': config['price'],
            'duration_days': config['duration_days'],
            'features': config['features']
        })
    
    return jsonify({'plans': plans})
