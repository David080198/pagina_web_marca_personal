from flask import Blueprint, jsonify, request, current_app
from flask_wtf.csrf import CSRFProtect
from flask_login import login_required, current_user
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.project import Project
from app.models.site_config import SiteConfig
from app.models.like import Like
from app.models.comment import Comment
from app.models.favorite import Favorite
from app.extensions import db
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

api_bp = Blueprint('api', __name__)

# Exentar todo el blueprint de CSRF (es una API)
@api_bp.before_request
def csrf_exempt():
    pass  # Flask-WTF CSRFProtect ya maneja esto con decoradores

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


# ============================================
# Upload de imágenes para blogs (Markdown editor)
# ============================================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route('/upload-blog-image', methods=['POST'])
@login_required
def upload_blog_image():
    """Subir imagen para insertar en el contenido del blog (Markdown)"""
    
    # Verificar que el usuario sea admin
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No se envió ninguna imagen'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Tipo de archivo no permitido. Usa JPG, PNG, GIF o WebP'}), 400
    
    # Verificar tamaño
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'success': False, 'error': 'La imagen supera el tamaño máximo de 5MB'}), 400
    
    try:
        # Generar nombre único para el archivo
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
        
        # Crear directorio si no existe
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'blog')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Guardar archivo
        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)
        
        # Generar URL de la imagen
        image_url = f"/static/uploads/blog/{unique_filename}"
        
        return jsonify({
            'success': True,
            'url': image_url,
            'filename': unique_filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===============================================
# API de Likes
# ===============================================

@api_bp.route('/like/<content_type>/<int:content_id>', methods=['POST'])
@login_required
def toggle_like(content_type, content_id):
    """Toggle like en un contenido (blog, course, project)"""
    if content_type not in ['blog', 'course', 'project']:
        return jsonify({'success': False, 'error': 'Tipo de contenido inválido'}), 400
    
    # Verificar que el contenido existe
    if content_type == 'blog':
        content = BlogPost.query.get(content_id)
    elif content_type == 'course':
        content = Course.query.get(content_id)
    elif content_type == 'project':
        content = Project.query.get(content_id)
    
    if not content:
        return jsonify({'success': False, 'error': 'Contenido no encontrado'}), 404
    
    # Toggle like
    liked = Like.toggle_like(current_user.id, content_type, content_id)
    likes_count = Like.get_likes_count(content_type, content_id)
    
    return jsonify({
        'success': True,
        'liked': liked,
        'likes_count': likes_count
    })


@api_bp.route('/like/<content_type>/<int:content_id>', methods=['GET'])
def get_like_status(content_type, content_id):
    """Obtener estado del like y contador"""
    if content_type not in ['blog', 'course', 'project']:
        return jsonify({'success': False, 'error': 'Tipo de contenido inválido'}), 400
    
    likes_count = Like.get_likes_count(content_type, content_id)
    liked = False
    
    if current_user.is_authenticated:
        liked = Like.user_has_liked(current_user.id, content_type, content_id)
    
    return jsonify({
        'success': True,
        'liked': liked,
        'likes_count': likes_count
    })


# ===============================================
# API de Favoritos
# ===============================================

@api_bp.route('/favorite/<content_type>/<int:content_id>', methods=['POST'])
@login_required
def toggle_favorite(content_type, content_id):
    """Toggle favorito en un contenido (blog, course, project)"""
    if content_type not in ['blog', 'course', 'project']:
        return jsonify({'success': False, 'error': 'Tipo de contenido inválido'}), 400
    
    # Verificar que el contenido existe
    if content_type == 'blog':
        content = BlogPost.query.get(content_id)
    elif content_type == 'course':
        content = Course.query.get(content_id)
    elif content_type == 'project':
        content = Project.query.get(content_id)
    
    if not content:
        return jsonify({'success': False, 'error': 'Contenido no encontrado'}), 404
    
    # Toggle favorite
    favorited = Favorite.toggle_favorite(current_user.id, content_type, content_id)
    
    return jsonify({
        'success': True,
        'favorited': favorited
    })


@api_bp.route('/favorite/<content_type>/<int:content_id>', methods=['GET'])
def get_favorite_status(content_type, content_id):
    """Obtener estado del favorito"""
    if content_type not in ['blog', 'course', 'project']:
        return jsonify({'success': False, 'error': 'Tipo de contenido inválido'}), 400
    
    favorited = False
    
    if current_user.is_authenticated:
        favorited = Favorite.is_favorited_by_user(current_user.id, content_type, content_id)
    
    return jsonify({
        'success': True,
        'favorited': favorited
    })


# ===============================================
# API de Comentarios
# ===============================================

@api_bp.route('/comments/<content_type>/<int:content_id>', methods=['GET'])
def get_comments(content_type, content_id):
    """Obtener comentarios de un contenido"""
    if content_type not in ['blog', 'course', 'project']:
        return jsonify({'success': False, 'error': 'Tipo de contenido inválido'}), 400
    
    comments = Comment.query.filter_by(
        content_type=content_type,
        content_id=content_id,
        is_approved=True,
        parent_id=None  # Solo comentarios principales
    ).order_by(Comment.created_at.desc()).all()
    
    comments_data = []
    for comment in comments:
        replies = Comment.query.filter_by(
            parent_id=comment.id,
            is_approved=True
        ).order_by(Comment.created_at.asc()).all()
        
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'user': {
                'id': comment.author.id,
                'username': comment.author.username,
                'display_name': comment.author.display_name,
                'avatar_url': comment.author.get_avatar_url(50)
            },
            'created_at': comment.created_at.isoformat(),
            'is_pinned': comment.is_pinned,
            'can_edit': current_user.is_authenticated and comment.can_edit(current_user),
            'can_delete': current_user.is_authenticated and comment.can_delete(current_user),
            'replies': [{
                'id': reply.id,
                'content': reply.content,
                'user': {
                    'id': reply.author.id,
                    'username': reply.author.username,
                    'display_name': reply.author.display_name,
                    'avatar_url': reply.author.get_avatar_url(40)
                },
                'created_at': reply.created_at.isoformat(),
                'can_edit': current_user.is_authenticated and reply.can_edit(current_user),
                'can_delete': current_user.is_authenticated and reply.can_delete(current_user)
            } for reply in replies]
        })
    
    return jsonify({
        'success': True,
        'comments': comments_data,
        'count': len(comments_data)
    })


