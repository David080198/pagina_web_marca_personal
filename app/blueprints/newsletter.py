"""
Blueprint de Newsletter - CODEXSOTO
====================================
Sistema de suscripción a newsletter y gestión de campañas
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db, mail
from app.models.newsletter import NewsletterSubscriber, NewsletterCampaign
from flask_mail import Message
import re

newsletter_bp = Blueprint('newsletter', __name__)


def is_valid_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@newsletter_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """Suscribirse a la newsletter"""
    email = request.form.get('email', '').strip().lower()
    name = request.form.get('name', '').strip()
    source = request.form.get('source', 'website')
    
    # Validar email
    if not email or not is_valid_email(email):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Email no válido'}), 400
        flash('Por favor ingresa un email válido', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    # Obtener IP del usuario
    ip_address = request.remote_addr
    
    # Verificar si el usuario está logueado
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Crear suscripción
    subscriber, is_new = NewsletterSubscriber.subscribe(
        email=email,
        name=name,
        source=source,
        user_id=user_id
    )
    
    if subscriber:
        subscriber.ip_address = ip_address
        db.session.commit()
    
    # Enviar email de confirmación
    if is_new and subscriber:
        try:
            send_confirmation_email(subscriber)
        except Exception as e:
            current_app.logger.error(f'Error enviando email de confirmación: {e}')
    
    # Respuesta
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if is_new:
            return jsonify({
                'success': True,
                'message': '¡Gracias por suscribirte! Revisa tu email para confirmar.',
                'is_new': True
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Ya estás suscrito a nuestra newsletter.',
                'is_new': False
            })
    
    if is_new:
        flash('¡Gracias por suscribirte! Revisa tu email para confirmar.', 'success')
    else:
        flash('Ya estás suscrito a nuestra newsletter.', 'info')
    
    return redirect(request.referrer or url_for('main.index'))


@newsletter_bp.route('/confirm/<token>')
def confirm(token):
    """Confirmar suscripción a newsletter"""
    subscriber = NewsletterSubscriber.query.filter_by(confirmation_token=token).first()
    
    if not subscriber:
        flash('Token de confirmación no válido o expirado.', 'error')
        return redirect(url_for('main.index'))
    
    if subscriber.is_confirmed:
        flash('Tu suscripción ya está confirmada.', 'info')
        return redirect(url_for('main.index'))
    
    subscriber.confirm()
    
    flash('¡Tu suscripción ha sido confirmada! Recibirás nuestras últimas novedades.', 'success')
    return redirect(url_for('main.index'))


@newsletter_bp.route('/unsubscribe/<token>')
def unsubscribe(token):
    """Cancelar suscripción a newsletter"""
    subscriber = NewsletterSubscriber.query.filter_by(unsubscribe_token=token).first()
    
    if not subscriber:
        flash('Token de desuscripción no válido.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('newsletter/unsubscribe.html', subscriber=subscriber)


@newsletter_bp.route('/unsubscribe/<token>/confirm', methods=['POST'])
def confirm_unsubscribe(token):
    """Confirmar cancelación de suscripción"""
    subscriber = NewsletterSubscriber.query.filter_by(unsubscribe_token=token).first()
    
    if not subscriber:
        flash('Token de desuscripción no válido.', 'error')
        return redirect(url_for('main.index'))
    
    reason = request.form.get('reason', '')
    
    # Guardar razón si se proporcionó
    if reason:
        import json
        interests = json.loads(subscriber.interests or '{}')
        interests['unsubscribe_reason'] = reason
        subscriber.interests = json.dumps(interests)
    
    subscriber.unsubscribe()
    
    flash('Has sido dado de baja de nuestra newsletter. ¡Te extrañaremos!', 'info')
    return redirect(url_for('main.index'))


@newsletter_bp.route('/preferences/<token>')
def preferences(token):
    """Actualizar preferencias de newsletter"""
    subscriber = NewsletterSubscriber.query.filter_by(unsubscribe_token=token).first()
    
    if not subscriber:
        flash('Token no válido.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('newsletter/preferences.html', subscriber=subscriber)


@newsletter_bp.route('/preferences/<token>/update', methods=['POST'])
def update_preferences(token):
    """Guardar preferencias actualizadas"""
    subscriber = NewsletterSubscriber.query.filter_by(unsubscribe_token=token).first()
    
    if not subscriber:
        flash('Token no válido.', 'error')
        return redirect(url_for('main.index'))
    
    # Actualizar preferencias
    subscriber.frequency = request.form.get('frequency', 'weekly')
    
    # Intereses
    import json
    interests = request.form.getlist('interests')
    subscriber.interests = json.dumps({'categories': interests})
    
    db.session.commit()
    
    flash('Tus preferencias han sido actualizadas.', 'success')
    return redirect(url_for('newsletter.preferences', token=token))


@newsletter_bp.route('/track/open/<tracking_id>')
def track_open(tracking_id):
    """Tracking pixel para aperturas de email"""
    from app.models.newsletter import NewsletterSend
    
    send = NewsletterSend.query.filter_by(tracking_id=tracking_id).first()
    
    if send:
        send.record_open()
        send.subscriber.record_open()
    
    # Retornar imagen 1x1 transparente
    from flask import Response
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x44\x00\x3b'
    return Response(pixel, mimetype='image/gif')


@newsletter_bp.route('/track/click/<tracking_id>')
def track_click(tracking_id):
    """Tracking de clics en enlaces"""
    from app.models.newsletter import NewsletterSend
    
    url = request.args.get('url')
    
    if not url:
        return redirect(url_for('main.index'))
    
    send = NewsletterSend.query.filter_by(tracking_id=tracking_id).first()
    
    if send:
        send.record_click(url)
        send.subscriber.record_click()
    
    return redirect(url)


# ========== Funciones auxiliares ==========

def send_confirmation_email(subscriber):
    """Envía email de confirmación de suscripción"""
    confirm_url = url_for('newsletter.confirm', token=subscriber.confirmation_token, _external=True)
    
    msg = Message(
        subject='Confirma tu suscripción a CodexSoto',
        recipients=[subscriber.email],
        html=f'''
        <h2>¡Bienvenido a la newsletter de CodexSoto!</h2>
        <p>Gracias por suscribirte. Por favor confirma tu email haciendo clic en el siguiente enlace:</p>
        <p><a href="{confirm_url}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Confirmar Suscripción</a></p>
        <p>Si no solicitaste esta suscripción, puedes ignorar este email.</p>
        <p>Saludos,<br>David Soto - CodexSoto</p>
        ''',
        body=f'''
        ¡Bienvenido a la newsletter de CodexSoto!
        
        Gracias por suscribirte. Por favor confirma tu email visitando el siguiente enlace:
        {confirm_url}
        
        Si no solicitaste esta suscripción, puedes ignorar este email.
        
        Saludos,
        David Soto - CodexSoto
        '''
    )
    
    mail.send(msg)


# ========== API Endpoints ==========

@newsletter_bp.route('/api/subscribe', methods=['POST'])
def api_subscribe():
    """API: Suscribirse a newsletter"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Datos no proporcionados'}), 400
    
    email = data.get('email', '').strip().lower()
    name = data.get('name', '').strip()
    source = data.get('source', 'api')
    
    if not email or not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Email no válido'}), 400
    
    subscriber, is_new = NewsletterSubscriber.subscribe(
        email=email,
        name=name,
        source=source
    )
    
    if is_new and subscriber:
        try:
            send_confirmation_email(subscriber)
        except Exception as e:
            current_app.logger.error(f'Error enviando email: {e}')
    
    return jsonify({
        'success': True,
        'is_new': is_new,
        'message': '¡Gracias por suscribirte!' if is_new else 'Ya estás suscrito.',
        'requires_confirmation': is_new
    })


@newsletter_bp.route('/api/check', methods=['POST'])
def api_check():
    """API: Verificar si un email está suscrito"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'subscribed': False})
    
    subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
    
    return jsonify({
        'subscribed': subscriber is not None and subscriber.is_active,
        'confirmed': subscriber.is_confirmed if subscriber else False
    })
