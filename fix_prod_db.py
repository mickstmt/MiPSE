from app import app, db
from sqlalchemy import text, inspect

def fix_production_db():
    with app.app_context():
        print("🛠️ Diagnóstico y Reparación de DB en Producción...")

        inspector = inspect(db.engine)

        # ──────────────────────────────────────────────
        # BLOQUE 1: Columnas de auditoría en 'usuarios'
        # ──────────────────────────────────────────────
        print("\n🔍 [1/3] Verificando columnas de 'usuarios'...")
        try:
            columns = [c['name'] for c in inspector.get_columns('usuarios')]
            print(f"   Columnas actuales: {', '.join(columns)}")
        except Exception as e:
            print(f"❌ Error al inspeccionar 'usuarios': {e}")

        column_commands_usuarios = [
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ultimo_login TIMESTAMP;",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ip_registro VARCHAR(45);"
        ]

        cleanup_commands = [
            "DROP TABLE IF EXISTS rol_permisos CASCADE;",
            "DROP TABLE IF EXISTS usuario_roles CASCADE;",
            "DROP TABLE IF EXISTS roles CASCADE;",
            "DROP TABLE IF EXISTS permisos CASCADE;",
            "DROP SEQUENCE IF EXISTS roles_id_seq CASCADE;",
            "DROP SEQUENCE IF EXISTS permisos_id_seq CASCADE;"
        ]

        # ──────────────────────────────────────────────
        # BLOQUE 2: Columnas nuevas en 'ventas'
        # ──────────────────────────────────────────────
        print("\n🔍 [2/3] Verificando columnas de 'ventas'...")
        column_commands_ventas = [
            "ALTER TABLE ventas ADD COLUMN IF NOT EXISTS costo_envio NUMERIC(10,2) DEFAULT 0.00;",
            "ALTER TABLE ventas ADD COLUMN IF NOT EXISTS fecha_pedido TIMESTAMP;"
        ]

        # ──────────────────────────────────────────────
        # BLOQUE 3: Tabla costos_productos
        # ──────────────────────────────────────────────
        print("\n🔍 [3/3] Verificando tabla 'costos_productos'...")
        create_costos_table = """
            CREATE TABLE IF NOT EXISTS costos_productos (
                id SERIAL PRIMARY KEY,
                sku VARCHAR(100),
                desc VARCHAR(255),
                colorcode VARCHAR(100),
                sizecode VARCHAR(100),
                costo NUMERIC(10,2) DEFAULT 0.00
            );
        """

        try:
            print(" -> Asegurando columnas de auditoría en 'usuarios'...")
            for cmd in column_commands_usuarios:
                print(f"    {cmd}")
                db.session.execute(text(cmd))

            print(" -> Limpiando RBAC inconsistente...")
            for cmd in cleanup_commands:
                db.session.execute(text(cmd))

            print(" -> Asegurando columnas nuevas en 'ventas'...")
            for cmd in column_commands_ventas:
                print(f"    {cmd}")
                db.session.execute(text(cmd))

            print(" -> Asegurando tabla 'costos_productos'...")
            db.session.execute(text(create_costos_table))

            db.session.commit()
            print("\n✅ Esquema de BD actualizado correctamente.")

            # Re-crear tablas faltantes con SQLAlchemy
            print("🔄 Re-creando tablas faltantes con db.create_all()...")
            db.create_all()
            print("✅ db.create_all() completado.")

            # Verificación final
            inspector = inspect(db.engine)
            ventas_cols = [c['name'] for c in inspector.get_columns('ventas')]
            print(f"\n📋 Columnas en 'ventas': {', '.join(ventas_cols)}")
            for col in ['costo_envio', 'fecha_pedido']:
                status = "✅" if col in ventas_cols else "❌ FALTA"
                print(f"   {status} {col}")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error crítico: {e}")

if __name__ == "__main__":
    fix_production_db()
