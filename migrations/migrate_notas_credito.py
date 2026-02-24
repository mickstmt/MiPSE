"""
Migración: Agrega columnas para Notas de Crédito a la tabla ventas.

Nuevas columnas:
  - tipo_comprobante    VARCHAR(20) DEFAULT 'BOLETA'   ('BOLETA' | 'NOTA_CREDITO')
  - venta_referencia_id INTEGER (FK nullable → ventas.id)
  - motivo_nc_codigo    VARCHAR(5) nullable             (SUNAT catálogo 09)
  - motivo_nc_descripcion VARCHAR(255) nullable

Uso:
    python migrate_notas_credito.py
"""

import os
import sys
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_USER     = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = quote_plus(os.getenv('DB_PASSWORD', ''))
DB_HOST     = os.getenv('DB_HOST', 'izi-fact-db')
DB_PORT     = os.getenv('DB_PORT', '5432')
DB_NAME     = os.getenv('DB_NAME', 'iziFact')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"Conectando a: {DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = create_engine(DATABASE_URL)

MIGRATIONS = [
    (
        "tipo_comprobante",
        "ALTER TABLE ventas ADD COLUMN IF NOT EXISTS tipo_comprobante VARCHAR(20) DEFAULT 'BOLETA';"
    ),
    (
        "venta_referencia_id",
        "ALTER TABLE ventas ADD COLUMN IF NOT EXISTS venta_referencia_id INTEGER REFERENCES ventas(id);"
    ),
    (
        "motivo_nc_codigo",
        "ALTER TABLE ventas ADD COLUMN IF NOT EXISTS motivo_nc_codigo VARCHAR(5);"
    ),
    (
        "motivo_nc_descripcion",
        "ALTER TABLE ventas ADD COLUMN IF NOT EXISTS motivo_nc_descripcion VARCHAR(255);"
    ),
]

with engine.begin() as conn:
    for col_name, sql in MIGRATIONS:
        try:
            conn.execute(text(sql))
            print(f"  OK  columna '{col_name}' agregada (o ya existia)")
        except Exception as e:
            print(f"  ERROR en '{col_name}': {e}")
            sys.exit(1)

print("\nMigracion completada exitosamente.")
