"""
Verificación final de configuración antes de enviar a SUNAT
"""

from config import Config
import os

print("="*70)
print("VERIFICACIÓN FINAL DE CONFIGURACIÓN")
print("="*70)

config = Config()

print(f"\n✅ AMBIENTE: {config.SUNAT_AMBIENTE}")
print(f"\n📋 EMPRESA:")
print(f"   RUC: {config.EMPRESA_RUC}")
print(f"   Razón Social: {config.EMPRESA_RAZON_SOCIAL}")
print(f"   Nombre Comercial: {config.EMPRESA_NOMBRE_COMERCIAL}")

print(f"\n🔐 CREDENCIALES SUNAT:")
print(f"   RUC: {config.SUNAT_RUC}")
print(f"   Usuario SOL: {config.SUNAT_USUARIO_SOL}")
print(f"   Clave SOL: {'*' * len(config.SUNAT_CLAVE_SOL)}")

print(f"\n🌐 URL SUNAT:")
if config.SUNAT_AMBIENTE == 'PRODUCCION':
    print(f"   Servicio: {config.SUNAT_URL_PRODUCCION}")
    print(f"   WSDL: {config.SUNAT_WSDL_PRODUCCION}")
else:
    print(f"   Servicio: {config.SUNAT_URL_BETA}")
    print(f"   WSDL: {config.SUNAT_WSDL_BETA}")

print(f"\n📜 CERTIFICADO:")
print(f"   Ruta: {config.CERT_PATH}")
print(f"   Existe: {'✅ SÍ' if os.path.exists(config.CERT_PATH) else '❌ NO'}")

if os.path.exists(config.CERT_PATH):
    size = os.path.getsize(config.CERT_PATH)
    print(f"   Tamaño: {size} bytes")

    # Verificar que se pueda leer
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
        from cryptography.hazmat.backends import default_backend

        with open(config.CERT_PATH, 'rb') as f:
            pfx_data = f.read()

        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
            pfx_data,
            config.CERT_PASSWORD.encode() if config.CERT_PASSWORD else None,
            backend=default_backend()
        )

        print(f"   Contraseña: ✅ CORRECTA")
        print(f"   Estado: ✅ VÁLIDO")

        # Obtener info del certificado
        subject = certificate.subject
        issuer = certificate.issuer

        print(f"\n   📄 Detalles del certificado:")
        for attr in subject:
            print(f"      {attr.oid._name}: {attr.value}")

        print(f"\n   📅 Validez:")

        # Usar las propiedades UTC para evitar warnings
        not_before = certificate.not_valid_before_utc
        not_after = certificate.not_valid_after_utc

        print(f"      Desde: {not_before}")
        print(f"      Hasta: {not_after}")

        # Verificar si está vigente
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        if now < not_before:
            print(f"   ⚠️  Certificado aún no es válido")
        elif now > not_after:
            print(f"   ❌ Certificado EXPIRADO")
        else:
            days_left = (not_after - now).days
            print(f"   ✅ Certificado VIGENTE ({days_left} días restantes)")

    except ValueError as e:
        print(f"   ❌ Contraseña INCORRECTA")
    except Exception as e:
        print(f"   ❌ Error al leer certificado: {e}")

else:
    print(f"   ❌ Archivo no encontrado")

print(f"\n📁 CARPETAS:")
carpetas = ['xml_generados', 'cdr_recibidos', 'comprobantes']
for carpeta in carpetas:
    existe = os.path.exists(carpeta)
    print(f"   {carpeta}: {'✅' if existe else '❌ NO EXISTE'}")

print(f"\n{'='*70}")
print("CHECKLIST FINAL")
print('='*70)

checks = []

# Verificar todo
checks.append(("Certificado existe", os.path.exists(config.CERT_PATH)))
checks.append(("Usuario SOL configurado", bool(config.SUNAT_USUARIO_SOL)))
checks.append(("Clave SOL configurada", bool(config.SUNAT_CLAVE_SOL)))
checks.append(("Carpetas creadas", all(os.path.exists(c) for c in carpetas)))

all_ok = all(status for _, status in checks)

for item, status in checks:
    symbol = "✅" if status else "❌"
    print(f"{symbol} {item}")

print(f"\n{'='*70}")

if all_ok:
    print("🎉 TODO LISTO PARA ENVIAR A SUNAT")
    print("\nEjecuta: python app.py")
    print("Luego ve a http://localhost:5000 y envía una boleta")
else:
    print("⚠️  Hay configuraciones pendientes (revisa arriba)")

print('='*70)
