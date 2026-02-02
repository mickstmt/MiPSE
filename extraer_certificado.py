"""
Script para extraer el certificado público (.cer) desde el archivo .pfx
Este archivo .cer es el que debes subir a SUNAT
"""

from cryptography.hazmat.primitives.serialization import pkcs12, Encoding
from cryptography.hazmat.backends import default_backend
import os

# Configuración
PFX_PATH = "certificados/CT2510134109.pfx"
PFX_PASSWORD = os.getenv('CERT_PASSWORD', 'tu_contraseña_aqui')
CER_OUTPUT = "certificados/CT2510134109.cer"

def extraer_certificado():
    """Extrae el certificado público en formato .cer desde el .pfx"""

    print("=" * 60)
    print("EXTRACCIÓN DE CERTIFICADO PÚBLICO (.cer) DESDE .pfx")
    print("=" * 60)

    # Verificar que existe el archivo .pfx
    if not os.path.exists(PFX_PATH):
        print(f"❌ Error: No se encuentra el archivo {PFX_PATH}")
        return

    print(f"\n📂 Leyendo archivo: {PFX_PATH}")

    # Leer el archivo .pfx
    with open(PFX_PATH, 'rb') as f:
        pfx_data = f.read()

    print(f"✅ Archivo .pfx leído correctamente ({len(pfx_data)} bytes)")

    # Cargar el certificado desde el .pfx
    print(f"\n🔐 Extrayendo certificado con contraseña...")

    try:
        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
            pfx_data,
            PFX_PASSWORD.encode(),
            backend=default_backend()
        )

        print(f"✅ Certificado extraído correctamente")

        # Información del certificado
        print(f"\n📋 Información del certificado:")
        print(f"   Subject: {certificate.subject}")
        print(f"   Issuer: {certificate.issuer}")
        print(f"   Válido desde: {certificate.not_valid_before_utc}")
        print(f"   Válido hasta: {certificate.not_valid_after_utc}")

        # Exportar el certificado en formato DER (.cer)
        cert_bytes = certificate.public_bytes(Encoding.DER)

        # Guardar el archivo .cer
        with open(CER_OUTPUT, 'wb') as f:
            f.write(cert_bytes)

        print(f"\n✅ Certificado público guardado en: {CER_OUTPUT}")
        print(f"   Tamaño: {len(cert_bytes)} bytes")

        print("\n" + "=" * 60)
        print("SIGUIENTE PASO:")
        print("=" * 60)
        print(f"1. Ve a la carpeta 'certificados'")
        print(f"2. Busca el archivo: CT2510134109.cer")
        print(f"3. Sube ese archivo a SUNAT en la sección:")
        print(f"   'Registro y Mantenimiento de Correo y Certificados Digitales'")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error al extraer certificado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extraer_certificado()
