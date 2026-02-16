from flask import Flask
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def create_app():
    # Configurar rutas de templates y static
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Importar extensiones localmente para evitar imports circulares
    from app.extensions import db, login_manager, migrate, mail, csrf
    
    # Configuración
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///codexsoto.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
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
    csrf.init_app(app)
    
    # Inicializar analytics
    from app.utils.analytics import init_analytics
    init_analytics(app)
    
    # Configuración de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Registrar Blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
        
        # Crear usuario admin por defecto
        from app.models.user import User
        from app.models.site_config import SiteConfig
        from app.models.analytics import PageView, VisitorStats
        from werkzeug.security import generate_password_hash
        
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email=os.environ.get('ADMIN_EMAIL', 'admin@codexsoto.com'),
                password_hash=generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123')),
                is_admin=True
            )
            db.session.add(admin_user)
        
        # Crear configuración por defecto del sitio
        site_config = SiteConfig.query.first()
        if not site_config:
            site_config = SiteConfig(
                site_name='CodexSoto',
                site_description='Investigación en IA, Automatizaciones y Cursos',
                primary_color='#3b82f6',
                secondary_color='#1e40af',
                dark_mode=False,
                hero_title='David Soto',
                hero_subtitle='Especialista en Inteligencia Artificial y Automatizaciones',
                about_text='Investigador y desarrollador especializado en IA, machine learning y automatización de procesos.'
            )
            db.session.add(site_config)
        
        db.session.commit()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
