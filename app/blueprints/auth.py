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
