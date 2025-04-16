from app import app, db, User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

# Configurar el contexto de la aplicación
with app.app_context():
    # Crear un usuario administrador
    hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
    admin_user = User(username="admin", password=hashed_password, is_admin=True, is_active=True)
    db.session.add(admin_user)
    db.session.commit()
    print("Usuario administrador creado exitosamente.")