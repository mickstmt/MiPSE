from app import app, db, Venta
from pdf_service import generar_pdf_boleta
import os

def probar_pdf(venta_id):
    with app.app_context():
        # Using Session.get() as per SQLAlchemy 2.0 recommendation
        venta = db.session.get(Venta, venta_id)
        if not venta:
            print(f"Venta {venta_id} no encontrada")
            return
            
        output_path = f"final_test_boleta_{venta_id}.pdf"
        print(f"Generando PDF corregido para venta {venta.numero_completo}...")
        
        if generar_pdf_boleta(venta, output_path):
            print(f"✅ PDF generado exitosamente: {os.path.abspath(output_path)}")
        else:
            print("❌ Error al generar PDF")

if __name__ == "__main__":
    import sys
    vid = 7
    if len(sys.argv) > 1:
        vid = int(sys.argv[1])
    probar_pdf(vid)
