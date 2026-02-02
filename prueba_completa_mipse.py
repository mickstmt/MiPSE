"""
Script para crear venta y enviar via MiPSE
"""
from dotenv import load_dotenv
load_dotenv(override=True)

from datetime import datetime
from app import app, db
from models import Venta, VentaItem, Cliente, Usuario
from mipse_service import MiPSEService
import config

print("=" * 60)
print("  PRUEBA COMPLETA: CREAR VENTA Y ENVIAR VIA MiPSE")
print("=" * 60)

with app.app_context():
    # 1. Buscar o crear cliente
    cliente = Cliente.query.filter_by(numero_documento="12345678").first()
    if not cliente:
        print("\nCreando cliente de prueba...")
        cliente = Cliente(
            numero_documento="12345678",
            tipo_documento="DNI",
            nombres="CLIENTE",
            apellido_paterno="PRUEBA",
            apellido_materno="SUNAT",
            direccion="Lima, Peru"
        )
        db.session.add(cliente)
        db.session.commit()
    print(f"Cliente: {cliente.nombre_completo} (DNI: {cliente.numero_documento})")

    # 2. Obtener vendedor
    vendedor = Usuario.query.first()
    if not vendedor:
        print("ERROR: No hay usuarios")
        exit(1)
    print(f"Vendedor: {vendedor.nombre}")

    # 3. Obtener siguiente correlativo
    serie = config.Config.SERIE_BOLETA  # B001
    ultima_venta = Venta.query.filter(Venta.serie == serie)\
        .order_by(db.cast(Venta.correlativo, db.Integer).desc()).first()

    if ultima_venta:
        siguiente = int(ultima_venta.correlativo) + 1
    else:
        siguiente = 1

    correlativo_str = str(siguiente).zfill(8)
    numero_completo = f"{serie}-{correlativo_str}"

    print(f"\nComprobante: {numero_completo}")

    # 4. Crear venta
    venta = Venta(
        cliente_id=cliente.id,
        vendedor_id=vendedor.id,
        fecha_emision=datetime.now(),
        serie=serie,
        correlativo=correlativo_str,
        numero_completo=numero_completo,
        subtotal=42.37,  # 50 / 1.18
        total=50.00,
        estado="PENDIENTE"
    )
    db.session.add(venta)
    db.session.flush()

    # 5. Crear item
    item = VentaItem(
        venta_id=venta.id,
        producto_nombre="PRODUCTO DE PRUEBA",
        cantidad=1,
        precio_unitario=50.00,
        subtotal=50.00
    )
    db.session.add(item)
    db.session.commit()

    print(f"Venta creada: ID {venta.id}")
    print(f"Total: S/ {venta.total}")
    print(f"Fecha: {venta.fecha_emision}")

    # 6. Enviar via MiPSE
    print("\n" + "=" * 60)
    print("  ENVIANDO A SUNAT VIA MiPSE")
    print("=" * 60)

    service = MiPSEService()
    resultado = service.procesar_venta(venta)

    print("\n" + "=" * 60)
    print("  RESULTADO")
    print("=" * 60)

    if resultado.get('success'):
        print("EXITO!")
        print(f"Mensaje: {resultado.get('mensaje')}")
        print(f"Hash: {resultado.get('hash')}")
        if resultado.get('cdr'):
            print("CDR: Recibido (base64)")

        # Actualizar venta
        venta.fecha_envio_sunat = datetime.now()
        venta.hash_cpe = resultado.get('hash')
        venta.mensaje_sunat = resultado.get('mensaje')
        venta.estado = "ACEPTADO"
        db.session.commit()
        print("\nVenta actualizada en BD")
    else:
        print("ERROR")
        print(f"Mensaje: {resultado.get('mensaje')}")
        if resultado.get('error'):
            print(f"Detalle: {resultado.get('error')}")

        venta.estado = "RECHAZADO"
        venta.mensaje_sunat = resultado.get('mensaje', '') or resultado.get('error', '')
        db.session.commit()

print("\n" + "=" * 60)
