from app import app, db
from sqlalchemy import text

def fix_production_db():
    with app.app_context():
        print("🛠️ Iniciando limpieza de inconsistencias en DB de Producción...")
        
        # Lista de comandos para limpiar secuencias y tablas parciales de RBAC
        # Esto permitirá que db.create_all() vuelva a intentarlo limpiamente
        commands = [
            "DROP TABLE IF EXISTS rol_permisos CASCADE;",
            "DROP TABLE IF EXISTS usuario_roles CASCADE;",
            "DROP TABLE IF EXISTS roles CASCADE;",
            "DROP TABLE IF EXISTS permisos CASCADE;",
            "DROP SEQUENCE IF EXISTS roles_id_seq CASCADE;",
            "DROP SEQUENCE IF EXISTS permisos_id_seq CASCADE;"
        ]
        
        try:
            for cmd in commands:
                print(f" -> Ejecutando: {cmd}")
                db.session.execute(text(cmd))
            db.session.commit()
            print("✅ Limpieza completada. Ahora SQLAlchemy podrá crear las tablas de nuevo.")
            
            print("🔄 Re-creando tablas...")
            db.create_all()
            print("✅ Tablas creadas exitosamente.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error durante la limpieza: {e}")

if __name__ == "__main__":
    fix_production_db()
