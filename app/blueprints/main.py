from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import current_user
from flask_mail import Message
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.project import Project
from app.models.site_config import SiteConfig
from app.models.contact import ContactMessage
from app.extensions import db, mail, csrf

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    config = SiteConfig.query.first()
    featured_projects = Project.query.filter_by(published=True, featured=True).limit(3).all()
    featured_courses = Course.query.filter_by(published=True, featured=True).limit(3).all()
    recent_posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).limit(3).all()
    
    return render_template('index.html', 
                         config=config,
                         featured_projects=featured_projects,
                         featured_courses=featured_courses,
                         recent_posts=recent_posts)

@main_bp.route('/investigacion')
def research():
    config = SiteConfig.query.first()
    research_projects = Project.query.filter_by(published=True, category='research').all()
    
    return render_template('research.html', 
                         config=config,
                         projects=research_projects)

@main_bp.route('/automatizaciones')
def automation():
    config = SiteConfig.query.first()
    automation_projects = Project.query.filter_by(published=True, category='automation').all()
    
    return render_template('automation.html', 
                         config=config,
                         projects=automation_projects)

@main_bp.route('/cursos')
def courses():
    config = SiteConfig.query.first()
    all_courses = Course.query.filter_by(published=True).all()
    
    return render_template('courses.html', 
                         config=config,
                         courses=all_courses)

@main_bp.route('/curso/<slug>')
def course_detail(slug):
    config = SiteConfig.query.first()
    course = Course.query.filter_by(slug=slug, published=True).first_or_404()
    
    # Verificar inscripción existente si el usuario está autenticado
    existing_enrollment = None
    if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        try:
            from app.models.enrollment import CourseEnrollment
            existing_enrollment = CourseEnrollment.query.filter_by(
                user_id=current_user.id,
                course_id=course.id
            ).first()
        except ImportError:
            # Si no existe el modelo de inscripción, continuar sin error
            pass
    
    return render_template('course_detail.html', 
                         config=config,
                         course=course,
                         existing_enrollment=existing_enrollment)

@main_bp.route('/blog')
def blog():
    config = SiteConfig.query.first()
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False)
    
    return render_template('blog.html', 
                         config=config,
                         posts=posts)

@main_bp.route('/blog/<slug>')
def blog_post(slug):
    config = SiteConfig.query.first()
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    
    return render_template('blog_post.html', 
                         config=config,
                         post=post)

@main_bp.route('/proyectos')
def projects():
    config = SiteConfig.query.first()
    all_projects = Project.query.filter_by(published=True).all()
    
    return render_template('projects.html', 
                         config=config,
                         projects=all_projects)

@main_bp.route('/contacto', methods=['GET', 'POST'])
def contact():
    config = SiteConfig.query.first()
    
    current_app.logger.warning("=== DEBUG FORMULARIO CONTACTO ===")
    current_app.logger.warning(f"Método de request: {request.method}")
    
    if request.method == 'POST':
        current_app.logger.warning("--- DATOS RAW DEL FORMULARIO ---")
        current_app.logger.warning(f"request.form: {dict(request.form)}")
        
        # Obtener datos del formulario directamente
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', 'Contacto desde la web').strip()
        message = request.form.get('message', '').strip()
        
        current_app.logger.warning(f"Nombre capturado: '{name}'")
        current_app.logger.warning(f"Email capturado: '{email}'")
        current_app.logger.warning(f"Asunto capturado: '{subject}'")
        current_app.logger.warning(f"Mensaje capturado: '{message}'")
        
        # Validación básica
        if not name or not email or not message:
            flash('Por favor completa todos los campos requeridos.', 'error')
            current_app.logger.warning("--- VALIDACIÓN FALLIDA ---")
            return render_template('contact.html', config=config)
        
        if len(message) < 10:
            flash('El mensaje debe tener al menos 10 caracteres.', 'error')
            current_app.logger.warning("--- MENSAJE MUY CORTO ---")
            return render_template('contact.html', config=config)
        
        # Guardar mensaje en la base de datos
        try:
            contact_message = ContactMessage(
                name=name,
                email=email,
                subject=subject or 'Contacto desde la web',
                message=message
            )
            
            db.session.add(contact_message)
            db.session.commit()
            current_app.logger.warning("--- MENSAJE GUARDADO EN BD EXITOSAMENTE ---")
            current_app.logger.warning(f"ID del mensaje: {contact_message.id}")
        except Exception as e:
            current_app.logger.error(f"--- ERROR AL GUARDAR EN BD ---")
            current_app.logger.error(f"Error: {e}")
            db.session.rollback()
            flash('Error al enviar el mensaje. Inténtalo de nuevo.', 'error')
            return render_template('contact.html', config=config)
        
        # Configurar sender
        import os
        mail_sender = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME') or 'codexsoto@gmail.com'
        
        # Enviar email al administrador
        try:
            recipient_email = config.contact_email if config and config.contact_email else 'codexsoto@gmail.com'
            current_app.logger.warning(f"--- INTENTANDO ENVIAR EMAIL ---")
            current_app.logger.warning(f"Destinatario: {recipient_email}")
            current_app.logger.warning(f"Sender: {mail_sender}")
            current_app.logger.warning(f"MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}")
            current_app.logger.warning(f"MAIL_USERNAME: {current_app.config.get('MAIL_USERNAME')}")
            
            msg = Message(
                subject=f'[CodexSoto] {subject}',
                sender=mail_sender,
                recipients=[recipient_email],
                body=f'Nombre: {name}\nEmail: {email}\n\nMensaje:\n{message}'
            )
            mail.send(msg)
            current_app.logger.warning("--- EMAIL ENVIADO EXITOSAMENTE ---")
        except Exception as e:
            current_app.logger.error(f"--- ERROR ENVIANDO EMAIL ---")
            current_app.logger.error(f"Error: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
        
        # Enviar email de confirmación al usuario
        try:
            confirmation_msg = Message(
                subject='Gracias por contactarnos - CodexSoto',
                sender=mail_sender,
                recipients=[email],
                body=f'''Hola {name},

¡Gracias por contactarnos! Hemos recibido tu mensaje y te responderemos lo antes posible.

Resumen de tu mensaje:
- Asunto: {subject}
- Mensaje: {message[:200]}{'...' if len(message) > 200 else ''}

Saludos,
El equipo de CodexSoto
'''
            )
            mail.send(confirmation_msg)
            current_app.logger.warning("--- EMAIL DE CONFIRMACIÓN ENVIADO AL USUARIO ---")
        except Exception as e:
            current_app.logger.error(f"--- ERROR ENVIANDO EMAIL DE CONFIRMACIÓN ---")
            current_app.logger.error(f"Error: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
        
        flash('Mensaje enviado correctamente. Te contactaré pronto.', 'success')
        current_app.logger.warning("--- REDIRIGIENDO DESPUÉS DE ÉXITO ---")
        return redirect(url_for('main.contact'))
    
    current_app.logger.warning("--- RENDERIZANDO TEMPLATE ---")
    current_app.logger.warning("=== FIN DEBUG ===")
    return render_template('contact.html', config=config)

@main_bp.route('/proyecto/<slug>')
def project_detail(slug):
    config = SiteConfig.query.first()
    project = Project.query.filter_by(slug=slug, published=True).first_or_404()
    
    return render_template('project_detail.html', 
                         config=config,
                         project=project)
