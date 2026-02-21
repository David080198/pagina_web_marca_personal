from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.project import Project
from app.models.site_config import SiteConfig
from app.models.contact import ContactMessage
from app.models.enrollment import CourseEnrollment, Payment, PaymentStatus, EnrollmentStatus
from app.models.user import User
from app.extensions import db
from app.utils.file_upload import save_uploaded_file, delete_uploaded_file
import os
from werkzeug.utils import secure_filename
import json
import re
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def slugify(text):
    """Convierte un texto en un slug válido para URLs"""
    # Convertir a minúsculas
    text = text.lower()
    # Reemplazar espacios y caracteres especiales con guiones
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    # Eliminar guiones al inicio y final
    return text.strip('-')

def admin_required(f):
    """Decorador para requerir permisos de administrador"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Estadísticas del dashboard
    total_posts = BlogPost.query.count()
    published_posts = BlogPost.query.filter_by(published=True).count()
    total_courses = Course.query.count()
    total_projects = Project.query.count()
    unread_messages = ContactMessage.query.filter_by(read=False).count()
    
    # Estadísticas de usuarios
    total_users = User.query.filter_by(is_admin=False).count()
    recent_users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).limit(10).all()
    
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    
    # Obtener estadísticas de analytics
    from app.utils.analytics import get_analytics_summary
    analytics = get_analytics_summary()
    
    return render_template('admin/dashboard.html',
                         total_posts=total_posts,
                         published_posts=published_posts,
                         total_courses=total_courses,
                         total_projects=total_projects,
                         unread_messages=unread_messages,
                         total_users=total_users,
                         recent_users=recent_users,
                         recent_messages=recent_messages,
                         analytics=analytics)

# Configuración del sitio
@admin_bp.route('/config', methods=['GET', 'POST'])
@login_required
@admin_required
def site_config():
    config = SiteConfig.query.first()
    if not config:
        config = SiteConfig()
        db.session.add(config)
    
    if request.method == 'POST':
        config.site_name = request.form.get('site_name')
        config.site_description = request.form.get('site_description')
        config.primary_color = request.form.get('primary_color')
        config.secondary_color = request.form.get('secondary_color')
        config.dark_mode = bool(request.form.get('dark_mode'))
        config.hero_title = request.form.get('hero_title')
        config.hero_subtitle = request.form.get('hero_subtitle')
        config.about_text = request.form.get('about_text')
        config.contact_email = request.form.get('contact_email')
        config.linkedin_url = request.form.get('linkedin_url')
        config.github_url = request.form.get('github_url')
        config.twitter_url = request.form.get('twitter_url')
        config.youtube_url = request.form.get('youtube_url')
        config.instagram_url = request.form.get('instagram_url')
        config.facebook_url = request.form.get('facebook_url')
        config.tiktok_url = request.form.get('tiktok_url')
        config.discord_url = request.form.get('discord_url')
        config.telegram_url = request.form.get('telegram_url')
        config.whatsapp_url = request.form.get('whatsapp_url')
        
        db.session.commit()
        flash('Configuración actualizada correctamente', 'success')
        return redirect(url_for('admin.site_config'))
    
    return render_template('admin/config.html', config=config)

# Gestión del blog
@admin_bp.route('/blog')
@login_required
@admin_required
def blog_list():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog_list.html', posts=posts)

def generate_unique_slug(base_slug, model_class, exclude_id=None):
    """Genera un slug único agregando un número si es necesario"""
    slug = base_slug
    counter = 1
    
    while True:
        query = model_class.query.filter_by(slug=slug)
        if exclude_id:
            query = query.filter(model_class.id != exclude_id)
        
        if not query.first():
            return slug
        
        slug = f"{base_slug}-{counter}"
        counter += 1

@admin_bp.route('/blog/new', methods=['GET', 'POST'])
@login_required
@admin_required
def blog_new():
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        summary = request.form.get('summary')
        tags = request.form.get('tags')
        published = 'published' in request.form
        
        # Manejar imagen
        image_url = request.form.get('image_url')
        image_file = request.files.get('image_file')
        
        # Validar que el slug no esté vacío
        if not slug:
            flash('El slug es requerido', 'error')
            return render_template('admin/blog_edit.html', post=None)
        
        # Generar slug único
        unique_slug = generate_unique_slug(slug, BlogPost)
        
        try:
            # Procesar imagen si se subió un archivo
            if image_file and image_file.filename:
                try:
                    image_url = save_uploaded_file(image_file, 'uploads/blog')
                except ValueError as e:
                    flash(f'Error con la imagen: {str(e)}', 'error')
                    return render_template('admin/blog_edit.html', post=None)
            
            post = BlogPost(
                title=title,
                slug=unique_slug,
                content=content,
                summary=summary,
                tags=tags,
                image_url=image_url,
                published=published
            )
            
            db.session.add(post)
            db.session.commit()
            
            if unique_slug != slug:
                flash(f'Post creado correctamente. El slug se cambió a "{unique_slug}" para evitar duplicados.', 'warning')
            else:
                flash('Post creado correctamente', 'success')
            
            return redirect(url_for('admin.blog_list'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el post. Inténtalo de nuevo.', 'error')
            return render_template('admin/blog_edit.html', post=None)
    
    return render_template('admin/blog_edit.html', post=None)

@admin_bp.route('/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def blog_edit(post_id):
    post = BlogPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        summary = request.form.get('summary')
        tags = request.form.get('tags')
        published = 'published' in request.form
        
        # Manejar imagen
        image_url = request.form.get('image_url')
        image_file = request.files.get('image_file')
        
        # Validar que el slug no esté vacío
        if not slug:
            flash('El slug es requerido', 'error')
            return render_template('admin/blog_edit.html', post=post)
        
        # Generar slug único (excluyendo el post actual)
        unique_slug = generate_unique_slug(slug, BlogPost, exclude_id=post_id)
        
        try:
            # Procesar imagen si se subió un archivo
            if image_file and image_file.filename:
                try:
                    # Eliminar imagen anterior si existe y es local
                    old_image = post.image_url
                    if old_image and old_image.startswith('/static/uploads/'):
                        delete_uploaded_file(old_image)
                    
                    # Guardar nueva imagen
                    image_url = save_uploaded_file(image_file, 'uploads/blog')
                except ValueError as e:
                    flash(f'Error con la imagen: {str(e)}', 'error')
                    return render_template('admin/blog_edit.html', post=post)
            
            post.title = title
            post.slug = unique_slug
            post.content = content
            post.summary = summary
            post.tags = tags
            post.image_url = image_url
            post.published = published
            post.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            if unique_slug != slug:
                flash(f'Post actualizado correctamente. El slug se cambió a "{unique_slug}" para evitar duplicados.', 'warning')
            else:
                flash('Post actualizado correctamente', 'success')
            
            return redirect(url_for('admin.blog_list'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el post. Inténtalo de nuevo.', 'error')
            return render_template('admin/blog_edit.html', post=post)
    
    return render_template('admin/blog_edit.html', post=post)

@admin_bp.route('/blog/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def blog_delete(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post eliminado correctamente', 'success')
    return redirect(url_for('admin.blog_list'))

# Gestión de cursos
@admin_bp.route('/courses')
@login_required
@admin_required
def course_list():
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('admin/course_list.html', courses=courses)

@admin_bp.route('/courses/new', methods=['GET', 'POST'])
@login_required
@admin_required
def course_new():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        content = request.form.get('content')
        price = float(request.form.get('price', 0))
        duration = int(request.form.get('duration', 0))
        level = request.form.get('level')
        language = request.form.get('language')
        video_url = request.form.get('video_url')
        published = 'published' in request.form
        featured = 'featured' in request.form
        
        # Manejar imagen
        image_url = request.form.get('image_url')
        image_file = request.files.get('image_file')
        
        # Validar que el título no esté vacío
        if not title:
            flash('El título es requerido', 'error')
            return render_template('admin/course_edit.html', course=None)
        
        # Generar slug automáticamente desde el título
        base_slug = slugify(title)
        unique_slug = generate_unique_slug(base_slug, Course)
        
        try:
            # Procesar imagen si se subió un archivo
            if image_file and image_file.filename:
                try:
                    image_url = save_uploaded_file(image_file, 'uploads/courses')
                except ValueError as e:
                    flash(f'Error con la imagen: {str(e)}', 'error')
                    return render_template('admin/course_edit.html', course=None)
            
            course = Course(
                title=title,
                slug=unique_slug,
                description=description,
                content=content,
                price=price,
                duration=duration,
                level=level,
                language=language,
                image_url=image_url,
                video_url=video_url,
                published=published,
                featured=featured
            )
            
            db.session.add(course)
            db.session.commit()
            
            if unique_slug != base_slug:
                flash(f'Curso creado correctamente. El slug se cambió a "{unique_slug}" para evitar duplicados.', 'warning')
            else:
                flash('Curso creado correctamente', 'success')
            
            return redirect(url_for('admin.course_list'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el curso. Inténtalo de nuevo.', 'error')
            return render_template('admin/course_edit.html', course=None)
    
    return render_template('admin/course_edit.html', course=None)

@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def course_edit(course_id):
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        
        # Manejar imagen
        image_url = request.form.get('image_url')
        image_file = request.files.get('image_file')
        
        # Validar que el título no esté vacío
        if not title:
            flash('El título es requerido', 'error')
            return render_template('admin/course_edit.html', course=course)
        
        try:
            # Procesar imagen si se subió un archivo
            if image_file and image_file.filename:
                try:
                    # Eliminar imagen anterior si existe y es local
                    old_image = course.image_url
                    if old_image and old_image.startswith('/static/uploads/'):
                        delete_uploaded_file(old_image)
                    
                    # Guardar nueva imagen
                    image_url = save_uploaded_file(image_file, 'uploads/courses')
                except ValueError as e:
                    flash(f'Error con la imagen: {str(e)}', 'error')
                    return render_template('admin/course_edit.html', course=course)
            
            # Solo regenerar slug si el título ha cambiado
            if title != course.title:
                base_slug = slugify(title)
                unique_slug = generate_unique_slug(base_slug, Course, exclude_id=course_id)
                course.slug = unique_slug
            
            course.title = title
            course.description = request.form.get('description')
            course.content = request.form.get('content')
            course.price = float(request.form.get('price', 0))
            course.duration = int(request.form.get('duration', 0))
            course.level = request.form.get('level')
            course.language = request.form.get('language')
            course.image_url = image_url
            course.video_url = request.form.get('video_url')
            course.published = 'published' in request.form
            course.featured = 'featured' in request.form
            course.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Curso actualizado correctamente', 'success')
            return redirect(url_for('admin.course_list'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el curso. Inténtalo de nuevo.', 'error')
            return render_template('admin/course_edit.html', course=course)
    
    return render_template('admin/course_edit.html', course=course)

@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def course_delete(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Curso eliminado correctamente', 'success')
    return redirect(url_for('admin.course_list'))

# Gestión de proyectos
@admin_bp.route('/projects')
@login_required
@admin_required
def project_list():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('admin/project_list.html', projects=projects)

@admin_bp.route('/projects/new', methods=['GET', 'POST'])
@login_required
@admin_required
def project_new():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        content = request.form.get('content')
        category = request.form.get('category')
        technologies = request.form.get('technologies')
        github_url = request.form.get('github_url')
        demo_url = request.form.get('demo_url')
        published = 'published' in request.form
        featured = 'featured' in request.form
        
        # Manejar imagen
        image_url = request.form.get('image_url')
        image_file = request.files.get('image_file')
        
        # Validar que el título no esté vacío
        if not title:
            flash('El título es requerido', 'error')
            return render_template('admin/project_edit.html', project=None)
        
        # Generar slug automáticamente desde el título
        base_slug = slugify(title)
        unique_slug = generate_unique_slug(base_slug, Project)
        
        try:
            # Procesar imagen si se subió un archivo
            if image_file and image_file.filename:
                try:
                    image_url = save_uploaded_file(image_file, 'uploads/projects')
                except ValueError as e:
                    flash(f'Error con la imagen: {str(e)}', 'error')
                    return render_template('admin/project_edit.html', project=None)
            
            project = Project(
                title=title,
                slug=unique_slug,
                description=description,
                content=content,
                category=category,
                technologies=technologies,
                github_url=github_url,
                demo_url=demo_url,
                image_url=image_url,
                published=published,
                featured=featured
            )
            
            db.session.add(project)
            db.session.commit()
            
            if unique_slug != base_slug:
                flash(f'Proyecto creado correctamente. El slug se cambió a "{unique_slug}" para evitar duplicados.', 'warning')
            else:
                flash('Proyecto creado correctamente', 'success')
            
            return redirect(url_for('admin.project_list'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el proyecto. Inténtalo de nuevo.', 'error')
            return render_template('admin/project_edit.html', project=None)
    
    return render_template('admin/project_edit.html', project=None)

@admin_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def project_edit(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        
        # Manejar imagen
        image_url = request.form.get('image_url')
        image_file = request.files.get('image_file')
        
        # Validar que el título no esté vacío
        if not title:
            flash('El título es requerido', 'error')
            return render_template('admin/project_edit.html', project=project)
        
        try:
            # Procesar imagen si se subió un archivo
            if image_file and image_file.filename:
                try:
                    # Eliminar imagen anterior si existe y es local
                    old_image = project.image_url
                    if old_image and old_image.startswith('/static/uploads/'):
                        delete_uploaded_file(old_image)
                    
                    # Guardar nueva imagen
                    image_url = save_uploaded_file(image_file, 'uploads/projects')
                except ValueError as e:
                    flash(f'Error con la imagen: {str(e)}', 'error')
                    return render_template('admin/project_edit.html', project=project)
            
            # Solo regenerar slug si el título ha cambiado
            if title != project.title:
                base_slug = slugify(title)
                unique_slug = generate_unique_slug(base_slug, Project, exclude_id=project_id)
                project.slug = unique_slug
            
            project.title = title
            project.description = request.form.get('description')
            project.content = request.form.get('content')
            project.category = request.form.get('category')
            project.technologies = request.form.get('technologies')
            project.github_url = request.form.get('github_url')
            project.demo_url = request.form.get('demo_url')
            project.image_url = image_url
            project.published = 'published' in request.form
            project.featured = 'featured' in request.form
            project.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Proyecto actualizado correctamente', 'success')
            return redirect(url_for('admin.project_list'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el proyecto. Inténtalo de nuevo.', 'error')
            return render_template('admin/project_edit.html', project=project)
    
    return render_template('admin/project_edit.html', project=project)

@admin_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
@admin_required
def project_delete(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Proyecto eliminado correctamente', 'success')
    return redirect(url_for('admin.project_list'))

# Messages
@admin_bp.route('/messages')
@login_required
@admin_required
def contact_list():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    unread_count = ContactMessage.query.filter_by(read=False).count()
    total_count = len(messages)
    return render_template('admin/messages_list.html', 
                         messages=messages,
                         unread_count=unread_count,
                         total_count=total_count)

@admin_bp.route('/messages/<int:message_id>')
@login_required
@admin_required
def message_detail(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    return jsonify({
        'id': message.id,
        'name': message.name,
        'email': message.email,
        'subject': message.subject,
        'message': message.message,
        'read': message.read,
        'created_at': message.created_at.strftime('%d/%m/%Y %H:%M')
    })

@admin_bp.route('/messages/<int:message_id>/read', methods=['GET', 'POST'])
@login_required
@admin_required
def message_read(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.read = True
    db.session.commit()
    
    # Si es GET (desde el dashboard), redirigir de vuelta
    if request.method == 'GET':
        flash('Mensaje marcado como leído', 'success')
        return redirect(url_for('admin.dashboard'))
    
    # Si es POST (desde la lista de mensajes con AJAX), devolver JSON
    return jsonify({'success': True})

@admin_bp.route('/messages/<int:message_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def message_delete(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    return jsonify({'success': True})

# ====== MANEJO DE PAGOS ======

@admin_bp.route('/payments')
@login_required
@admin_required
def payments():
    """Lista todos los pagos pendientes de aprobación"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'pending')
    
    # Contar pagos por estado
    payments_count = {
        'pending': Payment.query.filter(Payment.status == PaymentStatus.PENDING_APPROVAL).count(),
        'approved': Payment.query.filter(Payment.status == PaymentStatus.APPROVED).count(),
        'rejected': Payment.query.filter(Payment.status == PaymentStatus.REJECTED).count()
    }
    
    # Filtrar pagos según el estado
    query = Payment.query.join(CourseEnrollment).join(Course)
    
    if status_filter == 'pending':
        query = query.filter(Payment.status == PaymentStatus.PENDING_APPROVAL)
    elif status_filter == 'approved':
        query = query.filter(Payment.status == PaymentStatus.APPROVED)
    elif status_filter == 'rejected':
        query = query.filter(Payment.status == PaymentStatus.REJECTED)
    
    payments = query.order_by(Payment.submitted_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/payments_new.html', 
                         payments=payments.items, 
                         payments_count=payments_count,
                         status_filter=status_filter)

