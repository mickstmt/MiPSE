import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'izistore_ventas')

if not DB_PASSWORD:
    print("❌ ERROR: No se encontró DB_PASSWORD en el archivo .env")
    print("   Verifica que hayas creado el archivo .env y configurado la contraseña")
    exit(1)

try:
    print(f"🔄 Conectando a PostgreSQL en {DB_HOST}:{DB_PORT}...")
    
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cursor.fetchone()
    
    if exists:
        print(f"⚠️  La base de datos '{DB_NAME}' ya existe.")
    else:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
        print(f"✅ Base de datos '{DB_NAME}' creada exitosamente!")
    
    cursor.close()
    conn.close()
    
    print("\n✅ ¡Listo! Ahora ejecuta: python init_db.py")
    
except psycopg2.OperationalError as e:
    print(f"\n❌ Error de conexión:")
    print(f"   - Verifica que PostgreSQL esté corriendo")
    print(f"   - Verifica la contraseña en el archivo .env")
    print(f"   Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
