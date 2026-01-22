"""
Servicio de Seguridad - CODEXSOTO
=================================
Funciones de seguridad y protección
"""

import hashlib
import hmac
import secrets
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import request, abort, current_app, g
from flask_login import current_user


class SecurityService:
    """Servicio para funciones de seguridad"""
    
    # Almacén simple de rate limiting (en producción usar Redis)
    _rate_limit_store = {}
    
    @staticmethod
    def generate_token(length=32):
        """Genera un token seguro"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_verification_token():
        """Genera un token de verificación"""
        return secrets.token_hex(16)
    
    @staticmethod
    def generate_password_reset_token():
        """Genera un token para reset de contraseña"""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_token(token):
        """Hashea un token para almacenamiento seguro"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def verify_token(token, hashed_token):
        """Verifica un token contra su hash"""
        return hmac.compare_digest(
            SecurityService.hash_token(token),
            hashed_token
        )
    
    @staticmethod
    def validate_password(password):
        """
        Valida que una contraseña cumpla requisitos de seguridad
        
        Returns:
            tuple: (is_valid, message)
        """
        errors = []
        
        if len(password) < 8:
            errors.append('Mínimo 8 caracteres')
        
        if len(password) > 128:
            errors.append('Máximo 128 caracteres')
        
        if not re.search(r'[A-Z]', password):
            errors.append('Al menos una letra mayúscula')
        
        if not re.search(r'[a-z]', password):
            errors.append('Al menos una letra minúscula')
        
        if not re.search(r'\d', password):
            errors.append('Al menos un número')
        
        # Opcional: carácter especial
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        #     errors.append('Al menos un carácter especial')
        
        if errors:
            return False, ', '.join(errors)
        
        return True, 'Contraseña válida'
    
    @staticmethod
    def validate_email(email):
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitiza un nombre de archivo"""
        # Eliminar caracteres peligrosos
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Eliminar caracteres no ASCII
        filename = filename.encode('ascii', 'ignore').decode()
        # Limitar longitud
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:200-len(ext)-1] + '.' + ext if ext else name[:200]
        
        return filename.strip()
    
    @staticmethod
    def is_safe_url(target):
        """Verifica que una URL sea segura para redirección"""
        from urllib.parse import urlparse, urljoin
        from flask import request
        
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        
        return test_url.scheme in ('http', 'https') and \
               ref_url.netloc == test_url.netloc
    
    @staticmethod
    def get_client_ip():
        """Obtiene la IP real del cliente"""
        # Considerar proxies
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
    
    @staticmethod
    def check_rate_limit(key, max_requests=100, window_seconds=3600):
        """
        Verifica si se ha excedido el límite de tasa
        
        Args:
            key: Identificador único (ej: IP, user_id)
            max_requests: Máximo de solicitudes permitidas
            window_seconds: Ventana de tiempo en segundos
            
        Returns:
            tuple: (is_allowed, remaining_requests, reset_time)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Limpiar entradas antiguas
        if key in SecurityService._rate_limit_store:
            SecurityService._rate_limit_store[key] = [
                timestamp for timestamp in SecurityService._rate_limit_store[key]
                if timestamp > window_start
            ]
        else:
            SecurityService._rate_limit_store[key] = []
        
        requests = len(SecurityService._rate_limit_store[key])
        
        if requests >= max_requests:
            # Calcular tiempo de reset
            oldest = min(SecurityService._rate_limit_store[key])
            reset_time = oldest + timedelta(seconds=window_seconds)
            return False, 0, reset_time
        
        # Registrar nueva solicitud
        SecurityService._rate_limit_store[key].append(now)
        remaining = max_requests - requests - 1
        
        return True, remaining, now + timedelta(seconds=window_seconds)
    
    @staticmethod
    def rate_limit(max_requests=100, window_seconds=3600, key_func=None):
        """
        Decorador para rate limiting
        
        Usage:
            @SecurityService.rate_limit(max_requests=5, window_seconds=60)
            def my_view():
                pass
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if key_func:
                    key = key_func()
                elif current_user and current_user.is_authenticated:
                    key = f'user_{current_user.id}'
                else:
                    key = f'ip_{SecurityService.get_client_ip()}'
                
                allowed, remaining, reset_time = SecurityService.check_rate_limit(
                    key, max_requests, window_seconds
                )
                
                if not allowed:
                    abort(429, description='Demasiadas solicitudes. Intenta más tarde.')
                
                # Añadir headers de rate limit
                g.rate_limit_remaining = remaining
                g.rate_limit_reset = reset_time
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def log_security_event(event_type, details=None, user_id=None):
        """Registra un evento de seguridad"""
        from app.models.analytics import Analytics
        from app.extensions import db
        
        try:
            analytics = Analytics(
                page_url=f'/security/{event_type}',
                event_type='security_event',
                user_id=user_id or (current_user.id if current_user and current_user.is_authenticated else None),
                ip_address=SecurityService.get_client_ip(),
                user_agent=request.headers.get('User-Agent', '')[:500] if request else None,
                referrer=str(details)[:500] if details else None
            )
            db.session.add(analytics)
            db.session.commit()
        except Exception:
            # No fallar si el logging falla
            pass
    
    @staticmethod
    def detect_suspicious_activity(user_id=None):
        """Detecta actividad sospechosa"""
        ip = SecurityService.get_client_ip()
        
        # Verificar múltiples intentos de login fallidos
        key = f'login_failed_{ip}'
        if key in SecurityService._rate_limit_store:
            failed_attempts = len(SecurityService._rate_limit_store[key])
            if failed_attempts >= 5:
                SecurityService.log_security_event(
                    'suspicious_login_attempts',
                    {'ip': ip, 'attempts': failed_attempts},
                    user_id
                )
                return True
        
        return False
    
    @staticmethod
    def record_failed_login(identifier):
        """Registra un intento de login fallido"""
        ip = SecurityService.get_client_ip()
        key = f'login_failed_{ip}'
        
        now = datetime.utcnow()
        window_start = now - timedelta(hours=1)
        
        if key not in SecurityService._rate_limit_store:
            SecurityService._rate_limit_store[key] = []
        
        # Limpiar antiguos
        SecurityService._rate_limit_store[key] = [
            t for t in SecurityService._rate_limit_store[key]
            if t > window_start
        ]
        
        SecurityService._rate_limit_store[key].append(now)
        
        SecurityService.log_security_event(
            'failed_login',
            {'identifier': identifier, 'ip': ip}
        )
    
    @staticmethod
    def clear_failed_logins(identifier=None):
        """Limpia los intentos de login fallidos después de login exitoso"""
        ip = SecurityService.get_client_ip()
        key = f'login_failed_{ip}'
        
        if key in SecurityService._rate_limit_store:
            del SecurityService._rate_limit_store[key]
    
    @staticmethod
    def generate_csrf_token():
        """Genera un token CSRF"""
        from flask import session
        
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(32)
        
        return session['_csrf_token']
    
    @staticmethod
    def validate_csrf_token(token):
        """Valida un token CSRF"""
        from flask import session
        
        session_token = session.get('_csrf_token')
        if not session_token or not token:
            return False
        
        return hmac.compare_digest(session_token, token)
    
    @staticmethod
    def require_https():
        """Decorador para requerir HTTPS"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not request.is_secure and not current_app.debug:
                    abort(403, description='Se requiere conexión segura (HTTPS)')
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def admin_required(f):
        """Decorador para requerir rol de administrador"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401, description='Autenticación requerida')
            if not current_user.is_admin:
                SecurityService.log_security_event(
                    'unauthorized_admin_access',
                    {'path': request.path},
                    current_user.id
                )
                abort(403, description='Acceso denegado')
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def premium_required(f):
        """Decorador para requerir suscripción premium"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401, description='Autenticación requerida')
            
            from .subscription_service import SubscriptionService
            
            if not SubscriptionService.has_access_to_premium_content(current_user):
                abort(403, description='Se requiere suscripción premium')
            
            return f(*args, **kwargs)
        return decorated_function


# Funciones auxiliares para uso en templates
def csrf_token():
    """Función helper para templates"""
    return SecurityService.generate_csrf_token()


def get_password_requirements():
    """Retorna los requisitos de contraseña para mostrar en UI"""
    return [
        'Mínimo 8 caracteres',
        'Al menos una letra mayúscula',
        'Al menos una letra minúscula',
        'Al menos un número'
    ]
