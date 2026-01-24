from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.comment import Comment
from app.models.favorite import Favorite
from app.extensions import db
from app.forms.user_forms import RegistrationForm, LoginForm, ProfileEditForm, ChangePasswordForm
from app.utils.file_upload import save_uploaded_file, delete_uploaded_file
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data.lower(),
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                newsletter_subscribed=form.newsletter_subscribed.data,
                role='user'
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('¡Registro exitoso! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la cuenta. Inténtalo de nuevo.', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        next_page = request.args.get('next')
        if current_user.is_admin:
            return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
        else:
            return redirect(next_page) if next_page else redirect(url_for('user.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username_or_email = form.username_or_email.data
        password = form.password.data
        remember = form.remember_me.data
        
        # Buscar por username o email
        user = None
        if '@' in username_or_email:
            user = User.query.filter_by(email=username_or_email.lower()).first()
        else:
            user = User.query.filter_by(username=username_or_email).first()
        
        if user and user.check_password(password) and user.is_active:
            # Actualizar último login
            user.last_login = datetime.utcnow()
            user.update_last_seen()
            db.session.commit()
            
            login_user(user, remember=remember)
            
            next_page = request.args.get('next')
            if user.is_admin:
                return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
            else:
                return redirect(next_page) if next_page else redirect(url_for('user.dashboard'))
        else:
            flash('Credenciales incorrectas o cuenta inactiva', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/reset-admin-secret-2026')
def reset_admin():
    """Ruta temporal para resetear credenciales de admin - ELIMINAR DESPUÉS DE USAR"""
    try:
        # Credenciales fijas
        admin_email = 'david@codexsoto.com'
        admin_password = 'MiPasswordSeguro123!'
        admin_username = 'david'
        
        # Buscar cualquier admin existente
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User.query.filter_by(username='administrador').first()
        if not admin_user:
            admin_user = User.query.filter_by(username='david').first()
        
        if admin_user:
            # Actualizar
            admin_user.username = admin_username
            admin_user.email = admin_email
            admin_user.set_password(admin_password)
            admin_user.is_admin = True
            admin_user.role = 'admin'
            admin_user.is_active = True
            admin_user.email_verified = True
            db.session.commit()
            return f"""
            <h1>✅ Admin actualizado!</h1>
            <p><strong>Email:</strong> {admin_email}</p>
            <p><strong>Username:</strong> {admin_username}</p>
            <p><strong>Password:</strong> {admin_password}</p>
            <p><a href="/auth/login">Ir al Login</a></p>
            <p style="color:red"><strong>⚠️ ELIMINA ESTA RUTA DESPUÉS DE USAR!</strong></p>
            """
        else:
            # Crear nuevo
            admin_user = User(
                username=admin_username,
                email=admin_email,
                first_name='David',
                last_name='Soto',
                role='admin',
                is_admin=True,
                is_active=True,
                email_verified=True
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            return f"""
            <h1>✅ Admin CREADO!</h1>
            <p><strong>Email:</strong> {admin_email}</p>
            <p><strong>Username:</strong> {admin_username}</p>
            <p><strong>Password:</strong> {admin_password}</p>
            <p><a href="/auth/login">Ir al Login</a></p>
            <p style="color:red"><strong>⚠️ ELIMINA ESTA RUTA DESPUÉS DE USAR!</strong></p>
            """
    except Exception as e:
        db.session.rollback()
        return f"<h1>❌ Error:</h1><pre>{str(e)}</pre>"
