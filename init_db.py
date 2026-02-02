from app import app, db

with app.app_context():
    print("🗑️  Eliminando tablas existentes...")
    db.drop_all()
    print("✅ Tablas eliminadas")
    
    print("🔄 Creando tablas nuevamente...")
    db.create_all()
    print("✅ ¡Tablas creadas exitosamente!")
    print("\n📋 Tablas creadas:")
    print("   - usuarios")
    print("   - clientes")
    print("   - ventas")
    print("   - venta_items")
    print("\n✅ Ahora puedes ejecutar: python app.py")
