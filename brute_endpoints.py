from app import app, db, Venta
from mipse_service import MiPSEService
import json
import requests

venta_id = 6

with app.app_context():
    venta = Venta.query.get(venta_id)
    service = MiPSEService()
    headers = service._get_headers()
    
    tipo_doc = "03" if not (venta.serie and venta.serie.startswith('F')) else "01"
    correlativo = str(venta.correlativo).zfill(8)
    ruc = service.ruc
    serie = venta.serie
    
    nombre_archivo = f"{ruc}-{tipo_doc}-{serie}-{correlativo}"
    
    # Endpoints a probar
    endpoints = [
        "cpe/consultar",
        "cpe/estado",
        "cpe/ver",
        "cpe/detalle",
        "cpe/buscar",
        "cpe/descargar",
        "comprobante/consultar",
        "comprobante/estado"
    ]
    
    print(f"--- BRUTE-FORCING ENDPOINTS FOR {nombre_archivo} ---")
    
    for ep in endpoints:
        url = f"{service.url}/pro/{service.system}/{ep}/{nombre_archivo}"
        print(f"\nProbando: {ep}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print("  !!! POSIBLE EXITO (200) !!!")
                print(f"  Body: {response.text[:200]}")
            elif response.status_code == 202:
                print("  Accepted (202) - body: {}".format(response.text[:100]))
        except:
            print("  Error de conexion")
