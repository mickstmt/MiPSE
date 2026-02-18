from app import app
from models import db, Rol, Permiso

def seed_rbac():
    with app.app_context():
        # 1. Crear Permisos básicos
        permisos_data = [
            ('Crear Ventas', 'ventas.crear'),
            ('Ver Ventas', 'ventas.ver'),
            ('Gestionar Productos', 'productos.gestionar'),
            ('Ver Reportes', 'reportes.ver'),
            ('Gestionar Usuarios', 'usuarios.gestionar'),
            ('Editar Diseño PDF', 'diseno.editar'),
        ]
        
        permisos_objs = {}
        for nombre, codigo in permisos_data:
            permiso = Permiso.query.filter_by(codigo=codigo).first()
            if not permiso:
                permiso = Permiso(nombre=nombre, codigo=codigo)
                db.session.add(permiso)
                print(f" [RBAC] Permiso creado: {codigo}")
            permisos_objs[codigo] = permiso
        
        db.session.commit()

        # 2. Crear Roles y asignar permisos
        roles_data = [
            {
                'nombre': 'Administrador',
                'desc': 'Acceso total al sistema',
                'permisos': ['ventas.crear', 'ventas.ver', 'productos.gestionar', 'reportes.ver', 'usuarios.gestionar', 'diseno.editar']
            },
            {
                'nombre': 'Vendedor',
                'desc': 'Solo puede realizar ventas y ver clientes',
                'permisos': ['ventas.crear', 'ventas.ver']
            },
            {
                'nombre': 'Almacén',
                'desc': 'Gestión de inventario y productos',
                'permisos': ['productos.gestionar', 'ventas.ver']
            },
            {
                'nombre': 'Consulta',
                'desc': 'Solo visualización de reportes y ventas',
                'permisos': ['ventas.ver', 'reportes.ver']
            }
        ]

        for r_data in roles_data:
            rol = Rol.query.filter_by(nombre=r_data['nombre']).first()
            if not rol:
                rol = Rol(nombre=r_data['nombre'], descripcion=r_data['desc'])
                db.session.add(rol)
                print(f" [RBAC] Rol creado: {r_data['nombre']}")
            
            # Asignar permisos al rol
            rol.permisos = [permisos_objs[p_cod] for p_cod in r_data['permisos']]
        
        db.session.commit()
        print(" [RBAC] ✅ Seed completado exitosamente.")

if __name__ == "__main__":
    seed_rbac()
