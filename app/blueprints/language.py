from flask import Blueprint, session, redirect, request, url_for

language_bp = Blueprint('language', __name__)

@language_bp.route('/set-language/<lang>')
def set_language(lang):
    """Cambiar el idioma de la aplicación"""
    # Validar que el idioma sea válido
    if lang in ['en', 'es']:
        session['language'] = lang
    
    # Redirigir a la página anterior o a la página principal
    return redirect(request.referrer or url_for('main.index'))
