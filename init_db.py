#!/usr/bin/env python3
"""
Script para inicializar la base de datos de CodexSoto
Ejecuta este script para crear todas las tablas y datos iniciales
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Inicializar la base de datos con todas las tablas y datos por defecto"""
    
    print("🚀 INICIANDO INICIALIZACIÓN DE BASE DE DATOS")
    print("=" * 50)
    
    try:
        # Importar la aplicación desde el archivo app.py (no del paquete app/)
        import app as app_module
        from app.extensions import db
        
        # Crear la aplicación
        flask_app = app_module.create_app()
        
        with flask_app.app_context():
            print("📋 Creando todas las tablas...")
            
            # Importar todos los modelos para registrarlos
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
            
            # Crear todas las tablas
            db.create_all()
            print("✅ Tablas creadas exitosamente")
            
            # Crear usuario administrador
            print("👤 Creando usuario administrador...")
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                admin_email = os.environ.get('ADMIN_EMAIL', 'admin@codexsoto.com')
                admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
                
                admin_user = User(
                    username='admin',
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
                print(f"🔑 Contraseña: {admin_password}")
            else:
                print(f"✅ Usuario administrador ya existe: {admin_user.email}")
            
            # Crear configuración del sitio
            print("⚙️ Configurando sitio...")
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
            
            # Confirmar cambios
            db.session.commit()
            print("💾 Cambios guardados en la base de datos")
            
        print("=" * 50)
        print("🎉 ¡INICIALIZACIÓN COMPLETADA EXITOSAMENTE!")
        print("=" * 50)
        print("📝 INFORMACIÓN DE ACCESO:")
        print(f"   🌐 URL: http://localhost/admin")
        print(f"   📧 Email: {os.environ.get('ADMIN_EMAIL', 'admin@codexsoto.com')}")
        print(f"   🔑 Contraseña: {os.environ.get('ADMIN_PASSWORD', 'admin123')}")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ ERROR durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit_code = init_database()
    sys.exit(exit_code)