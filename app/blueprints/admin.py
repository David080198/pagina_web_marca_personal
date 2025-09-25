from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.project import Project
from app.models.site_config import SiteConfig
from app.models.contact import ContactMessage
from app.extensions import db
import os
from werkzeug.utils import secure_filename
import json
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

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
    
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_posts=total_posts,
                         published_posts=published_posts,
                         total_courses=total_courses,
                         total_projects=total_projects,
                         unread_messages=unread_messages,
                         recent_messages=recent_messages)

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

@admin_bp.route('/blog/new', methods=['GET', 'POST'])
@login_required
@admin_required
def blog_new():
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        summary = request.form.get('summary')
        published = bool(request.form.get('published'))
        
        post = BlogPost(
            title=title,
            slug=slug,
            content=content,
            summary=summary,
            published=published
        )
        
        db.session.add(post)
        db.session.commit()
        flash('Post creado correctamente', 'success')
        return redirect(url_for('admin.blog_list'))
    
    return render_template('admin/blog_edit.html', post=None)

@admin_bp.route('/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def blog_edit(post_id):
    post = BlogPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.slug = request.form.get('slug')
        post.content = request.form.get('content')
        post.summary = request.form.get('summary')
        post.published = bool(request.form.get('published'))
        post.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Post actualizado correctamente', 'success')
        return redirect(url_for('admin.blog_list'))
    
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
        slug = request.form.get('slug')
        description = request.form.get('description')
        short_description = request.form.get('short_description')
        price = float(request.form.get('price', 0))
        duration = request.form.get('duration')
        level = request.form.get('level')
        published = bool(request.form.get('published'))
        featured = bool(request.form.get('featured'))
        
        course = Course(
            title=title,
            slug=slug,
            description=description,
            short_description=short_description,
            price=price,
            duration=duration,
            level=level,
            published=published,
            featured=featured
        )
        
        db.session.add(course)
        db.session.commit()
        flash('Curso creado correctamente', 'success')
        return redirect(url_for('admin.course_list'))
    
    return render_template('admin/course_edit.html', course=None)

@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def course_edit(course_id):
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.slug = request.form.get('slug')
        course.description = request.form.get('description')
        course.short_description = request.form.get('short_description')
        course.price = float(request.form.get('price', 0))
        course.duration = request.form.get('duration')
        course.level = request.form.get('level')
        course.published = bool(request.form.get('published'))
        course.featured = bool(request.form.get('featured'))
        course.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Curso actualizado correctamente', 'success')
        return redirect(url_for('admin.course_list'))
    
    return render_template('admin/course_edit.html', course=course)

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
        slug = request.form.get('slug')
        description = request.form.get('description')
        short_description = request.form.get('short_description')
        category = request.form.get('category')
        technologies = request.form.get('technologies')
        github_url = request.form.get('github_url')
        demo_url = request.form.get('demo_url')
        published = bool(request.form.get('published'))
        featured = bool(request.form.get('featured'))
        
        project = Project(
            title=title,
            slug=slug,
            description=description,
            short_description=short_description,
            category=category,
            technologies=technologies,
            github_url=github_url,
            demo_url=demo_url,
            published=published,
            featured=featured
        )
        
        db.session.add(project)
        db.session.commit()
        flash('Proyecto creado correctamente', 'success')
        return redirect(url_for('admin.project_list'))
    
    return render_template('admin/project_edit.html', project=None)

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

@admin_bp.route('/messages/<int:message_id>/read', methods=['POST'])
@login_required
@admin_required
def message_read(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.read = True
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/messages/<int:message_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def message_delete(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    return jsonify({'success': True})
