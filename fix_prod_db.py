from app import app, db
from sqlalchemy import text, inspect

def fix_production_db():
    with app.app_context():
        print("🛠️ Diagnóstico y Reparación de DB en Producción...")
        
        # 1. Verificar columnas actuales en 'usuarios'
        inspector = inspect(db.engine)
        print("🔍 Verificando columnas de la tabla 'usuarios'...")
        try:
            columns = [c['name'] for c in inspector.get_columns('usuarios')]
            print(f"   Columnas actuales: {', '.join(columns)}")
        except Exception as e:
            print(f"❌ Error al inspeccionar la tabla: {e}")
            columns = []

        # 2. Comandos para asegurar columnas de auditoría
        # Usamos SQL puro para evitar cualquier caché de SQLAlchemy
        column_commands = [
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ultimo_login TIMESTAMP;",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ip_registro VARCHAR(45);"
        ]
        
        # 3. Limpieza de secuencias y tablas RBAC para evitar colisiones
        cleanup_commands = [
            "DROP TABLE IF EXISTS rol_permisos CASCADE;",
            "DROP TABLE IF EXISTS usuario_roles CASCADE;",
            "DROP TABLE IF EXISTS roles CASCADE;",
            "DROP TABLE IF EXISTS permisos CASCADE;",
            "DROP SEQUENCE IF EXISTS roles_id_seq CASCADE;",
            "DROP SEQUENCE IF EXISTS permisos_id_seq CASCADE;"
        ]
        
        try:
            # Ejecutar adición de columnas PRIMERO (ya que es lo que más urge para el login)
            print(" -> Asegurando columnas de auditoría en 'usuarios'...")
            for cmd in column_commands:
                print(f"    Ejecutando: {cmd}")
                db.session.execute(text(cmd))
            
            # Ejecutar limpieza de RBAC
            print(" -> Limpiando estados inconsistentes de RBAC...")
            for cmd in cleanup_commands:
                db.session.execute(text(cmd))
                
            db.session.commit()
            print("✅ Actualización de esquema completada.")
            
            # Re-crear tablas usando SQLAlchemy
            print("🔄 Re-creando tablas de Roles y Permisos...")
            db.create_all()
            print("✅ Tablas creadas exitosamente.")
            
            # Verificación final
            inspector = inspect(db.engine)
            final_columns = [c['name'] for c in inspector.get_columns('usuarios')]
            print(f"📋 Verificación Final - Columnas en 'usuarios': {', '.join(final_columns)}")
            
            if 'ultimo_login' in final_columns:
                print("✨ ¡ÉXITO! La columna 'ultimo_login' ahora existe.")
            else:
                print("⚠️ ADVERTENCIA: La columna 'ultimo_login' sigue sin aparecer.")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error crítico durante el proceso: {e}")

if __name__ == "__main__":
    fix_production_db()
