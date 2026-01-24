from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.comment import Comment
from app.models.favorite import Favorite
from app.models.like import Like
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.project import Project
from app.extensions import db
from app.forms.user_forms import ProfileEditForm, ChangePasswordForm, CommentForm
from app.utils.file_upload import save_uploaded_file, delete_uploaded_file
from datetime import datetime
from sqlalchemy import or_, desc

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal del usuario"""
    # Estadísticas del usuario
    comments_count = Comment.query.filter_by(user_id=current_user.id).count()
    favorites_count = Favorite.query.filter_by(user_id=current_user.id).count()
    
    # Favoritos recientes
    recent_favorites = Favorite.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Favorite.created_at)).limit(5).all()
    
    # Comentarios recientes
    recent_comments = Comment.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Comment.created_at)).limit(5).all()
    
    return render_template('user/dashboard.html',
                         comments_count=comments_count,
                         favorites_count=favorites_count,
                         recent_favorites=recent_favorites,
                         recent_comments=recent_comments)

@user_bp.route('/profile')
@login_required
def profile():
    """Perfil público del usuario"""
    # Obtener comentarios recientes
    recent_comments = Comment.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Comment.created_at)).limit(5).all()
    
    # Obtener comentarios públicos
    public_comments = Comment.query.filter_by(user_id=current_user.id, is_approved=True)\
        .order_by(desc(Comment.created_at)).limit(10).all()
    
    # Obtener favoritos recientes
    recent_favorites = Favorite.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Favorite.created_at)).limit(6).all()
    
    # Obtener likes del usuario
    user_likes = Like.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Like.created_at)).limit(10).all()
    
    # Obtener inscripciones si existen
    try:
        from app.models.enrollment import CourseEnrollment
        recent_enrollments = CourseEnrollment.query.filter_by(user_id=current_user.id)\
            .order_by(desc(CourseEnrollment.enrolled_at)).limit(3).all()
    except ImportError:
        recent_enrollments = []
    
    return render_template('user/profile.html', 
                         user=current_user,
                         recent_comments=recent_comments,
                         public_comments=public_comments,
                         recent_favorites=recent_favorites,
                         user_likes=user_likes,
                         recent_enrollments=recent_enrollments)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Editar perfil del usuario"""
    form = ProfileEditForm(current_user.username, current_user.email, obj=current_user)
    
    if form.validate_on_submit():
        try:
            # Manejar avatar si se sube uno nuevo
            if form.avatar_file.data and form.avatar_file.data.filename:
                # Eliminar avatar anterior si existe y es local
                if current_user.avatar_url and current_user.avatar_url.startswith('/static/uploads/'):
                    delete_uploaded_file(current_user.avatar_url)
                
                # Guardar nuevo avatar
                avatar_url = save_uploaded_file(form.avatar_file.data, 'uploads/avatars')
                current_user.avatar_url = avatar_url
            
            # Actualizar campos del formulario
            form.populate_obj(current_user)
            current_user.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Perfil actualizado correctamente', 'success')
            return redirect(url_for('user.profile'))
            
        except ValueError as e:
            flash(f'Error con la imagen: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el perfil. Inténtalo de nuevo.', 'error')
    
    return render_template('user/edit_profile.html', form=form)

@user_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambiar contraseña del usuario"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            current_user.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Contraseña actualizada correctamente', 'success')
            return redirect(url_for('user.profile'))
        else:
            flash('Contraseña actual incorrecta', 'error')
    
    return render_template('user/change_password.html', form=form)

@user_bp.route('/favorites')
@login_required
def favorites():
    """Lista de favoritos del usuario"""
    page = request.args.get('page', 1, type=int)
    content_type = request.args.get('type', 'all')  # all, blog, course, project
    
    query = Favorite.query.filter_by(user_id=current_user.id)
    
    if content_type != 'all':
        query = query.filter_by(content_type=content_type)
    
    favorites = query.order_by(desc(Favorite.created_at))\
        .paginate(page=page, per_page=12, error_out=False)
    
    # Obtener objetos de contenido
    favorites_with_content = []
    for favorite in favorites.items:
        content_obj = favorite.get_content_object()
        if content_obj:
            favorites_with_content.append({
                'favorite': favorite,
                'content': content_obj
            })
    
    return render_template('user/favorites.html',
                         favorites=favorites,
                         favorites_with_content=favorites_with_content,
                         content_type=content_type)

