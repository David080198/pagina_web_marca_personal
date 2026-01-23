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

NEW_USERNAME = 'administrador'
NEW_PASSWORD = 'David1Soto2'

app = create_app()

with app.app_context():
    # Prefer finding by username 'admin'
    user = User.query.filter_by(username='admin').first()
    if not user:
        admin_email = os.environ.get('ADMIN_EMAIL')
        if admin_email:
            user = User.query.filter_by(email=admin_email).first()

    if not user:
        print('No se encontró el usuario administrador (username="admin" o ADMIN_EMAIL). No se aplicaron cambios.')
    else:
        # Check for username conflict
        conflict = User.query.filter(User.username==NEW_USERNAME, User.id!=user.id).first()
        if conflict:
            print(f"Existe otro usuario con username '{NEW_USERNAME}'. Cambia el NEW_USERNAME en el script o elimina/confirma el usuario conflictivo.")
        else:
            user.username = NEW_USERNAME
            user.password_hash = generate_password_hash(NEW_PASSWORD)
            user.is_admin = True
            user.role = 'admin'
            db.session.commit()
            print(f"Credenciales actualizadas. Nuevo username: {user.username} | contraseña: {NEW_PASSWORD}")
