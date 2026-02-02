"""
Script para ajustar el correlativo inicial y actualizar las ventas existentes
"""

from app import app, db
from models import Venta

print("="*70)
print("AJUSTE DE CORRELATIVO Y SERIE")
print("="*70)

# Serie y correlativo correctos
SERIE_CORRECTA = "EB01"
CORRELATIVO_INICIAL = 5907  # La próxima venta que crearás

with app.app_context():
    # Obtener todas las ventas
    ventas = Venta.query.order_by(Venta.id.asc()).all()

    print(f"\n📋 Ventas actuales en la base de datos: {len(ventas)}")

    if len(ventas) == 0:
        print("   No hay ventas para ajustar")
        print(f"\n✅ La próxima venta será: {SERIE_CORRECTA}-{str(CORRELATIVO_INICIAL).zfill(8)}")
    else:
        print(f"\n⚠️  Opciones disponibles:\n")
        print(f"1. Eliminar todas las ventas de prueba y empezar desde {CORRELATIVO_INICIAL}")
        print(f"2. Actualizar las ventas existentes con la serie correcta ({SERIE_CORRECTA})")
        print(f"3. Solo mostrar información (no hacer cambios)")

        opcion = input("\nElige una opción (1/2/3): ").strip()

        if opcion == "1":
            print(f"\n⚠️  ¿Estás SEGURO de eliminar las {len(ventas)} ventas?")
            confirmar = input("Escribe 'SI' para confirmar: ").strip().upper()

            if confirmar == "SI":
                for venta in ventas:
                    db.session.delete(venta)

                db.session.commit()
                print(f"\n✅ {len(ventas)} venta(s) eliminadas")
                print(f"✅ La próxima venta será: {SERIE_CORRECTA}-{str(CORRELATIVO_INICIAL).zfill(8)}")
            else:
                print("\n❌ Cancelado")

        elif opcion == "2":
            print(f"\n🔄 Actualizando ventas con serie {SERIE_CORRECTA}...")

            # Actualizar cada venta con el nuevo formato
            correlativo_actual = CORRELATIVO_INICIAL

            for idx, venta in enumerate(ventas):
                nuevo_correlativo = correlativo_actual + idx
                nuevo_correlativo_str = str(nuevo_correlativo).zfill(8)
                nuevo_numero_completo = f"{SERIE_CORRECTA}-{nuevo_correlativo_str}"

                print(f"   Venta {venta.id}: {venta.numero_completo} -> {nuevo_numero_completo}")

                venta.serie = SERIE_CORRECTA
                venta.correlativo = nuevo_correlativo_str
                venta.numero_completo = nuevo_numero_completo

            db.session.commit()
            print(f"\n✅ {len(ventas)} venta(s) actualizadas")
            print(f"✅ La próxima venta será: {SERIE_CORRECTA}-{str(correlativo_actual + len(ventas)).zfill(8)}")

        else:
            print(f"\n📊 Información actual:")
            for venta in ventas[:10]:  # Mostrar primeras 10
                print(f"   {venta.numero_completo} - {venta.estado} - S/ {venta.total}")

            if len(ventas) > 10:
                print(f"   ... y {len(ventas) - 10} más")

            # Mostrar último correlativo
            ultimo = ventas[-1]
            print(f"\n   Última venta: {ultimo.numero_completo}")

            try:
                ultimo_num = int(ultimo.correlativo)
                proximo = ultimo_num + 1
                print(f"   Próxima venta será: {SERIE_CORRECTA}-{str(proximo).zfill(8)}")
            except:
                print(f"   Próxima venta será: {SERIE_CORRECTA}-{str(CORRELATIVO_INICIAL).zfill(8)}")

print("\n" + "="*70)
