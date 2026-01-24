from flask import Flask, request, session, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_locale():
    """Seleccionar el idioma del usuario"""
    # 1. Primero verificar si el usuario ha seleccionado un idioma manualmente
    if 'language' in session:
        return session['language']
    
    # 2. Verificar si hay un parámetro en la URL
    lang = request.args.get('lang')
    if lang in ['en', 'es']:
        return lang
    
    # 3. Usar el idioma del navegador
    return request.accept_languages.best_match(['en', 'es']) or 'en'

def create_app():
    # Configurar rutas de templates y static
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Aplicar ProxyFix PRIMERO para que Flask reconozca HTTPS detrás de proxy (Traefik/nginx)
    # Esto debe estar antes de cualquier configuración de sesión
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Importar extensiones localmente para evitar imports circulares
    from app.extensions import db, login_manager, migrate, mail, csrf, babel
    
    # Detectar si estamos en producción
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    # Configuración
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///codexsoto.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # Configuración de sesiones para producción (detrás de proxy HTTPS)
    app.config['SESSION_COOKIE_SECURE'] = is_production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PREFERRED_URL_SCHEME'] = 'https' if is_production else 'http'
    
    # Configuración de Babel (multi-idioma)
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'translations')
    app.config['LANGUAGES'] = {
        'en': 'English',
        'es': 'Español'
    }
    
    # Configuración de email
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)  # Habilitado para seguridad
    babel.init_app(app, locale_selector=get_locale)
    
    # Exentar rutas de API y webhooks de CSRF
    from flask_wtf.csrf import CSRFProtect
    
    # Inicializar analytics
    from app.utils.analytics import init_analytics
    init_analytics(app)
    
    # Forzar HTTPS en producción
    @app.before_request
    def force_https():
        # Solo en producción (cuando hay un proxy delante)
        if request.headers.get('X-Forwarded-Proto') == 'http':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
    
    # Agregar csrf_token a todos los templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # Configuración de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Registrar Blueprints
    print("=== REGISTRANDO BLUEPRINTS ===")
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.password_reset import password_reset_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.user import user_bp
    from app.blueprints.api import api_bp
    from app.blueprints.enrollment import enrollment_bp
    from app.blueprints.payment_admin import payment_admin_bp
    from app.blueprints.language import language_bp
    
    # Nuevos blueprints
    from app.blueprints.articles import articles_bp
    from app.blueprints.subscriptions import subscriptions_bp
    from app.blueprints.newsletter import newsletter_bp
    from app.blueprints.lessons import lessons_bp
    from app.blueprints.technologies import bp as technologies_bp
    
    # Exentar rutas de API y webhooks de CSRF
    csrf.exempt(api_bp)
    csrf.exempt(subscriptions_bp)  # Para webhooks de Stripe/PayPal
    csrf.exempt(newsletter_bp)  # Para tracking pixels
    
    print("Registrando main_bp...")
    app.register_blueprint(main_bp)
    print("main_bp registrado")
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(password_reset_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp)  # Ya tiene url_prefix='/user' definido
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(enrollment_bp)  # Ya tiene url_prefix='/enrollment' definido
    app.register_blueprint(payment_admin_bp)  # Ya tiene url_prefix='/admin/payments' definido
    
    # Registrar nuevos blueprints
    app.register_blueprint(articles_bp, url_prefix='/articulos')
    app.register_blueprint(subscriptions_bp, url_prefix='/suscripciones')
    app.register_blueprint(newsletter_bp, url_prefix='/newsletter')
    app.register_blueprint(lessons_bp, url_prefix='/lecciones')
    app.register_blueprint(language_bp)  # Blueprint para cambio de idioma
    app.register_blueprint(technologies_bp)  # Blueprint para tecnologías
    print("Todos los blueprints registrados")
    
    # Crear tablas si no existen
    with app.app_context():
        print("=== INICIALIZANDO BASE DE DATOS ===")
        
        try:
            # Crear todas las tablas
            print("Creando tablas de base de datos...")
            db.create_all()
            print("✅ Tablas creadas exitosamente")
            
            # Importar todos los modelos para asegurar que estén registrados
            print("Importando modelos...")
            from app.models.user import User
            from app.models.site_config import SiteConfig
            from app.models.blog import BlogPost
            from app.models.course import Course
            from app.models.project import Project
            from app.models.contact import ContactMessage
            from app.models.analytics import PageView, VisitorStats
            from app.models.enrollment import CourseEnrollment, Payment
            from app.models.comment import Comment
            from app.models.favorite import Favorite
            
            # Nuevos modelos
            from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionPayment
            from app.models.article import Article, ArticleCategory
            from app.models.newsletter import NewsletterSubscriber, NewsletterCampaign
            from app.models.lesson import Lesson, CourseSection, LessonProgress
            from app.models.certificate import Certificate
            
            from werkzeug.security import generate_password_hash
            print("✅ Modelos importados exitosamente")
            
            # Credenciales del admin desde variables de entorno
            admin_email = os.environ.get('ADMIN_EMAIL', 'david@codexsoto.com')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'MiPasswordSeguro123!')
            admin_username = admin_email.split('@')[0]  # Usar parte antes del @ como username
            
            # Buscar usuario admin existente por varios criterios
            print("Verificando usuario administrador...")
            admin_user = User.query.filter_by(is_admin=True).first()
            if not admin_user:
                admin_user = User.query.filter_by(email=admin_email).first()
            if not admin_user:
                admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User.query.filter_by(username='administrador').first()
            
            if not admin_user:
                # Crear nuevo usuario admin
                print("Creando usuario administrador...")
                admin_user = User(
                    username=admin_username,
                    email=admin_email,
                    first_name='David',
                    last_name='Soto',
                    bio='Administrador del sitio CodexSoto - Especialista en IA y Automatización',
                    role='admin',
                    is_admin=True,
                    email_verified=True
                )
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                print(f"✅ Usuario administrador creado: {admin_email}")
            else:
                # Actualizar credenciales del admin existente
                print(f"Actualizando credenciales del administrador...")
                admin_user.username = admin_username
                admin_user.email = admin_email
                admin_user.set_password(admin_password)
                admin_user.is_admin = True
                admin_user.role = 'admin'
                admin_user.email_verified = True
                print(f"✅ Credenciales actualizadas: {admin_email}")
            
            # Crear configuración por defecto del sitio
            print("Verificando configuración del sitio...")
            site_config = SiteConfig.query.first()
            
            if not site_config:
                print("Creando configuración por defecto del sitio...")
                site_config = SiteConfig(
                    site_name='CodexSoto',
                    site_description='Investigación en IA, Automatizaciones y Cursos',
                    primary_color='#3b82f6',
                    secondary_color='#1e40af',
                    dark_mode=False,
                    hero_title='David Soto',
                    hero_subtitle='Especialista en Inteligencia Artificial y Automatizaciones',
                    about_text='Investigador y desarrollador especializado en IA, machine learning y automatización de procesos.',
                    contact_email=os.environ.get('ADMIN_EMAIL', 'admin@codexsoto.com'),
                    linkedin_url='https://linkedin.com/in/david-soto',
                    github_url='https://github.com/David080198',
                    twitter_url='https://twitter.com/davidsoto_dev'
                )
                db.session.add(site_config)
                print("✅ Configuración del sitio creada")
            else:
                print("✅ Configuración del sitio ya existe")
            
            # Confirmar todos los cambios
            db.session.commit()
            print("✅ Todos los cambios guardados en la base de datos")
            print("=== INICIALIZACIÓN COMPLETADA ===")
            
        except Exception as e:
            print(f"❌ ERROR durante la inicialización de la base de datos: {e}")
            db.session.rollback()
            print("⚠️  Continuando con la aplicación...")
            import traceback
            traceback.print_exc()
    
    return app

if __name__ == '__main__':
    print("=== INICIANDO APLICACIÓN ===")
    print("Creando app...")
    try:
        app = create_app()
        print("App creada exitosamente")
        print(f"Blueprints registrados: {[bp.name for bp in app.blueprints.values()]}")
        print(f"Rutas disponibles:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
        print("Iniciando servidor...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"ERROR AL CREAR LA APP: {e}")
        import traceback
        traceback.print_exc()
