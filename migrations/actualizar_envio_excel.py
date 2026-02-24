import sys
import os
import pandas as pd
from app import app, db
from models import Venta

def update_envio_desde_excel(file_path):
    if not os.path.exists(file_path):
        print(f"Error: El archivo '{file_path}' no existe.")
        return

    print(f"Leyendo Excel: {file_path} ...")
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return

    print("Actualizando costos de envío en la base de datos...")
    
    with app.app_context():
        actualizados = 0
        no_encontrados = 0
        
        # Agrupar por Numero de Orden (Columna E o index 4) para hacerlo más rápido
        # Columna AL es index 37 (Costo del envio)
        for index, row in df.iterrows():
            try:
                order_num = str(row.iloc[4]).strip() if not pd.isna(row.iloc[4]) else ""
                
                if not order_num:
                    continue
                
                # Extraer envío
                costo_envio = 0.0
                if not pd.isna(row.iloc[37]):
                    try:
                        costo_envio = float(row.iloc[37])
                    except:
                        costo_envio = 0.0
                
                if costo_envio <= 0:
                    continue
                
                # Buscar venta en DB
                venta = Venta.query.filter_by(numero_orden=order_num).first()
                if venta:
                    # Sólo actualizar si no tenía costo_envio o vamos a forzarla
                    if venta.costo_envio != costo_envio:
                        venta.costo_envio = costo_envio
                        actualizados += 1
                else:
                    no_encontrados += 1
                    
            except Exception as e:
                print(f"  [-] Error procesando fila {index}: {e}")

        # Guardar cambios
        if actualizados > 0:
            db.session.commit()
            print(f"\n¡Éxito! Se actualizaron {actualizados} filas/ventas en la base de datos.")
        else:
            print("\nNo se encontraron ventas para actualizar o ya estaban todas actualizadas.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python actualizar_envio_excel.py <ruta_del_archivo.xlsx>")
        sys.exit(1)
        
    archivo_excel = sys.argv[1]
    update_envio_desde_excel(archivo_excel)
