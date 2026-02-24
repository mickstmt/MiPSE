"""
Script para cambiar el ambiente de SUNAT a PRODUCCION
"""
import os
from dotenv import load_dotenv, set_key

# Ruta al archivo .env
env_path = '.env'

print("=" * 70)
print("  CAMBIAR AMBIENTE A PRODUCCIÓN")
print("=" * 70)

# Verificar si existe el archivo .env
if not os.path.exists(env_path):
    print(f"❌ No se encontró el archivo {env_path}")
    exit(1)

print(f"\n📝 Actualizando {env_path}...")

# Actualizar la variable SUNAT_AMBIENTE
set_key(env_path, 'SUNAT_AMBIENTE', 'PRODUCCION')

print("✅ Variable SUNAT_AMBIENTE actualizada a: PRODUCCION")

# Recargar las variables de entorno
load_dotenv(override=True)

# Verificar el cambio
ambiente = os.getenv('SUNAT_AMBIENTE')
print(f"\n✅ Ambiente actual: {ambiente}")

if ambiente == 'PRODUCCION':
    print("\n⚠️  IMPORTANTE:")
    print("   - Estás en modo PRODUCCIÓN")
    print("   - Los comprobantes enviados serán REALES")
    print("   - Asegúrate de tener tus credenciales correctas")
    print("   - URL: https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService")
else:
    print("\n⚠️  El ambiente sigue en BETA")

print("\n" + "=" * 70)
