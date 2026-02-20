import sys
import os
import pandas as pd
from app import app, db
from models import Venta
from datetime import datetime

def update_fechas_desde_excel(file_path):
    if not os.path.exists(file_path):
        print(f"Error: El archivo '{file_path}' no existe.")
        return

    print(f"Leyendo Excel: {file_path} ...")
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return

    print("Actualizando fechas de pedido en la base de datos...")
    
    with app.app_context():
        actualizados = 0
        no_encontrados = 0
        
        # Agrupar por Numero de Orden (Columna E o index 4) para hacerlo más rápido
        # Usamos row.iloc para no depender de nombres de columnas que pueden variar levemente
        for index, row in df.iterrows():
            try:
                order_num = str(row.iloc[4]).strip() if not pd.isna(row.iloc[4]) else ""
                
                if not order_num:
                    continue
                
                # Extraer Fecha (Columna D - index 3)
                fecha_excel = None
                if not pd.isna(row.iloc[3]):
                    try:
                        # Convertir a datetime de pandas y luego a string SQL
                        fecha_desc = pd.to_datetime(row.iloc[3])
                        fecha_excel = fecha_desc.to_pydatetime()
                    except Exception:
                        # Fallback por si acaso es formato string no estándar
                        fecha_str = str(row.iloc[3]).strip()
                        try:
                            fecha_excel = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                        except:
                            print(f"  [!] No se pudo parsear la fecha de la orden {order_num}: {fecha_str}")
                
                if not fecha_excel:
                    continue
                
                # Buscar venta en DB
                venta = Venta.query.filter_by(numero_orden=order_num).first()
                if venta:
                    # Sólo actualizar si no tenía fecha o vamos a forzarla
                    if venta.fecha_pedido is None or venta.fecha_pedido != fecha_excel:
                        venta.fecha_pedido = fecha_excel
                        actualizados += 1
                else:
                    no_encontrados += 1
                    
            except Exception as e:
                print(f"  [-] Error procesando fila {index}: {e}")

        # Guardar cambios
        if actualizados > 0:
            db.session.commit()
            print(f"\n¡Éxito! Se actualizaron {actualizados} filas/ventas en la base de datos.")
            if no_encontrados > 0:
                print(f"Nota: Hubo {no_encontrados} filas en el Excel que no corresponden a ventas registradas.")
        else:
            print("\nNo se encontraron ventas para actualizar o ya estaban todas actualizadas.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python actualizar_fechas_excel.py <ruta_del_archivo.xlsx>")
        sys.exit(1)
        
    archivo_excel = sys.argv[1]
    update_fechas_desde_excel(archivo_excel)
