from app import app, db, Venta
from mipse_service import MiPSEService
import json
import requests

with app.app_context():
    # Obtener las ultimas 3 ventas enviadas
    ventas = Venta.query.filter(Venta.estado == 'ENVIADO').order_by(Venta.id.desc()).limit(3).all()
    
    if not ventas:
        print("No hay ventas ENVIADAS para probar")
        exit()

    service = MiPSEService()
    headers = service._get_headers()
    
    # Probar con URL alternativa de Postman
    alt_url = "https://app.mipse.pe"
    
    print(f"--- TESTING ALTERNATIVE URL: {alt_url} ---")
    
    for venta in ventas:
        tipo_doc = "03" if not (venta.serie and venta.serie.startswith('F')) else "01"
        correlativo = str(venta.correlativo).zfill(8)
        ruc = service.ruc
        serie = venta.serie
        
        fmt = f"{ruc}-{tipo_doc}-{serie}-{correlativo}"
        url = f"{alt_url}/pro/{service.system}/cpe/consultar/{fmt}"
        
        print(f"\nConsultando {serie}-{correlativo} en {url}")
        try:
            response = requests.get(url, headers=headers, timeout=20)
            print(f"  Status: {response.status_code}")
            try:
                data = response.json()
                print(f"  Estado Body: {data.get('estado')}")
                print(f"  Mensaje: {data.get('mensaje')}")
                if data.get('estado') == 200:
                    print("  !!! EXITO EN URL ALTERNATIVA !!!")
            except:
                print(f"  Response: {response.text[:100]}")
        except Exception as e:
            print(f"  Error: {str(e)}")
