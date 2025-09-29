from flask import request, g
from app.models.analytics import PageView, VisitorStats
from app.extensions import db
from datetime import datetime, date
from sqlalchemy import func
import json
import re

def init_analytics(app):
    """Inicializar el sistema de analytics"""
    
    @app.before_request
    def track_page_view():
        """Trackear cada visita a páginas públicas"""
        # Solo trackear páginas públicas (no admin, API, etc.)
        if should_track_page():
            try:
                # Obtener información del visitante
                ip_address = get_client_ip()
                user_agent = request.headers.get('User-Agent', '')
                page = request.path
                referrer = request.headers.get('Referer', '')
                
                # Analizar user agent para obtener dispositivo y navegador
                device, browser = parse_user_agent(user_agent)
                
                # Obtener información del usuario si está autenticado
                from flask_login import current_user
                user_id = current_user.id if current_user.is_authenticated else None
                
                # Crear registro de vista de página
                page_view = PageView(
                    ip_address=ip_address,
                    user_agent=user_agent,
                    user_id=user_id,
                    page=page,
                    referrer=referrer,
                    device=device,
                    browser=browser
                )
                
                db.session.add(page_view)
                db.session.commit()
                
                # Actualizar estadísticas diarias
                update_daily_stats(page)
                
            except Exception as e:
                # En caso de error, continuar sin trackear
                db.session.rollback()
                app.logger.error(f"Error tracking page view: {e}")

def should_track_page():
    """Determinar si se debe trackear la página actual"""
    path = request.path
    
    # No trackear rutas de admin, API, archivos estáticos
    exclude_patterns = [
        r'^/admin',
        r'^/api',
        r'^/static',
        r'^/favicon',
        r'^/_',
        r'\.css$',
        r'\.js$',
        r'\.png$',
        r'\.jpg$',
        r'\.jpeg$',
        r'\.gif$',
        r'\.ico$'
    ]
    
    for pattern in exclude_patterns:
        if re.search(pattern, path):
            return False
    
    return True

def get_client_ip():
    """Obtener la IP real del cliente"""
    # Intentar obtener IP de headers de proxy
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def parse_user_agent(user_agent):
    """Analizar user agent para obtener dispositivo y navegador"""
    user_agent = user_agent.lower()
    
    # Detectar dispositivo
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        device = 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        device = 'tablet'
    else:
        device = 'desktop'
    
    # Detectar navegador
    if 'chrome' in user_agent and 'edge' not in user_agent:
        browser = 'chrome'
    elif 'firefox' in user_agent:
        browser = 'firefox'
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        browser = 'safari'
    elif 'edge' in user_agent:
        browser = 'edge'
    elif 'opera' in user_agent:
        browser = 'opera'
    else:
        browser = 'other'
    
    return device, browser

def update_daily_stats(page):
    """Actualizar estadísticas diarias"""
    today = date.today()
    
    # Obtener o crear registro de estadísticas para hoy
    stats = VisitorStats.query.filter_by(date=today).first()
    if not stats:
        stats = VisitorStats(
            date=today,
            unique_visitors=0,
            page_views=0,
            top_pages=json.dumps({})
        )
        db.session.add(stats)
    
    # Incrementar vistas de página
    stats.page_views += 1
    
    # Contar visitantes únicos (por IP en el día)
    unique_ips_today = db.session.query(func.count(func.distinct(PageView.ip_address))).filter(
        func.date(PageView.created_at) == today
    ).scalar()
    stats.unique_visitors = unique_ips_today
    
    # Actualizar páginas más visitadas
    top_pages = get_top_pages_today()
    stats.set_top_pages(top_pages)
    
    db.session.commit()

def get_top_pages_today():
    """Obtener las páginas más visitadas del día"""
    today = date.today()
    
    results = db.session.query(
        PageView.page,
        func.count(PageView.id).label('views')
    ).filter(
        func.date(PageView.created_at) == today
    ).group_by(PageView.page).order_by(
        func.count(PageView.id).desc()
    ).limit(10).all()
    
    return {page: views for page, views in results}

def get_analytics_summary():
    """Obtener resumen de analytics para el dashboard"""
    try:
        today = date.today()
        
        # Estadísticas de hoy
        today_stats = VisitorStats.query.filter_by(date=today).first()
        
        # Estadísticas totales
        total_views = db.session.query(func.count(PageView.id)).scalar() or 0
        total_unique_ips = db.session.query(func.count(func.distinct(PageView.ip_address))).scalar() or 0
        
        # Páginas más visitadas (últimos 7 días)
        from datetime import timedelta
        week_ago = today - timedelta(days=7)
        
        top_pages = db.session.query(
            PageView.page,
            func.count(PageView.id).label('views')
        ).filter(
            func.date(PageView.created_at) >= week_ago
        ).group_by(PageView.page).order_by(
            func.count(PageView.id).desc()
        ).limit(5).all()
        
        # Navegadores más usados (últimos 30 días)
        month_ago = today - timedelta(days=30)
        
        browsers = db.session.query(
            PageView.browser,
            func.count(PageView.id).label('count')
        ).filter(
            func.date(PageView.created_at) >= month_ago
        ).group_by(PageView.browser).order_by(
            func.count(PageView.id).desc()
        ).limit(5).all()
        
        # Dispositivos más usados (últimos 30 días)
        devices = db.session.query(
            PageView.device,
            func.count(PageView.id).label('count')
        ).filter(
            func.date(PageView.created_at) >= month_ago
        ).group_by(PageView.device).order_by(
            func.count(PageView.id).desc()
        ).all()
        
        return {
            'today_visitors': today_stats.unique_visitors if today_stats else 0,
            'today_views': today_stats.page_views if today_stats else 0,
            'total_views': total_views,
            'total_visitors': total_unique_ips,
            'top_pages': [(page, views) for page, views in top_pages],
            'browsers': [(browser, count) for browser, count in browsers],
            'devices': [(device, count) for device, count in devices]
        }
    
    except Exception as e:
        # En caso de error, retornar datos vacíos
        return {
            'today_visitors': 0,
            'today_views': 0,
            'total_views': 0,
            'total_visitors': 0,
            'top_pages': [],
            'browsers': [],
            'devices': []
        }
