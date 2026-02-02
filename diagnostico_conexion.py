"""
Diagnóstico completo de conectividad a SUNAT
"""

import socket
import ssl
import requests
from urllib.parse import urlparse

print("="*70)
print("DIAGNÓSTICO DE CONECTIVIDAD A SUNAT")
print("="*70)

# URLs a probar
urls_sunat = {
    'PRODUCCION': 'https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService?wsdl',
    'BETA': 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl'
}

def test_dns(hostname):
    """Probar resolución DNS"""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"   ✅ DNS OK - IP: {ip}")
        return True
    except Exception as e:
        print(f"   ❌ DNS FALLO: {e}")
        return False

def test_tcp_connection(hostname, port=443):
    """Probar conexión TCP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((hostname, port))
        sock.close()

        if result == 0:
            print(f"   ✅ Puerto {port} ABIERTO")
            return True
        else:
            print(f"   ❌ Puerto {port} CERRADO o BLOQUEADO")
            return False
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def test_ssl_connection(hostname, port=443):
    """Probar conexión SSL/TLS"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"   ✅ SSL/TLS OK - Protocolo: {ssock.version()}")
                return True
    except Exception as e:
        print(f"   ❌ SSL/TLS FALLO: {e}")
        return False

def test_http_request(url):
    """Probar request HTTP completo"""
    try:
        response = requests.get(url, timeout=15)
        print(f"   ✅ HTTP OK - Status: {response.status_code}")

        # Verificar si es WSDL válido
        if 'wsdl' in response.text.lower() or 'xml' in response.text.lower():
            print(f"   ✅ WSDL VÁLIDO - Tamaño: {len(response.text)} bytes")
            return True
        else:
            print(f"   ⚠️  Respuesta no parece ser WSDL")
            return False

    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT - La conexión tardó demasiado")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ ERROR DE CONEXIÓN: {e}")
        print(f"   💡 Posiblemente bloqueado por firewall")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

# Probar cada ambiente
for ambiente, url in urls_sunat.items():
    print(f"\n{'='*70}")
    print(f"🔍 Probando {ambiente}: {url}")
    print('='*70)

    parsed = urlparse(url)
    hostname = parsed.hostname

    print(f"\n1️⃣ Test DNS para '{hostname}':")
    dns_ok = test_dns(hostname)

    if dns_ok:
        print(f"\n2️⃣ Test conexión TCP puerto 443:")
        tcp_ok = test_tcp_connection(hostname, 443)

        if tcp_ok:
            print(f"\n3️⃣ Test SSL/TLS:")
            ssl_ok = test_ssl_connection(hostname, 443)

            if ssl_ok:
                print(f"\n4️⃣ Test HTTP Request (WSDL):")
                http_ok = test_http_request(url)

                if http_ok:
                    print(f"\n✅ TODAS LAS PRUEBAS PASARON PARA {ambiente}")
                else:
                    print(f"\n⚠️  HTTP request falló para {ambiente}")
            else:
                print(f"\n⚠️  SSL/TLS falló para {ambiente}")
        else:
            print(f"\n❌ No se pudo conectar al puerto 443")
            print(f"💡 PROBABLE CAUSA: Firewall bloqueando la conexión")
    else:
        print(f"\n❌ No se pudo resolver el DNS")

print(f"\n{'='*70}")
print("RESUMEN DE DIAGNÓSTICO")
print('='*70)

print("""
🔧 POSIBLES SOLUCIONES:

1. FIREWALL DE WINDOWS:
   - Abre PowerShell como Administrador
   - Ejecuta:
     New-NetFirewallRule -DisplayName "Python SUNAT" -Direction Outbound `
       -Program "C:\\Users\\FranksM\\sistema-ventas-izistore\\venv\\Scripts\\python.exe" `
       -Action Allow -Protocol TCP -RemotePort 443

2. ANTIVIRUS:
   - Agrega Python a la lista de exclusiones
   - Permite conexiones HTTPS salientes

3. PROXY CORPORATIVO:
   - Si estás en una red corporativa, configura el proxy
   - Consulta con tu administrador de red

4. VPN:
   - Si usas VPN, desactívala temporalmente para probar

5. FIREWALL DE TERCEROS:
   - Si tienes Norton, McAfee, Kaspersky, etc.
   - Permite Python en las reglas de firewall
""")

print('='*70)