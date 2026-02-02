"""
Script para limpiar todas las ventas y reiniciar desde B001-00000001
"""
from app import app, db
from models import Venta, VentaItem

print("=" * 60)
print("  LIMPIAR VENTAS Y REINICIAR CORRELATIVO")
print("=" * 60)

with app.app_context():
    # Contar ventas actuales
    total_ventas = Venta.query.count()
    total_items = VentaItem.query.count()

    print(f"\nVentas actuales: {total_ventas}")
    print(f"Items de venta: {total_items}")

    if total_ventas == 0:
        print("\nNo hay ventas para eliminar.")
    else:
        # Mostrar ventas antes de eliminar
        print("\nVentas a eliminar:")
        ventas = Venta.query.order_by(Venta.id).all()
        for v in ventas[:10]:
            print(f"  - {v.serie}-{v.correlativo} | Total: S/ {v.total} | Estado: {v.estado}")
        if len(ventas) > 10:
            print(f"  ... y {len(ventas) - 10} mas")

        # Eliminar todos los items primero (por si cascade no funciona)
        VentaItem.query.delete()

        # Eliminar todas las ventas
        Venta.query.delete()

        # Commit
        db.session.commit()

        print(f"\n ELIMINADAS {total_ventas} ventas y {total_items} items")

    # Verificar que quedo limpio
    ventas_restantes = Venta.query.count()
    print(f"\nVentas restantes: {ventas_restantes}")
    print(f"\nProxima venta sera: B001-00000001")

print("\n" + "=" * 60)
