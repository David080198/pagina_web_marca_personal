#!/usr/bin/env python3
"""
Script para recrear las tablas con la estructura correcta
Este script maneja el problema de columnas faltantes
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def recreate_tables():
    """Recrear todas las tablas con la estructura correcta"""
    
    print("🚀 RECREANDO TABLAS DE BASE DE DATOS")
    print("=" * 50)
    
    try:
        # Importar la aplicación del archivo app.py
        import sys
        import importlib.util
        
        # Cargar el módulo app.py específicamente
        spec = importlib.util.spec_from_file_location("app_module", "app.py")
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        from app.extensions import db
        
        # Crear la aplicación
        flask_app = app_module.create_app()
        
        with flask_app.app_context():
            print("🗑️ Eliminando todas las tablas existentes...")
            
            # Eliminar todas las tablas
            db.drop_all()
            print("✅ Tablas eliminadas")
            
            print("📋 Creando todas las tablas con estructura actualizada...")
            
            # Importar todos los modelos
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
            print("✅ Tablas creadas con estructura actualizada")
            
            # Crear usuario administrador
            print("👤 Creando usuario administrador...")
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
            
            # Crear configuración del sitio (solo con campos que existen)
            print("⚙️ Configurando sitio...")
            site_config = SiteConfig(
                site_name='CodexSoto',
                site_description='Investigación en IA, Automatizaciones y Cursos',
                primary_color='#3b82f6',
                secondary_color='#1e40af',
                dark_mode=False,
                hero_title='David Soto',
                hero_subtitle='Especialista en Inteligencia Artificial y Automatizaciones',
                about_text='Investigador y desarrollador especializado en IA, machine learning y automatización de procesos.',
                contact_email=admin_email,
                linkedin_url='https://linkedin.com/in/david-soto',
                github_url='https://github.com/David080198',
                twitter_url='https://twitter.com/davidsoto_dev'
            )
            db.session.add(site_config)
            print("✅ Configuración del sitio creada")
            
            # Confirmar cambios
            db.session.commit()
            print("💾 Cambios guardados en la base de datos")
            
        print("=" * 50)
        print("🎉 ¡RECREACIÓN COMPLETADA EXITOSAMENTE!")
        print("=" * 50)
        print("📝 INFORMACIÓN DE ACCESO:")
        print(f"   🌐 Panel admin: http://localhost/admin")
        print(f"   📧 Email: {admin_email}")
        print(f"   🔑 Contraseña: {admin_password}")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ ERROR durante la recreación: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit_code = recreate_tables()
    sys.exit(exit_code)