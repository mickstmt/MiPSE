"""
Script para cambiar el ambiente de SUNAT a BETA
"""
import os
from dotenv import load_dotenv, set_key

# Ruta al archivo .env
env_path = '.env'

print("=" * 70)
print("  CAMBIAR AMBIENTE A BETA (PRUEBAS)")
print("=" * 70)

# Verificar si existe el archivo .env
if not os.path.exists(env_path):
    print(f"❌ No se encontró el archivo {env_path}")
    exit(1)

print(f"\n📝 Actualizando {env_path}...")

# Actualizar la variable SUNAT_AMBIENTE
set_key(env_path, 'SUNAT_AMBIENTE', 'BETA')

print("✅ Variable SUNAT_AMBIENTE actualizada a: BETA")

# Recargar las variables de entorno
load_dotenv(override=True)

# Verificar el cambio
ambiente = os.getenv('SUNAT_AMBIENTE')
print(f"\n✅ Ambiente actual: {ambiente}")

if ambiente == 'BETA':
    print("\n✅ MODO PRUEBAS:")
    print("   - Estás en modo BETA")
    print("   - Los comprobantes enviados son de PRUEBA")
    print("   - URL: https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService")
else:
    print("\n⚠️  El ambiente sigue en PRODUCCION")

print("\n" + "=" * 70)
