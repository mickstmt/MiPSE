"""
Test para verificar la URL de SUNAT y el WSDL
"""

from config import Config
from zeep import Client
from zeep.transports import Transport
from requests import Session

print("="*60)
print("TEST DE CONEXIÓN A SUNAT")
print("="*60)

config = Config()

print(f"\n📋 Configuración:")
print(f"   Ambiente: {config.SUNAT_AMBIENTE}")
print(f"   RUC: {config.EMPRESA_RUC}")
print(f"   Usuario SOL: {config.SUNAT_USUARIO_SOL}")

if config.SUNAT_AMBIENTE == 'PRODUCCION':
    url = config.SUNAT_URL_PRODUCCION
    wsdl_url = config.SUNAT_WSDL_PRODUCCION
    print(f"\n🚀 Probando PRODUCCIÓN")
else:
    url = config.SUNAT_URL_BETA
    wsdl_url = config.SUNAT_WSDL_BETA
    print(f"\n🧪 Probando BETA")

print(f"   URL Servicio: {url}")
print(f"   URL WSDL: {wsdl_url}")

print(f"\n🔄 Intentando conectar al WSDL...")

try:
    # Configurar sesión
    session = Session()
    session.auth = (f"{config.EMPRESA_RUC}{config.SUNAT_USUARIO_SOL}", config.SUNAT_CLAVE_SOL)
    transport = Transport(session=session, timeout=30)

    # Intentar crear cliente
    client = Client(wsdl_url, transport=transport)

    print(f"✅ Conexión exitosa al WSDL!")
    print(f"\n📡 Servicios disponibles:")

    for service in client.wsdl.services.values():
        print(f"\n   Servicio: {service.name}")
        for port in service.ports.values():
            print(f"      Puerto: {port.name}")
            operations = list(port.binding._operations.keys())
            for op in operations:
                print(f"         • {op}")

    print(f"\n✅ TODO OK - Listo para enviar comprobantes")

except Exception as e:
    print(f"\n❌ ERROR al conectar:")
    print(f"   {type(e).__name__}: {str(e)}")
    print(f"\n🔍 Posibles causas:")
    print(f"   1. URL incorrecta")
    print(f"   2. Credenciales SOL incorrectas")
    print(f"   3. RUC no autorizado")
    print(f"   4. Firewall bloqueando la conexión")

print("\n" + "="*60)
