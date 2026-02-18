from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            print("Iniciando migración de base de datos...")
            # Agregar la columna producto_sku a la tabla venta_items si no existe
            db.session.execute(text("ALTER TABLE venta_items ADD COLUMN IF NOT EXISTS producto_sku VARCHAR(100)"))
            db.session.commit()
            print("¡Columna 'producto_sku' añadida exitosamente!")
        except Exception as e:
            db.session.rollback()
            print(f"Error durante la migración: {e}")

if __name__ == "__main__":
    migrate()
