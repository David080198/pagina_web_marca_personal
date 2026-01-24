"""
Script to update the admin username and password.
Usage: python scripts/change_admin_credentials.py

This script will:
 - find the admin user by username 'admin' or by ADMIN_EMAIL env var
 - update username to 'administrador'
 - update password to the value specified in the variable below
"""
import os
import importlib.util
import pathlib
from werkzeug.security import generate_password_hash

# Import the application factory from the top-level app.py file (module name conflicts with package `app`)
ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("app_module", str(ROOT / "app.py"))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
create_app = app_module.create_app

# Now import extensions and models from the package
from app.extensions import db
from app.models.user import User

# Nuevas credenciales - CAMBIAR según necesites
NEW_USERNAME = 'david'
NEW_PASSWORD = 'MiPasswordSeguro123!'
NEW_EMAIL = 'david@codexsoto.com'

app = create_app()

with app.app_context():
    # Buscar usuario admin existente por varios criterios
    user = User.query.filter_by(username='admin').first()
    if not user:
        user = User.query.filter_by(username='administrador').first()
    if not user:
        user = User.query.filter_by(is_admin=True).first()
    if not user:
        admin_email = os.environ.get('ADMIN_EMAIL')
        if admin_email:
            user = User.query.filter_by(email=admin_email).first()

    if not user:
        print('No se encontró ningún usuario administrador. Creando uno nuevo...')
        user = User(
            username=NEW_USERNAME,
            email=NEW_EMAIL,
            is_admin=True,
            role='admin'
        )
        user.set_password(NEW_PASSWORD)
        db.session.add(user)
        db.session.commit()
        print(f"✅ Usuario admin creado: {NEW_USERNAME} / {NEW_EMAIL}")
    else:
        # Actualizar credenciales
        old_username = user.username
        user.username = NEW_USERNAME
        user.email = NEW_EMAIL
        user.set_password(NEW_PASSWORD)
        user.is_admin = True
        user.role = 'admin'
        db.session.commit()
        print(f"✅ Credenciales actualizadas!")
        print(f"   Usuario anterior: {old_username}")
        print(f"   Nuevo usuario: {NEW_USERNAME}")
        print(f"   Email: {NEW_EMAIL}")
        print(f"   Contraseña: {NEW_PASSWORD}")
