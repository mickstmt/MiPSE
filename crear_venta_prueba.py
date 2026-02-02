"""
Script para crear una venta de prueba y enviarla a SUNAT
"""
import os
import sys

# Configurar encoding para Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Forzar recarga del .env
from dotenv import load_dotenv
load_dotenv(override=True)

from datetime import datetime
from models import db, Venta, VentaItem, Cliente
from sunat_service import SUNATService
import config

# Conectar a la base de datos
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Crear conexión
engine = create_engine(config.Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 70)
print("  CREAR VENTA DE PRUEBA Y ENVIAR A SUNAT")
print("=" * 70)

# 1. Buscar o crear un cliente de prueba
cliente = session.query(Cliente).filter_by(numero_documento="12345678").first()
if not cliente:
    print("\n📝 Creando cliente de prueba...")
    cliente = Cliente(
        numero_documento="12345678",
        tipo_documento="DNI",
        nombres="CLIENTE DE PRUEBA",
        apellido_paterno="SUNAT",
        apellido_materno="TEST",
        direccion="Lima, Perú"
    )
    session.add(cliente)
    session.commit()
    print(f"✅ Cliente creado: {cliente.nombre_completo}")
else:
    print(f"\n✅ Cliente encontrado: {cliente.nombre_completo}")

# 2. Crear producto de prueba (simulado)
class ProductoPrueba:
    id = 999
    nombre = "PRODUCTO DE PRUEBA PARA SUNAT"
    precio = 50.00

producto = ProductoPrueba()
print(f"✅ Producto: {producto.nombre} - S/ {producto.precio}")

# 3. Obtener siguiente correlativo
ultima_venta = session.query(Venta).filter(
    Venta.serie == config.Config.SERIE_BOLETA
).order_by(Venta.correlativo.desc()).first()

if ultima_venta:
    siguiente_correlativo = int(ultima_venta.correlativo) + 1
else:
    siguiente_correlativo = 1

numero_completo = f"{config.Config.SERIE_BOLETA}-{siguiente_correlativo:08d}"

print(f"\n📄 Generando comprobante: {numero_completo}")

# 4. Crear la venta (necesitamos vendedor_id también)
# Obtener el primer usuario como vendedor
from models import Usuario
vendedor = session.query(Usuario).first()
if not vendedor:
    print("❌ No hay usuarios en la base de datos. Crea un usuario primero.")
    exit(1)

venta = Venta(
    cliente_id=cliente.id,
    vendedor_id=vendedor.id,
    fecha_emision=datetime.now(),
    serie=config.Config.SERIE_BOLETA,
    correlativo=str(siguiente_correlativo),
    subtotal=float(producto.precio) / 1.18,  # Sin IGV
    total=float(producto.precio),
    estado="PENDIENTE",
    numero_completo=numero_completo
)
session.add(venta)
session.flush()  # Para obtener el ID de la venta

# 5. Crear el item de venta
venta_item = VentaItem(
    venta_id=venta.id,
    producto_nombre=producto.nombre,
    cantidad=1,
    precio_unitario=float(producto.precio),
    subtotal=float(producto.precio)
)
session.add(venta_item)
session.commit()

print(f"✅ Venta creada: ID {venta.id}")
print(f"   Cliente: {cliente.nombre_completo}")
print(f"   Producto: {producto.nombre}")
print(f"   Total: S/ {venta.total}")

# 6. Enviar a SUNAT
print("\n" + "=" * 70)
print("  ENVIANDO A SUNAT")
print("=" * 70)

sunat_service = SUNATService(config.Config)

try:
    print("\n1️⃣ Generando XML...")
    xml_path, xml_string = sunat_service.generar_xml_boleta(venta)
    print(f"✅ XML generado: {xml_path}")

    print("\n2️⃣ Firmando XML digitalmente...")
    xml_path, xml_firmado = sunat_service.firmar_xml(xml_path, xml_string)
    print(f"✅ XML firmado correctamente")

    print("\n3️⃣ Enviando a SUNAT...")
    # Usar el método correcto dependiendo de si hay API REST configurada
    if sunat_service.usar_api_rest:
        resultado = sunat_service.enviar_a_sunat_api_rest(xml_path, venta)
    else:
        resultado = sunat_service.enviar_a_sunat(xml_path, venta)

    print("\n" + "=" * 70)
    print("  RESULTADO DEL ENVÍO")
    print("=" * 70)

    if resultado['success']:
        print(f"✅ SUCCESS: {resultado['message']}")
        if 'cdr_path' in resultado:
            print(f"📦 CDR recibido: {resultado['cdr_path']}")

        # Actualizar estado en base de datos
        venta.estado = "ACEPTADO"
        venta.cdr_path = resultado.get('cdr_path', '')
        session.commit()
        print(f"✅ Estado actualizado en base de datos")
    else:
        print(f"❌ ERROR: {resultado['message']}")
        venta.estado = "RECHAZADO"
        venta.mensaje_sunat = resultado['message']
        session.commit()
        print(f"⚠️  Estado actualizado en base de datos")

    print("\n💡 Revisa los archivos de debug:")
    print("   - sunat_request_debug.xml")
    print("   - sunat_response_debug.xml")
    print(f"   - {xml_path}")

except Exception as e:
    print(f"\n❌ ERROR FATAL: {str(e)}")
    import traceback
    traceback.print_exc()

    venta.estado = "ERROR"
    venta.mensaje_sunat = str(e)
    session.commit()

session.close()

print("\n" + "=" * 70)
print("  FIN DEL PROCESO")
print("=" * 70)
