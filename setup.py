#!/usr/bin/env python3
"""
Script de inicialización para CodexSoto
Copia las imágenes existentes y configura el proyecto
"""

import os
import shutil
from pathlib import Path

def copy_images():
    """Copia las imágenes existentes al directorio static"""
    source_dir = Path("../imagenes")
    dest_dir = Path("app/static/images")
    
    if source_dir.exists():
        print("Copiando imágenes existentes...")
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Mapear archivos específicos
        image_mapping = {
            "perfil.jpeg": "profile.jpg",
            "logo_colores.png": "logo.png",
            "logo_transparente.png": "logo_transparent.png",
            "fondo_programacion.jpg": "background.jpg"
        }
        
        for source_name, dest_name in image_mapping.items():
            source_file = source_dir / source_name
            dest_file = dest_dir / dest_name
            
            if source_file.exists():
                shutil.copy2(source_file, dest_file)
                print(f"✓ Copiado: {source_name} → {dest_name}")
            else:
                print(f"✗ No encontrado: {source_name}")
    else:
        print("Directorio de imágenes no encontrado. Creando imágenes de ejemplo...")
        dest_dir.mkdir(parents=True, exist_ok=True)

def create_env_file():
    """Crea el archivo .env si no existe"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("Creando archivo .env...")
        shutil.copy2(".env.example", ".env")
        print("✓ Archivo .env creado. Recuerda modificar las variables según tu configuración.")
    else:
        print("Archivo .env ya existe.")

def create_init_files():
    """Crea archivos __init__.py necesarios"""
    init_files = [
        "app/__init__.py",
        "app/blueprints/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"✓ Creado: {init_file}")

def show_instructions():
    """Muestra las instrucciones finales"""
    print("\n" + "="*60)
    print("🎉 ¡CodexSoto está listo!")
    print("="*60)
    print("\n📋 Pasos siguientes:")
    print("\n1. Configurar variables de entorno:")
    print("   - Edita el archivo .env con tus datos")
    print("   - Cambia ADMIN_PASSWORD por una contraseña segura")
    print("\n2. Levantar la aplicación:")
    print("   docker-compose up -d")
    print("\n3. Acceder a la aplicación:")
    print("   - Sitio web: http://localhost")
    print("   - Panel admin: http://localhost/auth/login")
    print("   - Usuario: admin")
    print("   - Contraseña: (la que configuraste en .env)")
    print("\n4. API REST disponible en:")
    print("   - http://localhost/api/posts")
    print("   - http://localhost/api/courses")
    print("   - http://localhost/api/projects")
    print("   - http://localhost/api/config")
    print("\n🚀 ¡A crear contenido increíble!")
    print("="*60)

if __name__ == "__main__":
    print("Iniciando configuración de CodexSoto...")
    
    copy_images()
    create_env_file()
    create_init_files()
    show_instructions()
