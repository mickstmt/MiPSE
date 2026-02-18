from app import app, db, Venta
from mipse_service import MiPSEService
import json

venta_id = 6 # De la captura del usuario

with app.app_context():
    venta = Venta.query.get(venta_id)
    if not venta:
        print(f"Venta {venta_id} no encontrada")
        exit()

    print(f"--- DEBUG RECOVERY FOR SALE {venta.numero_completo} ---")
    service = MiPSEService()
    
    tipo_doc = "03" if not (venta.serie and venta.serie.startswith('F')) else "01"
    correlativo = str(venta.correlativo).zfill(8)
    nombre_archivo = f"{app.config['EMPRESA_RUC']}-{tipo_doc}-{venta.serie}-{correlativo}"
    
    print(f"Consultando MiPSE para: {nombre_archivo}")
    resultado = service.consultar_estado(nombre_archivo)
    
    print(f"Resultado success: {resultado.get('success')}")
    print(f"Estado retornado: {resultado.get('estado')}")
    print(f"Mensaje retornado: {resultado.get('mensaje')}")
    
    if resultado.get('data'):
        print("Estructura DATA completa (resumida):")
        data = resultado.get('data')
        for key in data.keys():
            val = data[key]
            if isinstance(val, str) and len(val) > 50:
                print(f"  - {key}: [Largo: {len(val)} bytes]")
            else:
                print(f"  - {key}: {val}")
    else:
        print("No hay DATA en el resultado")
        print(f"Error: {resultado.get('error')}")
