#!/usr/bin/env python3
"""
Script simplificado para inicializar la base de datos
"""

import os
import sys
import subprocess

def run_init_via_app():
    """Ejecutar inicialización a través del archivo app.py directamente"""
    
    print("🚀 INICIALIZANDO BASE DE DATOS VIA APP.PY")
    print("=" * 50)
    
    # Ejecutar app.py que tiene la lógica de inicialización
    try:
        # Usar Python para importar y ejecutar la función de inicialización
        init_code = '''
import sys
import os

# Agregar directorio actual al path
sys.path.insert(0, "/app")

# Importar y crear la app (esto ejecuta la inicialización automáticamente)
import app as app_module
flask_app = app_module.create_app()

print("✅ Base de datos inicializada correctamente")
'''
        
        # Ejecutar el código de inicialización
        result = subprocess.run([
            sys.executable, '-c', init_code
        ], capture_output=True, text=True, cwd='/app')
        
        if result.returncode == 0:
            print("✅ Inicialización exitosa")
            print(result.stdout)
        else:
            print("❌ Error en inicialización")
            print(result.stderr)
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit_code = run_init_via_app()
    sys.exit(exit_code)