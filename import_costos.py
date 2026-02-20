"""
Script para importar costos de productos desde Excel a PostgreSQL.
Tabla destino: costos_productos
Columnas del Excel: SKU, DESCRIPCION, COLOR, SIZE, FCLastCost

Uso:
    python import_costos.py ruta/al/archivo.xlsx

Si no se pasa argumento, busca 'costos.xlsx' en el directorio actual.
"""

import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIGURACIÓN (igual que config.py) ──────────────────────────
DB_USER     = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = quote_plus(os.getenv('DB_PASSWORD', ''))
DB_HOST     = os.getenv('DB_HOST', 'izi-fact-db')
DB_PORT     = os.getenv('DB_PORT', '5432')
DB_NAME     = os.getenv('DB_NAME', 'iziFact')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"🔌 Conectando a: {DB_HOST}:{DB_PORT}/{DB_NAME}")

# ─── ARCHIVO EXCEL ────────────────────────────────────────────────
archivo = sys.argv[1] if len(sys.argv) > 1 else 'costos.xlsx'
if not os.path.exists(archivo):
    print(f"❌ Archivo no encontrado: {archivo}")
    sys.exit(1)

# ─── LECTURA DEL EXCEL ────────────────────────────────────────────
print(f"📂 Leyendo archivo: {archivo}...")
df = pd.read_excel(archivo)
print(f"   Columnas encontradas: {list(df.columns)}")
print(f"   Total de filas: {len(df)}")

# Normalizar nombres de columnas (quitar espacios, mayúsculas)
df.columns = [c.strip().upper() for c in df.columns]

# Verificar columnas requeridas
requeridas = ['SKU', 'DESC', 'FCLASTCOST']
for col in requeridas:
    if col not in df.columns:
        print(f"❌ Columna requerida no encontrada: '{col}'")
        print(f"   Columnas disponibles: {list(df.columns)}")
        sys.exit(1)

# El Excel ya tiene los nombres correctos para la DB.
# Solo renombramos FCLastCost → costo y convertimos a numérico.
df_import = df.rename(columns={'FCLASTCOST': 'costo'}).copy()

# Limpiar todos los campos de texto
for col in df_import.select_dtypes(include='object').columns:
    df_import[col] = df_import[col].astype(str).str.strip()

# Asegurar que costo sea numérico
df_import['costo'] = pd.to_numeric(df_import['costo'], errors='coerce').fillna(0.0)

# Columnas en minúsculas para que coincidan con PostgreSQL
df_import.columns = [c.lower() for c in df_import.columns]

# Quitar filas con SKU vacío o 'NAN'
df_import = df_import[df_import['sku'].notna() & (df_import['sku'] != 'nan') & (df_import['sku'] != '')]
print(f"   Filas válidas para importar: {len(df_import)}")
print(f"   Columnas a insertar: {list(df_import.columns)}")

# ─── CARGA A POSTGRESQL ───────────────────────────────────────────
print("🔄 Conectando a la base de datos...")
engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    print("   Recreando tabla 'costos_productos'...")
    df_import.to_sql(
        'costos_productos',
        con=conn,
        if_exists='replace',   # Borra y recrea la tabla con las columnas del Excel
        index=False,
        method='multi',
        chunksize=500
    )
    # Agregar columna id serial autoincremental al inicio
    conn.execute(text("ALTER TABLE costos_productos ADD COLUMN IF NOT EXISTS id SERIAL;"))
    # Hacer que sea PRIMARY KEY
    conn.execute(text("""
        ALTER TABLE costos_productos 
        DROP CONSTRAINT IF EXISTS costos_productos_pkey;
    """))
    conn.execute(text("""
        ALTER TABLE costos_productos 
        ADD CONSTRAINT costos_productos_pkey PRIMARY KEY (id);
    """))

print(f"✅ ¡Importación completada! {len(df_import)} registros cargados en 'costos_productos'.")
print("\nPrimeros registros importados:")
print(df_import.head(5).to_string(index=False))
