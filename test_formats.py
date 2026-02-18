from app import app, db, Venta
from mipse_service import MiPSEService
import json
import requests

venta_id = 6

with app.app_context():
    venta = Venta.query.get(venta_id)
    if not venta:
        print(f"Venta {venta_id} no encontrada")
        exit()

    service = MiPSEService()
    tipo_doc = "03" if not (venta.serie and venta.serie.startswith('F')) else "01"
    correlativo = str(venta.correlativo).zfill(8)
    ruc = service.ruc
    serie = venta.serie

    # Diferentes formatos a probar
    formatos = [
        f"{ruc}-{tipo_doc}-{serie}-{correlativo}", # Actual
        f"{tipo_doc}-{serie}-{correlativo}",
        f"{serie}-{correlativo}",
        f"{ruc}-{serie}-{correlativo}",
    ]

    print(f"--- TESTING CONSULTATION FORMATS FOR {serie}-{correlativo} ---")
    
    headers = service._get_headers()
    
    for fmt in formatos:
        url = f"{service.url}/pro/{service.system}/cpe/consultar/{fmt}"
        print(f"\nProbando: {fmt}")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            try:
                data = response.json()
                print(f"Success in Body: {data.get('success')}")
                print(f"Estado en Body: {data.get('estado')}")
                print(f"Mensaje: {data.get('mensaje')}")
                if data.get('cdr'):
                    print("!!! CDR ENCONTRADO (Largo: {} bytes)".format(len(data.get('cdr'))))
                if data.get('xml'):
                    print("!!! XML ENCONTRADO (Largo: {} bytes)".format(len(data.get('xml'))))
            except:
                print(f"Response text: {response.text[:200]}")
        except Exception as e:
            print(f"Error: {str(e)}")
