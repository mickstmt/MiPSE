"""
Script para probar envio de boleta via MiPSE
Ejecutar: python probar_mipse.py
"""
from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import Venta
from mipse_service import MiPSEService

def probar_envio(venta_id=None):
    """Prueba el envio de una venta via MiPSE"""

    print("=" * 60)
    print("  PRUEBA DE ENVIO VIA MiPSE")
    print("=" * 60)
    print()

    with app.app_context():
        # Obtener venta
        if venta_id:
            venta = db.session.get(Venta, venta_id)
        else:
            # Buscar ultima venta pendiente
            venta = Venta.query.filter(
                Venta.fecha_envio_sunat == None
            ).order_by(Venta.id.desc()).first()

        if not venta:
            print("No hay ventas pendientes de enviar")
            return

        print(f"Venta seleccionada:")
        print(f"  ID: {venta.id}")
        print(f"  Numero: {venta.serie}-{venta.correlativo}")
        print(f"  Total: S/ {venta.total}")
        print(f"  Fecha: {venta.fecha_emision}")
        print()

        # Crear servicio MiPSE
        service = MiPSEService()
        print()

        # Procesar venta
        print("Iniciando envio...")
        print()
        resultado = service.procesar_venta(venta)

        # Mostrar resultado
        print()
        print("=" * 60)
        print("  RESULTADO")
        print("=" * 60)

        if resultado.get('success'):
            print("  EXITO!")
            print(f"  Mensaje: {resultado.get('mensaje')}")
            print(f"  Hash: {resultado.get('hash')}")

            # Actualizar venta en BD
            from datetime import datetime
            venta.fecha_envio_sunat = datetime.now()
            venta.hash_cpe = resultado.get('hash')
            venta.mensaje_sunat = resultado.get('mensaje')
            db.session.commit()
            print()
            print("  Venta actualizada en la base de datos")
        else:
            print("  ERROR")
            print(f"  Mensaje: {resultado.get('mensaje')}")
            if resultado.get('error'):
                print(f"  Detalle: {resultado.get('error')}")

        print()
        return resultado


if __name__ == "__main__":
    import sys

    venta_id = None
    if len(sys.argv) > 1:
        venta_id = int(sys.argv[1])
        print(f"Probando con venta ID: {venta_id}")

    probar_envio(venta_id)
