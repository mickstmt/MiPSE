from app import app, db
from models import producto_categorias

with app.app_context():
    print("🔄 Creando tabla de asociación 'producto_categorias'...")
    try:
        # Esto solo creará las tablas que NO existen
        db.create_all()
        print("✅ Base de datos actualizada exitosamente")
    except Exception as e:
        print(f"❌ Error al actualizar DB: {e}")
