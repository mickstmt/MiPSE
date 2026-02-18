from app import app, db, Venta
from pdf_service import generar_pdf_boleta
import os

def probar_pdf(venta_id):
    with app.app_context():
        venta = Venta.query.get(venta_id)
        if not venta:
            print(f"Venta {venta_id} no encontrada")
            return
            
        output_path = f"test_boleta_{venta_id}.pdf"
        print(f"Generando PDF para venta {venta.numero_completo}...")
        
        if generar_pdf_boleta(venta, output_path):
            print(f"✅ PDF generado exitosamente: {os.path.abspath(output_path)}")
        else:
            print("❌ Error al generar PDF")

if __name__ == "__main__":
    import sys
    vid = 7 # Por defecto probar con la 7
    if len(sys.argv) > 1:
        vid = int(sys.argv[1])
    probar_pdf(vid)
