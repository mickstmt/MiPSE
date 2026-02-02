"""
Diagnóstico de credenciales y permisos SUNAT
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

print("=" * 70)
print("  DIAGNÓSTICO DE CONFIGURACIÓN SUNAT")
print("=" * 70)

# Leer variables de entorno
ruc = os.getenv('SUNAT_RUC', 'NO CONFIGURADO')
usuario_sol = os.getenv('SUNAT_USUARIO_SOL', 'NO CONFIGURADO')
clave_sol = os.getenv('SUNAT_CLAVE_SOL', 'NO CONFIGURADO')
ambiente = os.getenv('SUNAT_AMBIENTE', 'BETA')
cert_path = os.getenv('CERT_PATH', 'NO CONFIGURADO')
cert_password = os.getenv('CERT_PASSWORD', 'NO CONFIGURADO')

print(f"\n📋 CONFIGURACIÓN ACTUAL:")
print(f"   RUC: {ruc}")
print(f"   Usuario SOL: {usuario_sol}")
print(f"   Clave SOL: {'*' * len(clave_sol) if clave_sol != 'NO CONFIGURADO' else 'NO CONFIGURADO'}")
print(f"   Ambiente: {ambiente}")
print(f"   Certificado: {cert_path}")
print(f"   Password Cert: {'*' * len(cert_password) if cert_password != 'NO CONFIGURADO' else 'NO CONFIGURADO'}")

# Verificar si el certificado existe
if os.path.exists(cert_path):
    print(f"\n✅ Certificado encontrado: {cert_path}")
    file_size = os.path.getsize(cert_path)
    print(f"   Tamaño: {file_size} bytes")
else:
    print(f"\n❌ Certificado NO encontrado: {cert_path}")

print("\n" + "=" * 70)
print("  ANÁLISIS DEL ERROR")
print("=" * 70)

print("""
❌ Error recibido: "No tiene el perfil para enviar comprobantes electronicos"
   Código: soap-env:Client.0111

🔍 POSIBLES CAUSAS:

1. USUARIO SOL NO HABILITADO EN PRODUCCIÓN:
   - El usuario SOL debe estar habilitado específicamente para producción
   - Verifica en SUNAT Operaciones en Línea que tu usuario tenga permisos
   - URL: https://www.sunat.gob.pe/

2. USUARIO SOL INCORRECTO:
   - El formato debe ser: [RUC][USUARIO]
   - Ejemplo: 10433050709VOTROEXP
   - Verifica que coincida con lo registrado en SUNAT

3. CLAVE SOL INCORRECTA:
   - Verifica que la clave sea la correcta
   - Si la cambiaste recientemente, actualiza el .env

4. AMBIENTE BETA vs PRODUCCIÓN:
   - Las credenciales de BETA no funcionan en PRODUCCIÓN
   - Necesitas credenciales específicas de producción

5. PERFIL NO ASIGNADO:
   - Debes solicitar a SUNAT que active tu RUC para facturación electrónica
   - Esto se hace a través de SUNAT Virtual

📝 SOLUCIONES RECOMENDADAS:

A. VERIFICAR EN SUNAT OPERACIONES EN LÍNEA:
   1. Ingresa a: https://www.sunat.gob.pe/
   2. Ve a "SUNAT Operaciones en Línea"
   3. Ingresa con tu Clave SOL
   4. Verifica que tengas el perfil de "Emisor Electrónico"

B. VERIFICAR USUARIO SOL:
   1. El usuario debe tener el formato: {ruc}{usuario_sol}
   2. Usuario actual: {usuario_sol}
   3. Verifica que sea correcto

C. SOLICITAR ACTIVACIÓN (si es necesario):
   1. Ingresa a SUNAT Virtual
   2. Solicita la activación del servicio de facturación electrónica
   3. Espera la confirmación de SUNAT

D. USAR AMBIENTE BETA PARA PRUEBAS:
   - Si aún no tienes permisos en producción
   - Cambia SUNAT_AMBIENTE=BETA en el .env
   - Continúa probando en el ambiente de pruebas

""")

print("=" * 70)
print("  RECOMENDACIÓN")
print("=" * 70)

if ambiente == 'PRODUCCION':
    print("""
⚠️  Mientras resuelves el problema de permisos:
   
   1. Cambia temporalmente a BETA:
      python cambiar_a_beta.py
   
   2. Verifica tus credenciales con SUNAT
   
   3. Una vez confirmado que tienes permisos, vuelve a PRODUCCION
""")
else:
    print("\n✅ Estás en modo BETA - Puedes continuar probando")

print("=" * 70)
