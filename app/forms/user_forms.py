from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, URL
from app.models.user import User
import re

class RegistrationForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[
        DataRequired(message='El nombre de usuario es requerido'),
        Length(min=3, max=20, message='El nombre de usuario debe tener entre 3 y 20 caracteres')
    ])
    
    email = EmailField('Correo electrónico', validators=[
        DataRequired(message='El correo electrónico es requerido'),
        Email(message='Ingrese un correo electrónico válido')
    ])
    
    first_name = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=50, message='El nombre debe tener entre 2 y 50 caracteres')
    ])
    
    last_name = StringField('Apellido', validators=[
        DataRequired(message='El apellido es requerido'),
        Length(min=2, max=50, message='El apellido debe tener entre 2 y 50 caracteres')
    ])
    
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida'),
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
    ])
    
    password2 = PasswordField('Confirmar contraseña', validators=[
        DataRequired(message='Confirme su contraseña'),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    
    newsletter_subscribed = BooleanField('Quiero recibir el newsletter con actualizaciones')
    terms_accepted = BooleanField('Acepto los términos y condiciones', validators=[
        DataRequired(message='Debe aceptar los términos y condiciones')
    ])
    
    def validate_username(self, username):
        # Verificar que no contenga caracteres especiales
        if not re.match("^[a-zA-Z0-9_]+$", username.data):
            raise ValidationError('El nombre de usuario solo puede contener letras, números y guiones bajos')
        
        # Verificar que no esté en uso
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este correo electrónico ya está registrado')
    
    def validate_password(self, password):
        # Validar complejidad de contraseña
        if not re.search(r'[A-Za-z]', password.data):
            raise ValidationError('La contraseña debe contener al menos una letra')
        if not re.search(r'[0-9]', password.data):
            raise ValidationError('La contraseña debe contener al menos un número')

class LoginForm(FlaskForm):
    username_or_email = StringField('Usuario o Email', validators=[
        DataRequired(message='Ingrese su usuario o email')
    ])
    
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='Ingrese su contraseña')
    ])
    
    remember_me = BooleanField('Recordarme')

class ProfileEditForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[
        DataRequired(message='El nombre de usuario es requerido'),
        Length(min=3, max=20, message='El nombre de usuario debe tener entre 3 y 20 caracteres')
    ])
    
    email = EmailField('Correo electrónico', validators=[
        DataRequired(message='El correo electrónico es requerido'),
        Email(message='Ingrese un correo electrónico válido')
    ])
    
    first_name = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=50)
    ])
    
    last_name = StringField('Apellido', validators=[
        DataRequired(message='El apellido es requerido'),
        Length(min=2, max=50)
    ])
    
    bio = TextAreaField('Biografía', validators=[
        Length(max=500, message='La biografía no puede exceder 500 caracteres')
    ])
    
    location = StringField('Ubicación', validators=[Length(max=100)])
    
    website = StringField('Sitio web', validators=[
        Optional(),
        URL(message='Ingrese una URL válida')
    ])
    
    avatar_file = FileField('Foto de perfil', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Solo se permiten imágenes')
    ])
    
    # Preferencias
    preferred_language = SelectField('Idioma preferido', choices=[
        ('es', 'Español'),
        ('en', 'English')
    ])
    
    theme_preference = SelectField('Tema', choices=[
        ('auto', 'Automático'),
        ('light', 'Claro'),
        ('dark', 'Oscuro')
    ])
    
    newsletter_subscribed = BooleanField('Recibir newsletter')
    email_notifications = BooleanField('Notificaciones por email')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            if not re.match("^[a-zA-Z0-9_]+$", username.data):
                raise ValidationError('El nombre de usuario solo puede contener letras, números y guiones bajos')
            
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Este nombre de usuario ya está en uso')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Este correo electrónico ya está registrado')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Contraseña actual', validators=[
        DataRequired(message='Ingrese su contraseña actual')
    ])
    
    new_password = PasswordField('Nueva contraseña', validators=[
        DataRequired(message='Ingrese la nueva contraseña'),
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
    ])
    
    new_password2 = PasswordField('Confirmar nueva contraseña', validators=[
        DataRequired(message='Confirme la nueva contraseña'),
        EqualTo('new_password', message='Las contraseñas deben coincidir')
    ])
    
    def validate_new_password(self, new_password):
        if not re.search(r'[A-Za-z]', new_password.data):
            raise ValidationError('La contraseña debe contener al menos una letra')
        if not re.search(r'[0-9]', new_password.data):
            raise ValidationError('La contraseña debe contener al menos un número')

class CommentForm(FlaskForm):
    content = TextAreaField('Comentario', validators=[
        DataRequired(message='El comentario no puede estar vacío'),
        Length(min=5, max=1000, message='El comentario debe tener entre 5 y 1000 caracteres')
    ])
    
    parent_id = StringField('Parent ID')  # Para respuestas a comentarios
