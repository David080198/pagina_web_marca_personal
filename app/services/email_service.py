"""
Servicio de Email - CODEXSOTO
==============================
Gestión centralizada de envío de emails
"""

from flask import current_app, render_template, url_for
from flask_mail import Message
from app.extensions import mail
from threading import Thread


class EmailService:
    """Servicio centralizado para envío de emails"""
    
    @staticmethod
    def send_async(app, msg):
        """Envía email de forma asíncrona"""
        with app.app_context():
            try:
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(f'Error enviando email: {e}')
    
    @classmethod
    def send_email(cls, to, subject, template=None, html_content=None, text_content=None, **kwargs):
        """
        Envía un email
        
        Args:
            to: Email del destinatario
            subject: Asunto del email
            template: Nombre del template (sin extensión)
            html_content: Contenido HTML directo
            text_content: Contenido texto plano
            **kwargs: Variables para el template
        """
        app = current_app._get_current_object()
        
        msg = Message(
            subject=f'[CodexSoto] {subject}',
            recipients=[to] if isinstance(to, str) else to,
            sender=app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        if template:
            msg.html = render_template(f'emails/{template}.html', **kwargs)
            msg.body = render_template(f'emails/{template}.txt', **kwargs)
        else:
            msg.html = html_content
            msg.body = text_content or ''
        
        # Enviar de forma asíncrona
        thread = Thread(target=cls.send_async, args=[app, msg])
        thread.start()
    
    @classmethod
    def send_welcome_email(cls, user):
        """Envía email de bienvenida"""
        cls.send_email(
            to=user.email,
            subject='¡Bienvenido a CodexSoto!',
            html_content=f'''
            <h2>¡Hola {user.first_name or user.username}!</h2>
            <p>Gracias por unirte a CodexSoto. Estamos emocionados de tenerte con nosotros.</p>
            <p>Ahora tienes acceso a:</p>
            <ul>
                <li>Cursos gratuitos de programación</li>
                <li>Artículos técnicos</li>
                <li>Blog con las últimas novedades</li>
                <li>Newsletter con contenido exclusivo</li>
            </ul>
            <p><a href="{url_for('main.courses', _external=True)}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Explorar Cursos</a></p>
            <p>Saludos,<br>David Soto<br>CodexSoto</p>
            ''',
            text_content=f'''
            ¡Hola {user.first_name or user.username}!
            
            Gracias por unirte a CodexSoto.
            
            Explora nuestros cursos en: {url_for('main.courses', _external=True)}
            
            Saludos,
            David Soto - CodexSoto
            '''
        )
    
    @classmethod
    def send_password_reset(cls, user, reset_url):
        """Envía email de restablecimiento de contraseña"""
        cls.send_email(
            to=user.email,
            subject='Restablece tu contraseña',
            html_content=f'''
            <h2>Hola {user.first_name or user.username},</h2>
            <p>Recibimos una solicitud para restablecer tu contraseña.</p>
            <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>
            <p><a href="{reset_url}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Restablecer Contraseña</a></p>
            <p>Este enlace expirará en 1 hora.</p>
            <p>Si no solicitaste este cambio, puedes ignorar este email.</p>
            <p>Saludos,<br>CodexSoto</p>
            ''',
            text_content=f'''
            Hola {user.first_name or user.username},
            
            Visita el siguiente enlace para restablecer tu contraseña:
            {reset_url}
            
            El enlace expira en 1 hora.
            
            Saludos,
            CodexSoto
            '''
        )
    
    @classmethod
    def send_email_verification(cls, user, verification_url):
        """Envía email de verificación"""
        cls.send_email(
            to=user.email,
            subject='Verifica tu email',
            html_content=f'''
            <h2>Hola {user.first_name or user.username},</h2>
            <p>Por favor verifica tu email haciendo clic en el siguiente enlace:</p>
            <p><a href="{verification_url}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verificar Email</a></p>
            <p>Saludos,<br>CodexSoto</p>
            ''',
            text_content=f'''
            Hola {user.first_name or user.username},
            
            Verifica tu email visitando:
            {verification_url}
            
            Saludos,
            CodexSoto
            '''
        )
    
    @classmethod
    def send_enrollment_confirmation(cls, enrollment):
        """Envía confirmación de inscripción"""
        user = enrollment.user
        course = enrollment.course
        
        cls.send_email(
            to=user.email,
            subject=f'Inscripción confirmada: {course.title}',
            html_content=f'''
            <h2>¡Felicitaciones {user.first_name or user.username}!</h2>
            <p>Tu inscripción al curso <strong>{course.title}</strong> ha sido confirmada.</p>
            <p>Ya puedes acceder al contenido del curso:</p>
            <p><a href="{url_for('lessons.course_player', course_slug=course.slug, _external=True)}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Ir al Curso</a></p>
            <p>¡Éxito en tu aprendizaje!</p>
            <p>Saludos,<br>CodexSoto</p>
            '''
        )
    
    @classmethod
    def send_subscription_confirmation(cls, subscription):
        """Envía confirmación de suscripción premium"""
        user = subscription.user
        plan_name = subscription.get_plan_name()
        
        cls.send_email(
            to=user.email,
            subject=f'Suscripción {plan_name} activada',
            html_content=f'''
            <h2>¡Bienvenido al plan {plan_name}!</h2>
            <p>Hola {user.first_name or user.username},</p>
            <p>Tu suscripción ha sido activada exitosamente.</p>
            <p>Ahora tienes acceso a:</p>
            <ul>
                {''.join(f'<li>{feature}</li>' for feature in subscription.get_features())}
            </ul>
            <p><a href="{url_for('subscriptions.my_subscription', _external=True)}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Ver Mi Suscripción</a></p>
            <p>Saludos,<br>CodexSoto</p>
            '''
        )
    
    @classmethod
    def send_certificate_issued(cls, certificate):
        """Envía notificación de certificado emitido"""
        user = certificate.user
        
        cls.send_email(
            to=user.email,
            subject=f'¡Certificado disponible: {certificate.course_title}!',
            html_content=f'''
            <h2>¡Felicitaciones {certificate.recipient_name}!</h2>
            <p>Has completado exitosamente el curso <strong>{certificate.course_title}</strong>.</p>
            <p>Tu certificado está listo para descargar:</p>
            <p><a href="{url_for('certificates.view', code=certificate.certificate_code, _external=True)}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Ver Certificado</a></p>
            <p>Código de verificación: <strong>{certificate.certificate_code}</strong></p>
            <p>¡Compártelo en tus redes sociales!</p>
            <p>Saludos,<br>CodexSoto</p>
            '''
        )
    
    @classmethod
    def send_payment_received(cls, payment):
        """Notifica que el pago fue recibido y está en revisión"""
        user = payment.enrollment.user
        course = payment.enrollment.course
        
        cls.send_email(
            to=user.email,
            subject='Pago recibido - En revisión',
            html_content=f'''
            <h2>Hola {user.first_name or user.username},</h2>
            <p>Hemos recibido tu comprobante de pago para el curso <strong>{course.title}</strong>.</p>
            <p>Nuestro equipo está verificando el pago. Te notificaremos cuando sea aprobado.</p>
            <p>Referencia de pago: <strong>{payment.transaction_reference or payment.id}</strong></p>
            <p>Gracias por tu paciencia.</p>
            <p>Saludos,<br>CodexSoto</p>
            '''
        )
    
    @classmethod
    def send_payment_approved(cls, payment):
        """Notifica que el pago fue aprobado"""
        user = payment.enrollment.user
        course = payment.enrollment.course
        
        cls.send_email(
            to=user.email,
            subject=f'¡Pago aprobado! Acceso a {course.title}',
            html_content=f'''
            <h2>¡Excelentes noticias {user.first_name or user.username}!</h2>
            <p>Tu pago ha sido verificado y aprobado.</p>
            <p>Ya tienes acceso completo al curso <strong>{course.title}</strong>.</p>
            <p><a href="{url_for('lessons.course_player', course_slug=course.slug, _external=True)}" style="background-color: #10b981; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Comenzar el Curso</a></p>
            <p>¡Disfruta tu aprendizaje!</p>
            <p>Saludos,<br>CodexSoto</p>
            '''
        )
    
    @classmethod
    def send_payment_rejected(cls, payment, reason=None):
        """Notifica que el pago fue rechazado"""
        user = payment.enrollment.user
        course = payment.enrollment.course
        
        reason_text = f'<p><strong>Motivo:</strong> {reason}</p>' if reason else ''
        
        cls.send_email(
            to=user.email,
            subject='Pago no aprobado - Acción requerida',
            html_content=f'''
            <h2>Hola {user.first_name or user.username},</h2>
            <p>Lamentamos informarte que no pudimos verificar tu pago para el curso <strong>{course.title}</strong>.</p>
            {reason_text}
            <p>Por favor, verifica la información y vuelve a intentarlo, o contacta con soporte si crees que es un error.</p>
            <p><a href="{url_for('main.contact', _external=True)}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Contactar Soporte</a></p>
            <p>Saludos,<br>CodexSoto</p>
            '''
        )
