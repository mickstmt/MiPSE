from app import app, db
from models import Usuario
import sys

def create_admin(nombre, email, password):
    with app.app_context():
        # Check if user already exists
        user = Usuario.query.filter_by(email=email).first()
        if user:
            print(f"⚠️  El usuario {email} ya existe.")
            return

        # Create new admin user
        admin = Usuario(
            nombre=nombre,
            email=email,
            es_admin=True,
            activo=True
        )
        admin.set_password(password)

        try:
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Usuario administrador creado exitosamente:")
            print(f"   Nombre: {nombre}")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear el usuario: {str(e)}")

if __name__ == "__main__":
    # Parametros por defecto o desde argumentos
    nombre = "Administrador"
    email = "admin@izistoreperu.com"
    password = "AdminInitial123!"
    
    create_admin(nombre, email, password)
