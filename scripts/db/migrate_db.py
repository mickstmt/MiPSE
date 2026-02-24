import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'iziFact'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        cur = conn.cursor()
        
        print("Checking for missing columns in 'ventas' table...")
        
        # Agregar external_id
        try:
            cur.execute("ALTER TABLE ventas ADD COLUMN external_id VARCHAR(100);")
            print("✅ Column 'external_id' added successfully.")
        except psycopg2.errors.DuplicateColumn:
            conn.rollback()
            print("ℹ Column 'external_id' already exists.")
        except Exception as e:
            conn.rollback()
            print(f"❌ Error adding 'external_id': {e}")

        conn.commit()
        cur.close()
        conn.close()
        print("Migration finished.")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    migrate()
