from app import app, db, Venta
from mipse_service import MiPSEService
import json
import requests

with app.app_context():
    # Probar con varios IDs
    ids = [1, 2, 3, 4, 5, 6]
    
    service = MiPSEService()
    headers = service._get_headers()
    ruc = service.ruc
    
    print(f"--- BATCH CONSULTATION TEST ---")
    
    for vid in ids:
        venta = Venta.query.get(vid)
        if not venta: continue
        
        tipo_doc = "03" if not (venta.serie and venta.serie.startswith('F')) else "01"
        fmt = f"{ruc}-{tipo_doc}-{venta.serie}-{str(venta.correlativo).zfill(8)}"
        url = f"{service.url}/pro/{service.system}/cpe/consultar/{fmt}"
        
        print(f"\nID: {vid} | {venta.numero_completo} | {fmt}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {response.status_code} | Body: {response.text[:50]}")
        except:
            print("  Error")
