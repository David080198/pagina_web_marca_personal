from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash
import os
from app.extensions import db, mail
from app.models.user import User

password_reset_bp = Blueprint('password_reset', __name__)

# Configurar serializador para tokens de reset
def get_serializer():
    return URLSafeTimedSerializer(os.environ.get('SECRET_KEY', 'dev-secret'))

@password_reset_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Solicitar reset de contraseña"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Por favor ingresa tu correo electrónico.', 'warning')
            return redirect(url_for('password_reset.forgot_password'))
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generar token de reset
            serializer = get_serializer()
            token = serializer.dumps(user.id, salt='password-reset-salt')
            
            # Crear enlace de reset
            reset_url = url_for('password_reset.reset_password', token=token, _external=True)
            
            # Enviar email
            try:
                mail_sender = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME') or 'codexsoto@gmail.com'
                msg = Message(
                    subject='Restablecer Contraseña - CODEXSOTO',
                    sender=mail_sender,
                    recipients=[user.email],
                    html=render_template('auth/reset_password_email.html', 
                                       user=user, 
                                       reset_url=reset_url)
                )
                mail.send(msg)
                flash('Se ha enviado un correo con las instrucciones para resetear tu contraseña.', 'success')
            except Exception as e:
                print(f"Error enviando email: {e}")
                flash('Error al enviar el correo. Por favor intenta más tarde.', 'danger')
        else:
            # Informar que el correo no está registrado
            flash('El correo electrónico no está registrado en nuestro sistema.', 'danger')
            return redirect(url_for('password_reset.forgot_password'))
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@password_reset_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Resetear contraseña con token válido"""
    serializer = get_serializer()
    
    try:
        # Validar token (válido por 24 horas)
        user_id = serializer.loads(token, salt='password-reset-salt', max_age=86400)
        user = User.query.get(user_id)
        
        if not user:
            flash('Token inválido o expirado.', 'danger')
            return redirect(url_for('auth.login'))
        
    except Exception as e:
        print(f"Error validando token: {e}")
        flash('El enlace de reset ha expirado. Por favor solicita uno nuevo.', 'danger')
        return redirect(url_for('password_reset.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            flash('Por favor completa todos los campos.', 'warning')
            return redirect(url_for('password_reset.reset_password', token=token))
        
        if new_password != confirm_password:
            flash('Las contraseñas no coinciden.', 'warning')
            return redirect(url_for('password_reset.reset_password', token=token))
        
        if len(new_password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'warning')
            return redirect(url_for('password_reset.reset_password', token=token))
        
        # Actualizar contraseña
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Tu contraseña ha sido actualizada exitosamente. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)
