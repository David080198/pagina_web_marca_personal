#!/usr/bin/env python3
"""Script para crear migración de base de datos para campos de transferencia bancaria"""

import sys
import os
sys.path.append('/app')

# Configurar la aplicación Flask
from app import create_app
from app.extensions import db, migrate

app = create_app()

# Crear migración dentro del contexto de la aplicación
with app.app_context():
    from flask_migrate import init, migrate as create_migration, upgrade
    
    try:
        # Verificar si ya existe directorio de migraciones
        if not os.path.exists('/app/migrations'):
            print("Inicializando Flask-Migrate...")
            init()
        
        # Crear nueva migración
        print("Creando migración para campos de transferencia...")
        create_migration(message="Add transfer fields to Payment model")
        print("Migración creada exitosamente!")
        
        # Aplicar migración
        print("Aplicando migración...")
        upgrade()
        print("Migración aplicada exitosamente!")
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
