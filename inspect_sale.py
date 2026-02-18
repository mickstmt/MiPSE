from app import app, db, Venta
import json

venta_id = 6

with app.app_context():
    venta = Venta.query.get(venta_id)
    if not venta:
        print(f"Venta {venta_id} no encontrada")
    else:
        print(f"--- DATABASE RECORD FOR SALE {venta.id} ({venta.numero_completo}) ---")
        print(f"Estado: {venta.estado}")
        print(f"XML Path: {venta.xml_path}")
        print(f"CDR Path: {venta.cdr_path}")
        print(f"Hash: {venta.hash_cpe}")
        print(f"Mensaje SUNAT: {venta.mensaje_sunat}")
        print(f"Fecha Envío: {venta.fecha_envio_sunat}")
