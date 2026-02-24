from app import app
from models import db, Usuario, Rol

def assign_admin_roles():
    with app.app_context():
        admin_rol = Rol.query.filter_by(nombre='Administrador').first()
        if not admin_rol:
            print(" [RBAC] ❌ Error: El rol 'Administrador' no existe. Ejecuta seed_rbac.py primero.")
            return

        usuarios = Usuario.query.all()
        for u in usuarios:
            if admin_rol not in u.roles:
                u.roles.append(admin_rol)
                print(f" [RBAC] Rol Administrador asignado a: {u.username}")
        
        db.session.commit()
        print(" [RBAC] ✅ Todos los usuarios existentes ahora son Administradores.")

if __name__ == "__main__":
    assign_admin_roles()
