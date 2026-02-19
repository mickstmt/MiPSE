from app import app, db
from sqlalchemy import text

def fix_production_db():
    with app.app_context():
        print("🛠️ Iniciando limpieza y actualización de DB en Producción...")
        
        # 1. Comandos para limpiar secuencias y tablas parciales que causan conflictos
        cleanup_commands = [
            "DROP TABLE IF EXISTS rol_permisos CASCADE;",
            "DROP TABLE IF EXISTS usuario_roles CASCADE;",
            "DROP TABLE IF EXISTS roles CASCADE;",
            "DROP TABLE IF EXISTS permisos CASCADE;",
            "DROP SEQUENCE IF EXISTS roles_id_seq CASCADE;",
            "DROP SEQUENCE IF EXISTS permisos_id_seq CASCADE;"
        ]
        
        # 2. Comandos para añadir las columnas faltantes a la tabla de usuarios
        # Usamos IF NOT EXISTS para evitar errores si ya se intentó antes
        column_commands = [
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ultimo_login TIMESTAMP;",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ip_registro VARCHAR(45);"
        ]
        
        try:
            # Ejecutar limpieza
            print(" -> Limpiando estados inconsistentes...")
            for cmd in cleanup_commands:
                print(f"    - {cmd}")
                db.session.execute(text(cmd))
            
            # Ejecutar actualización de columnas
            print(" -> Asegurando columnas de auditoría en 'usuarios'...")
            for cmd in column_commands:
                print(f"    - {cmd}")
                db.session.execute(text(cmd))
                
            db.session.commit()
            print("✅ Limpieza y actualización de columnas completada.")
            
            # Re-crear tablas usando SQLAlchemy
            print("🔄 Re-creando tablas de Roles y Permisos...")
            db.create_all()
            print("✅ Tablas creadas exitosamente.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error durante el proceso: {e}")

if __name__ == "__main__":
    fix_production_db()