@user_bp.route('/favorites/toggle', methods=['POST'])
@login_required
def toggle_favorite():
    """API para agregar/quitar favoritos"""
    data = request.get_json()
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    
    if not content_type or not content_id:
        return jsonify({'error': 'Datos inválidos'}), 400
    
    try:
        is_favorited = Favorite.toggle_favorite(current_user.id, content_type, content_id)
        return jsonify({
            'success': True,
            'is_favorited': is_favorited,
            'message': 'Agregado a favoritos' if is_favorited else 'Eliminado de favoritos'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/comments')
@login_required
def comments():
    """Lista de comentarios del usuario"""
    page = request.args.get('page', 1, type=int)
    
    comments = Comment.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Comment.created_at))\
        .paginate(page=page, per_page=10, error_out=False)
    
    # Obtener objetos de contenido para cada comentario
    comments_with_content = []
    for comment in comments.items:
        content_obj = comment.get_content_object()
        if content_obj:
            comments_with_content.append({
                'comment': comment,
                'content': content_obj
            })
    
    return render_template('user/comments.html',
                         comments=comments,
                         comments_with_content=comments_with_content)

@user_bp.route('/comment/add', methods=['POST'])
@login_required
def add_comment():
    """API para agregar comentarios"""
    if not current_user.can_comment():
        return jsonify({'error': 'No tienes permisos para comentar'}), 403
    
    data = request.get_json()
    content = data.get('content', '').strip()
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    parent_id = data.get('parent_id')
    
    if not content or not content_type or not content_id:
        return jsonify({'error': 'Datos inválidos'}), 400
    
    if len(content) < 5 or len(content) > 1000:
        return jsonify({'error': 'El comentario debe tener entre 5 y 1000 caracteres'}), 400
    
    try:
        comment = Comment(
            content=content,
            user_id=current_user.id,
            content_type=content_type,
            content_id=content_id,
            parent_id=parent_id if parent_id else None
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment': comment.to_dict(),
            'message': 'Comentario agregado correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/comment/<int:comment_id>/edit', methods=['PUT'])
@login_required
def edit_comment(comment_id):
    """API para editar comentarios"""
    comment = Comment.query.get_or_404(comment_id)
    
    if not comment.can_edit(current_user):
        return jsonify({'error': 'No tienes permisos para editar este comentario'}), 403
    
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content or len(content) < 5 or len(content) > 1000:
        return jsonify({'error': 'El comentario debe tener entre 5 y 1000 caracteres'}), 400
    
    try:
        comment.content = content
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment': comment.to_dict(),
            'message': 'Comentario actualizado correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/comment/<int:comment_id>/delete', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """API para eliminar comentarios"""
    comment = Comment.query.get_or_404(comment_id)
    
    if not comment.can_delete(current_user):
        return jsonify({'error': 'No tienes permisos para eliminar este comentario'}), 403
    
    try:
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Comentario eliminado correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/favorite/<int:favorite_id>/remove', methods=['DELETE'])
@login_required
def remove_favorite(favorite_id):
    """API para eliminar favoritos"""
    favorite = Favorite.query.get_or_404(favorite_id)
    
    if favorite.user_id != current_user.id:
        return jsonify({'error': 'No tienes permisos para eliminar este favorito'}), 403
    
    try:
        db.session.delete(favorite)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Favorito eliminado correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/public/<username>')
def public_profile(username):
    """Perfil público de cualquier usuario"""
    user = User.query.filter_by(username=username).first_or_404()
    
    if not user.is_active:
        flash('Este perfil no está disponible', 'error')
        return redirect(url_for('main.index'))
    
    # Comentarios públicos recientes
    recent_comments = Comment.query.filter_by(user_id=user.id, is_approved=True)\
        .order_by(desc(Comment.created_at)).limit(5).all()
    
    return render_template('user/public_profile.html', 
                         user=user, 
                         recent_comments=recent_comments)
