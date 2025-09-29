#!/usr/bin/env python3
"""
Script para actualizar la base de datos con los nuevos campos
"""
import os
import sys

# Configurar el path correcto
sys.path.insert(0, '/app')

# Importar desde el archivo app.py en la raíz
import app as app_module
from app.extensions import db

create_app = app_module.create_app

def upgrade_database():
    """Actualiza la base de datos con los nuevos campos"""
    app = create_app()
    
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("✅ Base de datos actualizada correctamente")
        print("✅ Se han añadido los nuevos campos para tarjetas de crédito")

if __name__ == '__main__':
    upgrade_database()
