from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SelectField, StringField, TextAreaField, FloatField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models.enrollment import PaymentMethod

class CourseEnrollmentForm(FlaskForm):
    course_id = HiddenField('Course ID', validators=[DataRequired()])
    
    # Información de contacto adicional (opcional)
    phone = StringField('Teléfono de contacto', validators=[
        Optional(),
        Length(max=20, message='El teléfono no puede exceder 20 caracteres')
    ])
    
    # Observaciones del estudiante
    student_notes = TextAreaField('Comentarios adicionales', validators=[
        Optional(),
        Length(max=500, message='Los comentarios no pueden exceder 500 caracteres')
    ])
    
    # Campos para transferencia bancaria
    transfer_sender_name = StringField('Nombre completo del emisor', validators=[
        DataRequired(message='El nombre del emisor es requerido'),
        Length(max=100, message='El nombre no puede exceder 100 caracteres')
    ])
    
    transfer_reference = StringField('Referencia de transferencia', validators=[
        DataRequired(message='La referencia de transferencia es requerida'),
        Length(max=50, message='La referencia no puede exceder 50 caracteres')
    ])
    
    bank_account_used = SelectField('Cuenta bancaria utilizada', choices=[
        ('', 'Selecciona la cuenta a la que transferiste'),
        ('banco_nacional', 'Banco Nacional - 1234-5678-9012'),
        ('banco_internacional', 'Banco Internacional - 9876-5432-1098')
    ], validators=[DataRequired(message='Selecciona la cuenta bancaria utilizada')])
    
    transfer_amount = StringField('Monto transferido', validators=[
        DataRequired(message='El monto transferido es requerido'),
        Length(max=20, message='El monto no puede exceder 20 caracteres')
    ])
    
    # Comprobante de pago
    payment_receipt = FileField('Comprobante de transferencia', validators=[
        DataRequired(message='El comprobante de transferencia es requerido'),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Solo se permiten archivos JPG, PNG o PDF')
    ])

class PaymentForm(FlaskForm):
    enrollment_id = HiddenField('Enrollment ID', validators=[DataRequired()])
    
    payment_method = SelectField('Método de Pago', choices=[
        (PaymentMethod.BANK_TRANSFER.value, 'Transferencia Bancaria'),
        (PaymentMethod.PAYPAL.value, 'PayPal'),
        (PaymentMethod.CREDIT_CARD.value, 'Tarjeta de Crédito')
    ], validators=[DataRequired(message='Seleccione un método de pago')])
    
    # Para transferencias bancarias
    transaction_reference = StringField('Referencia/ID de Transacción', validators=[
        Optional(),
        Length(max=100, message='La referencia no puede exceder 100 caracteres')
    ])
    
    bank_account_used = StringField('Cuenta bancaria utilizada (últimos 4 dígitos)', validators=[
        Optional(),
        Length(max=100, message='La información de cuenta no puede exceder 100 caracteres')
    ])
    
    # Comprobante de pago
    proof_of_payment = FileField('Comprobante de Pago', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Solo se permiten archivos JPG, PNG o PDF')
    ])
    
    # Notas adicionales
    payment_notes = TextAreaField('Notas adicionales', validators=[
        Optional(),
        Length(max=500, message='Las notas no pueden exceder 500 caracteres')
    ])
    
    def validate_transaction_reference(self, field):
        """Validar referencia de transacción según el método de pago"""
        if self.payment_method.data == PaymentMethod.BANK_TRANSFER.value:
            if not field.data:
                raise ValidationError('La referencia de transacción es requerida para transferencias bancarias')

class PaymentApprovalForm(FlaskForm):
    """Formulario para que los admins aprueben/rechacen pagos"""
    action = SelectField('Acción', choices=[
        ('approve', 'Aprobar Pago'),
        ('reject', 'Rechazar Pago')
    ], validators=[DataRequired()])
    
    admin_notes = TextAreaField('Notas del Administrador', validators=[
        Optional(),
        Length(max=1000, message='Las notas no pueden exceder 1000 caracteres')
    ])
    
    rejection_reason = TextAreaField('Razón de Rechazo', validators=[
        Optional(),
        Length(max=500, message='La razón no puede exceder 500 caracteres')
    ])
    
    def validate_rejection_reason(self, field):
        """Validar que se proporcione razón si se rechaza"""
        if self.action.data == 'reject' and not field.data:
            raise ValidationError('Debe proporcionar una razón para rechazar el pago')

class BankAccountForm(FlaskForm):
    """Formulario para configurar cuentas bancarias del sitio"""
    bank_name = StringField('Nombre del Banco', validators=[
        DataRequired(message='El nombre del banco es requerido'),
        Length(max=100)
    ])
    
    account_type = SelectField('Tipo de Cuenta', choices=[
        ('checking', 'Cuenta Corriente'),
        ('savings', 'Cuenta de Ahorros')
    ], validators=[DataRequired()])
    
    account_number = StringField('Número de Cuenta', validators=[
        DataRequired(message='El número de cuenta es requerido'),
        Length(max=50)
    ])
    
    account_holder = StringField('Titular de la Cuenta', validators=[
        DataRequired(message='El titular es requerido'),
        Length(max=100)
    ])
    
    routing_number = StringField('Número de Ruta/SWIFT', validators=[
        Optional(),
        Length(max=20)
    ])
    
    is_active = SelectField('Estado', choices=[
        ('1', 'Activa'),
        ('0', 'Inactiva')
    ], coerce=int, default=1)
