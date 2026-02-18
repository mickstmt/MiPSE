from app import app, db
from sqlalchemy import text

def add_columns():
    with app.app_context():
        print("🔄 Intentando añadir columnas RBAC a la tabla 'usuarios'...")
        
        # SQL para añadir columnas si no existen (Postgres syntax)
        sql_commands = [
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ultimo_login TIMESTAMP;",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ip_registro VARCHAR(45);"
        ]
        
        try:
            for sql in sql_commands:
                db.session.execute(text(sql))
            db.session.commit()
            print("✅ Columnas añadidas exitosamente.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al añadir columnas: {e}")

if __name__ == "__main__":
    add_columns()
