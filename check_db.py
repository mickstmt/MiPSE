from app import app, db, Venta
from datetime import datetime

with app.app_context():
    print("--- RECENT SALES CHECK ---")
    ventas = Venta.query.order_by(Venta.id.desc()).limit(5).all()
    for v in ventas:
        print(f"ID: {v.id} | Num: {v.numero_completo} | Status: {v.estado} | Date: {v.fecha_emision}")
        print(f"  XML Path: {v.xml_path}")
        print(f"  CDR Path: {v.cdr_path}")
        print(f"  PDF Path: {v.pdf_path}")
        print("-" * 30)
