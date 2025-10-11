from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class ContactForm(FlaskForm):
    """Formulario de contacto con validación CSRF automática"""
    
    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        print("--- CONTACTFORM INICIALIZADO ---")
    
    name = StringField(
        'Nombre',
        validators=[
            DataRequired(message='El nombre es requerido'),
            Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
        ],
        render_kw={'class': 'form-control', 'placeholder': 'Tu nombre completo'}
    )
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='El email es requerido'),
            Email(message='Por favor ingresa un email válido')
        ],
        render_kw={'class': 'form-control', 'placeholder': 'tu@email.com'}
    )
    
    subject = StringField(
        'Asunto',
        validators=[
            Length(max=200, message='El asunto no puede exceder 200 caracteres')
        ],
        render_kw={'class': 'form-control', 'placeholder': 'Asunto del mensaje (opcional)'}
    )
    
    message = TextAreaField(
        'Mensaje',
        validators=[
            DataRequired(message='El mensaje es requerido'),
            Length(min=10, max=1000, message='El mensaje debe tener entre 10 y 1000 caracteres')
        ],
        render_kw={
            'class': 'form-control', 
            'rows': 5, 
            'placeholder': 'Escribe tu mensaje aquí...'
        }
    )
    
    submit = SubmitField(
        'Enviar Mensaje',
        render_kw={'class': 'btn btn-primary w-100'}
    )