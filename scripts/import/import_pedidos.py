"""
Script para actualizar fecha_pedido y costo_envio en la tabla ventas
desde un archivo Excel, haciendo match por numero_orden.

Columnas esperadas en el Excel (sin importar mayúsculas/acentos):
  - "Numero de orden"    → numero_orden (clave de búsqueda)
  - "Fecha de creacion"  → fecha_pedido
  - "Costo de envio"     → costo_envio

Uso:
    python import_pedidos.py ruta/al/archivo.xlsx
    python import_pedidos.py               # busca 'pedidos.xlsx' en el directorio actual
"""

import sys
import os
import re
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIGURACIÓN ────────────────────────────────────────────────
DB_USER     = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = quote_plus(os.getenv('DB_PASSWORD', ''))
DB_HOST     = os.getenv('DB_HOST', 'izi-fact-db')
DB_PORT     = os.getenv('DB_PORT', '5432')
DB_NAME     = os.getenv('DB_NAME', 'iziFact')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"🔌 Conectando a: {DB_HOST}:{DB_PORT}/{DB_NAME}")

# ─── ARCHIVO EXCEL ────────────────────────────────────────────────
archivo = sys.argv[1] if len(sys.argv) > 1 else 'pedidos.xlsx'
if not os.path.exists(archivo):
    print(f"❌ Archivo no encontrado: {archivo}")
    sys.exit(1)

# ─── LECTURA DEL EXCEL ────────────────────────────────────────────
print(f"📂 Leyendo archivo: {archivo}...")
df = pd.read_excel(archivo)
print(f"   Columnas encontradas: {list(df.columns)}")
print(f"   Total de filas: {len(df)}")


def normalizar(nombre):
    """Quita acentos, espacios extra y pasa a minúsculas para comparar."""
    s = str(nombre).strip().lower()
    s = re.sub(r'[áàä]', 'a', s)
    s = re.sub(r'[éèë]', 'e', s)
    s = re.sub(r'[íìï]', 'i', s)
    s = re.sub(r'[óòö]', 'o', s)
    s = re.sub(r'[úùü]', 'u', s)
    s = re.sub(r'\s+', ' ', s)
    return s


# Mapa: columna normalizada → nombre original
col_map = {normalizar(c): c for c in df.columns}

# Buscar cada columna requerida por nombre normalizado
def buscar_col(clave):
    k = normalizar(clave)
    if k in col_map:
        return col_map[k]
    # Búsqueda parcial por si el nombre es ligeramente diferente
    for norm, orig in col_map.items():
        if k in norm or norm in k:
            return orig
    return None

col_orden  = buscar_col('numero de orden')
col_fecha  = buscar_col('fecha de creacion')
col_envio  = buscar_col('costo de envio')

faltantes = []
if not col_orden:  faltantes.append('"Numero de orden"')
if not col_fecha:  faltantes.append('"Fecha de creacion"')
if not col_envio:  faltantes.append('"Costo de envio"')

if faltantes:
    print(f"❌ No se encontraron columnas requeridas: {', '.join(faltantes)}")
    print(f"   Columnas disponibles: {list(df.columns)}")
    sys.exit(1)

print(f"   ✓ Columna orden  → '{col_orden}'")
print(f"   ✓ Columna fecha  → '{col_fecha}'")
print(f"   ✓ Columna envío  → '{col_envio}'")

# ─── PREPARAR DATOS ───────────────────────────────────────────────
df_work = df[[col_orden, col_fecha, col_envio]].copy()
df_work.columns = ['numero_orden', 'fecha_pedido', 'costo_envio']

# Limpiar numero_orden: convertir a string limpio
df_work['numero_orden'] = df_work['numero_orden'].astype(str).str.strip()
df_work['numero_orden'] = df_work['numero_orden'].apply(
    lambda x: str(int(float(x))) if re.match(r'^\d+\.0$', x) else x
)

# Parsear fecha_pedido a datetime (acepta múltiples formatos de Excel)
df_work['fecha_pedido'] = pd.to_datetime(df_work['fecha_pedido'], errors='coerce')

# Limpiar costo_envio a float
df_work['costo_envio'] = pd.to_numeric(df_work['costo_envio'], errors='coerce').fillna(0.0)

# Quitar filas sin numero_orden válido
df_work = df_work[df_work['numero_orden'].notna() & (df_work['numero_orden'] != '') & (df_work['numero_orden'] != 'nan')]

filas_con_fecha = df_work['fecha_pedido'].notna().sum()
filas_sin_fecha = df_work['fecha_pedido'].isna().sum()
print(f"\n   Filas válidas para actualizar: {len(df_work)}")
print(f"   Con fecha válida: {filas_con_fecha} | Sin fecha (se omitirá ese campo): {filas_sin_fecha}")

# ─── ACTUALIZACIÓN EN POSTGRESQL ──────────────────────────────────
print("\n🔄 Conectando a la base de datos...")
engine = create_engine(DATABASE_URL)

actualizadas = 0
no_encontradas = []

with engine.begin() as conn:
    for _, row in df_work.iterrows():
        numero_orden = row['numero_orden']
        fecha        = row['fecha_pedido']
        costo_envio  = float(row['costo_envio'])

        # Construir la actualización según si tenemos fecha válida o no
        if pd.notna(fecha):
            result = conn.execute(text("""
                UPDATE ventas
                SET fecha_pedido = :fecha,
                    costo_envio  = :costo_envio
                WHERE numero_orden = :numero_orden
            """), {
                'fecha':        fecha.to_pydatetime(),
                'costo_envio':  costo_envio,
                'numero_orden': numero_orden,
            })
        else:
            result = conn.execute(text("""
                UPDATE ventas
                SET costo_envio = :costo_envio
                WHERE numero_orden = :numero_orden
            """), {
                'costo_envio':  costo_envio,
                'numero_orden': numero_orden,
            })

        if result.rowcount > 0:
            actualizadas += 1
        else:
            no_encontradas.append(numero_orden)

print(f"\n✅ Actualización completada.")
print(f"   Ventas actualizadas : {actualizadas}")
print(f"   Órdenes no halladas : {len(no_encontradas)}")

if no_encontradas:
    print("\n⚠️  Órdenes del Excel sin coincidencia en la BD:")
    for o in no_encontradas[:20]:
        print(f"   - {o}")
    if len(no_encontradas) > 20:
        print(f"   ... y {len(no_encontradas) - 20} más")
