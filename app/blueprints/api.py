from flask import Blueprint, jsonify, request
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.project import Project
from app.models.site_config import SiteConfig

api_bp = Blueprint('api', __name__)

@api_bp.route('/posts')
def get_posts():
    """Obtener todos los posts publicados"""
    posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).all()
    
    posts_data = []
    for post in posts:
        posts_data.append({
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'summary': post.summary,
            'created_at': post.created_at.isoformat(),
            'updated_at': post.updated_at.isoformat()
        })
    
    return jsonify({'posts': posts_data})

@api_bp.route('/posts/<slug>')
def get_post(slug):
    """Obtener un post específico por slug"""
    post = BlogPost.query.filter_by(slug=slug, published=True).first()
    
    if not post:
        return jsonify({'error': 'Post no encontrado'}), 404
    
    post_data = {
        'id': post.id,
        'title': post.title,
        'slug': post.slug,
        'content': post.content,
        'summary': post.summary,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat()
    }
    
    return jsonify(post_data)

@api_bp.route('/courses')
def get_courses():
    """Obtener todos los cursos publicados"""
    courses = Course.query.filter_by(published=True).all()
    
    courses_data = []
    for course in courses:
        courses_data.append({
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'short_description': course.short_description,
            'price': course.price,
            'duration': course.duration,
            'level': course.level,
            'featured': course.featured,
            'created_at': course.created_at.isoformat()
        })
    
    return jsonify({'courses': courses_data})

@api_bp.route('/courses/<slug>')
def get_course(slug):
    """Obtener un curso específico por slug"""
    course = Course.query.filter_by(slug=slug, published=True).first()
    
    if not course:
        return jsonify({'error': 'Curso no encontrado'}), 404
    
    course_data = {
        'id': course.id,
        'title': course.title,
        'slug': course.slug,
        'description': course.description,
        'short_description': course.short_description,
        'price': course.price,
        'duration': course.duration,
        'level': course.level,
        'featured': course.featured,
        'created_at': course.created_at.isoformat()
    }
    
    return jsonify(course_data)

@api_bp.route('/projects')
def get_projects():
    """Obtener todos los proyectos publicados"""
    category = request.args.get('category')
    
    query = Project.query.filter_by(published=True)
    if category:
        query = query.filter_by(category=category)
    
    projects = query.all()
    
    projects_data = []
    for project in projects:
        projects_data.append({
            'id': project.id,
            'title': project.title,
            'slug': project.slug,
            'short_description': project.short_description,
            'category': project.category,
            'technologies': project.technologies.split(',') if project.technologies else [],
            'github_url': project.github_url,
            'demo_url': project.demo_url,
            'featured': project.featured,
            'created_at': project.created_at.isoformat()
        })
    
    return jsonify({'projects': projects_data})

@api_bp.route('/projects/<slug>')
def get_project(slug):
    """Obtener un proyecto específico por slug"""
    project = Project.query.filter_by(slug=slug, published=True).first()
    
    if not project:
        return jsonify({'error': 'Proyecto no encontrado'}), 404
    
    project_data = {
        'id': project.id,
        'title': project.title,
        'slug': project.slug,
        'description': project.description,
        'short_description': project.short_description,
        'category': project.category,
        'technologies': project.technologies.split(',') if project.technologies else [],
        'github_url': project.github_url,
        'demo_url': project.demo_url,
        'featured': project.featured,
        'created_at': project.created_at.isoformat()
    }
    
    return jsonify(project_data)

@api_bp.route('/config')
def get_config():
    """Obtener configuración del sitio"""
    config = SiteConfig.query.first()
    
    if not config:
        return jsonify({'error': 'Configuración no encontrada'}), 404
    
    config_data = {
        'site_name': config.site_name,
        'site_description': config.site_description,
        'hero_title': config.hero_title,
        'hero_subtitle': config.hero_subtitle,
        'about_text': config.about_text,
        'contact_email': config.contact_email,
        'linkedin_url': config.linkedin_url,
        'github_url': config.github_url,
        'twitter_url': config.twitter_url
    }
    
    return jsonify(config_data)