@api_bp.route('/comments/<content_type>/<int:content_id>', methods=['POST'])
@login_required
def add_comment(content_type, content_id):
    """Agregar un comentario"""
    if content_type not in ['blog', 'course', 'project']:
        return jsonify({'success': False, 'error': 'Tipo de contenido inválido'}), 400
    
    data = request.get_json()
    if not data or not data.get('content'):
        return jsonify({'success': False, 'error': 'El contenido del comentario es requerido'}), 400
    
    content_text = data['content'].strip()
    if len(content_text) < 3:
        return jsonify({'success': False, 'error': 'El comentario es muy corto'}), 400
    if len(content_text) > 2000:
        return jsonify({'success': False, 'error': 'El comentario es muy largo (máximo 2000 caracteres)'}), 400
    
    parent_id = data.get('parent_id')
    
    # Verificar que el comentario padre existe si se especifica
    if parent_id:
        parent = Comment.query.get(parent_id)
        if not parent:
            return jsonify({'success': False, 'error': 'Comentario padre no encontrado'}), 404
    
    try:
        comment = Comment(
            content=content_text,
            user_id=current_user.id,
            content_type=content_type,
            content_id=content_id,
            parent_id=parent_id,
            is_approved=True  # Auto aprobar por ahora
        )
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'display_name': current_user.display_name,
                    'avatar_url': current_user.get_avatar_url(50)
                },
                'created_at': comment.created_at.isoformat()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@login_required
def edit_comment(comment_id):
    """Editar un comentario"""
    comment = Comment.query.get_or_404(comment_id)
    
    if not comment.can_edit(current_user):
        return jsonify({'success': False, 'error': 'No tienes permiso para editar este comentario'}), 403
    
    data = request.get_json()
    if not data or not data.get('content'):
        return jsonify({'success': False, 'error': 'El contenido es requerido'}), 400
    
    content_text = data['content'].strip()
    if len(content_text) < 3 or len(content_text) > 2000:
        return jsonify({'success': False, 'error': 'Longitud de comentario inválida'}), 400
    
    try:
        comment.content = content_text
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'updated_at': comment.updated_at.isoformat()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """Eliminar un comentario"""
    comment = Comment.query.get_or_404(comment_id)
    
    if not comment.can_delete(current_user):
        return jsonify({'success': False, 'error': 'No tienes permiso para eliminar este comentario'}), 403
    
    try:
        # Eliminar respuestas también
        Comment.query.filter_by(parent_id=comment.id).delete()
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