@admin_bp.route('/payments/<int:payment_id>')
@login_required
@admin_required
def payment_detail(payment_id):
    """Ver detalles de un pago específico"""
    payment = Payment.query.get_or_404(payment_id)
    return render_template('admin/payment_detail.html', payment=payment)

@admin_bp.route('/payments/<int:payment_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_payment(payment_id):
    """Aprobar un pago"""
    payment = Payment.query.get_or_404(payment_id)
    admin_notes = request.form.get('admin_notes', '')
    
    # Log para debug
    current_app.logger.info(f"Aprobando pago ID: {payment_id}, Estado actual: {payment.status}")
    
    try:
        # Actualizar el estado del pago
        old_status = payment.status
        payment.status = PaymentStatus.APPROVED
        payment.processed_at = datetime.utcnow()
        payment.processed_by = current_user.id
        payment.admin_notes = admin_notes
        
        # Activar la inscripción
        enrollment = payment.enrollment
        old_enrollment_status = enrollment.status
        enrollment.status = EnrollmentStatus.ACTIVE
        enrollment.activated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log para confirmar cambios
        current_app.logger.info(f"Pago {payment_id} aprobado: {old_status} -> {payment.status}")
        current_app.logger.info(f"Inscripción {enrollment.id} activada: {old_enrollment_status} -> {enrollment.status}")
        
        flash(f'Pago aprobado correctamente. El usuario {enrollment.user.username} ahora tiene acceso al curso.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al aprobar el pago: {str(e)}', 'error')
    
    # Redirigir de vuelta a la lista de pagos para ver el cambio
    return redirect(url_for('admin.payments', status='approved'))

@admin_bp.route('/payments/<int:payment_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_payment(payment_id):
    """Rechazar un pago"""
    payment = Payment.query.get_or_404(payment_id)
    rejection_reason = request.form.get('rejection_reason', '')
    admin_notes = request.form.get('admin_notes', '')
    
    try:
        # Actualizar el estado del pago
        payment.status = PaymentStatus.REJECTED
        payment.processed_at = datetime.utcnow()
        payment.processed_by = current_user.id
        payment.rejection_reason = rejection_reason
        payment.admin_notes = admin_notes
        
        # Cancelar la inscripción
        enrollment = payment.enrollment
        enrollment.status = EnrollmentStatus.CANCELLED
        
        db.session.commit()
        
        flash(f'Pago rechazado. Se ha notificado al usuario {enrollment.user.username}.', 'warning')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al rechazar el pago: {str(e)}', 'error')
    
    # Redirigir de vuelta a la lista de pagos rechazados
    return redirect(url_for('admin.payments', status='rejected'))


# ========================================
# Gestión de Usuarios
# ========================================

@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """Lista de todos los usuarios"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_role = request.args.get('role', '')
    
    query = User.query
    
    # Filtrar por búsqueda
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    # Filtrar por rol
    if filter_role == 'admin':
        query = query.filter_by(is_admin=True)
    elif filter_role == 'user':
        query = query.filter_by(is_admin=False)
    
    # Ordenar y paginar
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    # Estadísticas
    total_users = User.query.count()
    total_admins = User.query.filter_by(is_admin=True).count()
    active_users = User.query.filter_by(is_active=True, is_admin=False).count()
    
    return render_template('admin/users_list.html',
                         users=users,
                         search=search,
                         filter_role=filter_role,
                         total_users=total_users,
                         total_admins=total_admins,
                         active_users=active_users)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Activar/desactivar usuario"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('No puedes desactivar a un administrador', 'error')
        return redirect(url_for('admin.users_list'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activado' if user.is_active else 'desactivado'
    flash(f'Usuario {user.username} {status} correctamente', 'success')
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_user_admin(user_id):
    """Hacer/quitar admin a un usuario"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('No puedes cambiar tu propio rol de admin', 'error')
        return redirect(url_for('admin.users_list'))
    
    user.is_admin = not user.is_admin
    user.role = 'admin' if user.is_admin else 'user'
    db.session.commit()
    
    status = 'ahora es administrador' if user.is_admin else 'ya no es administrador'
    flash(f'Usuario {user.username} {status}', 'success')
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Eliminar usuario"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('No puedes eliminar a un administrador', 'error')
        return redirect(url_for('admin.users_list'))
    
    if user.id == current_user.id:
        flash('No puedes eliminarte a ti mismo', 'error')
        return redirect(url_for('admin.users_list'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Usuario {username} eliminado correctamente', 'success')
    return redirect(url_for('admin.users_list'))


# ============================================
# ============================================
# Professional Alterations Monitor
# ============================================

@admin_bp.route('/alterations-monitor')
@login_required
@admin_required
def alterations_monitor():
    """Panel de monitoreo de Professional Alterations by Maria"""
    return render_template('admin/alterations_monitor.html')


# API Endpoints para Analytics/Gráficos
# ============================================

@admin_bp.route('/api/analytics/daily-views')
@login_required
@admin_required
def api_daily_views():
    """API endpoint para obtener datos de visitas diarias"""
    days = request.args.get('days', 30, type=int)
    days = min(days, 365)  # Máximo 1 año
    
    from app.utils.analytics import get_daily_views_data
    data = get_daily_views_data(days)
    
    return jsonify(data)


@admin_bp.route('/api/analytics/referrers')
@login_required
@admin_required
def api_referrers():
    """API endpoint para obtener estadísticas de fuentes de tráfico"""
    days = request.args.get('days', 30, type=int)
    days = min(days, 365)  # Máximo 1 año
    
    from app.utils.analytics import get_referrer_stats
    data = get_referrer_stats(days)
    
    return jsonify(data)
