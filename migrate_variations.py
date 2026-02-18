from app import app, db
from sqlalchemy import text

with app.app_context():
    print("🔄 Actualizando esquema de base de datos para variaciones...")
    try:
        with db.engine.connect() as conn:
            # Añadir tipo a productos
            conn.execute(text("ALTER TABLE productos ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) DEFAULT 'simple'"))
            
            # Añadir variacion_id y atributos_json a venta_items
            conn.execute(text("ALTER TABLE venta_items ADD COLUMN IF NOT EXISTS variacion_id INTEGER"))
            conn.execute(text("ALTER TABLE venta_items ADD COLUMN IF NOT EXISTS atributos_json JSONB")) # JSONB es mejor en Postgres
            
            # La tabla variaciones se creará con db.create_all() si no existe
            conn.commit()
            
        db.create_all()
        print("✅ Base de datos actualizada con éxito")
    except Exception as e:
        print(f"❌ Error al actualizar DB: {e}")
