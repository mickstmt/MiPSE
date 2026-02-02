"""
Script para actualizar las credenciales de SUNAT
"""
import os
from dotenv import load_dotenv, set_key

# Ruta al archivo .env
env_path = '.env'

print("=" * 70)
print("  ACTUALIZAR CREDENCIALES SUNAT")
print("=" * 70)

# Verificar si existe el archivo .env
if not os.path.exists(env_path):
    print(f"❌ No se encontró el archivo {env_path}")
    exit(1)

print(f"\n📝 Actualizando credenciales en {env_path}...")

# Nuevas credenciales
nuevo_usuario = 'TU_USUARIO'
nueva_clave = 'TU_CLAVE'

# Actualizar las variables
set_key(env_path, 'SUNAT_USUARIO_SOL', nuevo_usuario)
set_key(env_path, 'SUNAT_CLAVE_SOL', nueva_clave)

print(f"✅ Usuario SOL actualizado a: {nuevo_usuario}")
print(f"✅ Clave SOL actualizada")

# Recargar las variables de entorno
load_dotenv(override=True)

# Verificar el cambio
usuario = os.getenv('SUNAT_USUARIO_SOL')
ruc = os.getenv('SUNAT_RUC')
ambiente = os.getenv('SUNAT_AMBIENTE', 'BETA')

print(f"\n📋 CONFIGURACIÓN ACTUALIZADA:")
print(f"   RUC: {ruc}")
print(f"   Usuario SOL: {usuario}")
print(f"   Formato completo: {ruc}{usuario}")
print(f"   Ambiente: {ambiente}")

print("\n✅ Credenciales actualizadas correctamente")
print("\n💡 Ahora puedes probar nuevamente con:")
print("   python crear_venta_prueba.py")

print("\n" + "=" * 70)
