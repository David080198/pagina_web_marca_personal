from flask import Blueprint, session, redirect, request, url_for

language_bp = Blueprint('language', __name__)

@language_bp.route('/set-language/<lang>')
def set_language(lang):
    """Cambiar el idioma de la aplicación"""
    # Validar que el idioma sea válido
    if lang in ['en', 'es']:
        session['language'] = lang
        session.modified = True  # Forzar que la sesión se guarde
    
    # Obtener la URL de referencia
    referrer = request.referrer
    
    # Si hay referrer, usarlo; si no, ir al index
    if referrer:
        # Asegurar que el referrer use el mismo esquema
        return redirect(referrer)
    
    return redirect(url_for('main.index'))
