"""
Blueprint de Artículos Técnicos - CODEXSOTO
=============================================
Rutas para ver, filtrar y gestionar artículos técnicos
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.article import Article, ArticleCategory, ArticleLike, ArticleDifficulty
from functools import wraps

articles_bp = Blueprint('articles', __name__)


def premium_required(f):
    """Decorador para contenido premium"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        article_id = kwargs.get('article_id')
        slug = kwargs.get('slug')
        
        if slug:
            article = Article.query.filter_by(slug=slug, published=True).first_or_404()
        elif article_id:
            article = Article.query.get_or_404(article_id)
        else:
            article = None
        
        if article and article.is_premium:
            if not current_user.is_authenticated:
                flash('Este artículo es exclusivo para suscriptores premium. Inicia sesión o suscríbete.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            if not article.can_access(current_user):
                flash('Este artículo es exclusivo para suscriptores premium.', 'warning')
                return redirect(url_for('subscriptions.plans'))
        
        return f(*args, **kwargs)
    return decorated_function


@articles_bp.route('/')
def index():
    """Lista de artículos con filtros"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Filtros
    category_slug = request.args.get('category')
    difficulty = request.args.get('difficulty')
    search = request.args.get('q')
    sort = request.args.get('sort', 'recent')  # recent, popular, oldest
    
    # Query base
    query = Article.query.filter_by(published=True)
    
    # Aplicar filtros
    if category_slug:
        category = ArticleCategory.query.filter_by(slug=category_slug).first()
        if category:
            query = query.filter_by(category_id=category.id)
    
    if difficulty:
        try:
            diff_enum = ArticleDifficulty(difficulty)
            query = query.filter_by(difficulty=diff_enum)
        except ValueError:
            pass
    
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Article.title.ilike(search_term),
                Article.summary.ilike(search_term),
                Article.tags.ilike(search_term)
            )
        )
    
    # Ordenamiento
    if sort == 'popular':
        query = query.order_by(Article.views_count.desc())
    elif sort == 'oldest':
        query = query.order_by(Article.published_at.asc())
    else:  # recent
        query = query.order_by(Article.published_at.desc())
    
    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    articles = pagination.items
    
    # Categorías para sidebar
    categories = ArticleCategory.query.filter_by(is_active=True).order_by(ArticleCategory.order).all()
    
    # Artículos destacados
    featured = Article.get_featured(limit=3)
    
    return render_template('articles/index.html',
                          articles=articles,
                          pagination=pagination,
                          categories=categories,
                          featured=featured,
                          current_category=category_slug,
                          current_difficulty=difficulty,
                          current_sort=sort,
                          search_query=search)


@articles_bp.route('/<slug>')
@premium_required
def detail(slug):
    """Vista detallada de un artículo"""
    article = Article.query.filter_by(slug=slug, published=True).first_or_404()
    
    # Incrementar vistas
    article.increment_views()
    
    # Verificar si el usuario tiene like
    user_has_liked = False
    if current_user.is_authenticated:
        user_has_liked = ArticleLike.query.filter_by(
            article_id=article.id,
            user_id=current_user.id
        ).first() is not None
    
    # Artículos relacionados
    related = Article.query.filter(
        Article.published == True,
        Article.id != article.id,
        Article.category_id == article.category_id
    ).order_by(Article.published_at.desc()).limit(3).all()
    
    # Si no hay relacionados por categoría, buscar por tags
    if not related and article.tags:
        tags = article.get_tags_list()[:2]
        for tag in tags:
            related = Article.query.filter(
                Article.published == True,
                Article.id != article.id,
                Article.tags.ilike(f'%{tag}%')
            ).limit(3).all()
            if related:
                break
    
    return render_template('articles/detail.html',
                          article=article,
                          related=related,
                          user_has_liked=user_has_liked)


@articles_bp.route('/category/<slug>')
def by_category(slug):
    """Artículos por categoría"""
    category = ArticleCategory.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    
    pagination = Article.query.filter_by(
        published=True,
        category_id=category.id
    ).order_by(Article.published_at.desc()).paginate(page=page, per_page=12, error_out=False)
    
    categories = ArticleCategory.query.filter_by(is_active=True).order_by(ArticleCategory.order).all()
    
    return render_template('articles/category.html',
                          category=category,
                          articles=pagination.items,
                          pagination=pagination,
                          categories=categories)


@articles_bp.route('/<int:article_id>/like', methods=['POST'])
@login_required
def toggle_like(article_id):
    """Toggle like de artículo"""
    article = Article.query.get_or_404(article_id)
    
    existing_like = ArticleLike.query.filter_by(
        article_id=article_id,
        user_id=current_user.id
    ).first()
    
    if existing_like:
        # Quitar like
        db.session.delete(existing_like)
        article.likes_count = max(0, article.likes_count - 1)
        liked = False
    else:
        # Agregar like
        like = ArticleLike(article_id=article_id, user_id=current_user.id)
        db.session.add(like)
        article.likes_count += 1
        liked = True
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'liked': liked,
            'likes_count': article.likes_count
        })
    
    return redirect(url_for('articles.detail', slug=article.slug))


@articles_bp.route('/search')
def search():
    """Búsqueda de artículos"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return redirect(url_for('articles.index'))
    
    articles = Article.search(query, limit=50)
    categories = ArticleCategory.query.filter_by(is_active=True).all()
    
    return render_template('articles/search.html',
                          articles=articles,
                          search_query=query,
                          categories=categories,
                          results_count=len(articles))


# ========== API Endpoints ==========

@articles_bp.route('/api/articles')
def api_list():
    """API: Lista de artículos"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    
    query = Article.query.filter_by(published=True)
    
    if category:
        cat = ArticleCategory.query.filter_by(slug=category).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
    
    if difficulty:
        try:
            query = query.filter_by(difficulty=ArticleDifficulty(difficulty))
        except ValueError:
            pass
    
    pagination = query.order_by(Article.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'articles': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@articles_bp.route('/api/articles/<slug>')
def api_detail(slug):
    """API: Detalle de artículo"""
    article = Article.query.filter_by(slug=slug, published=True).first()
    
    if not article:
        return jsonify({'error': 'Artículo no encontrado'}), 404
    
    # Para contenido premium, verificar acceso
    include_content = True
    if article.is_premium:
        if not current_user.is_authenticated or not article.can_access(current_user):
            include_content = False
    
    return jsonify(article.to_dict(include_content=include_content))


@articles_bp.route('/api/categories')
def api_categories():
    """API: Lista de categorías"""
    categories = ArticleCategory.query.filter_by(is_active=True).order_by(ArticleCategory.order).all()
    
    return jsonify({
        'categories': [
            {
                'id': c.id,
                'name': c.name,
                'slug': c.slug,
                'description': c.description,
                'icon': c.icon,
                'color': c.color,
                'article_count': c.article_count()
            }
            for c in categories
        ]
    })


@articles_bp.route('/api/popular')
def api_popular():
    """API: Artículos más populares"""
    limit = min(request.args.get('limit', 5, type=int), 20)
    articles = Article.get_popular(limit=limit)
    
    return jsonify({
        'articles': [a.to_dict() for a in articles]
    })


@articles_bp.route('/api/featured')
def api_featured():
    """API: Artículos destacados"""
    limit = min(request.args.get('limit', 3, type=int), 10)
    articles = Article.get_featured(limit=limit)
    
    return jsonify({
        'articles': [a.to_dict() for a in articles]
    })
