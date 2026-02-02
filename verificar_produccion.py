"""
Script para verificar si el SEE del Contribuyente ya está activo en PRODUCCIÓN
"""
import os
import sys

# Configurar encoding para Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Forzar uso de PRODUCCION temporalmente
os.environ['SUNAT_AMBIENTE'] = 'PRODUCCION'

from dotenv import load_dotenv
load_dotenv(override=True)

from datetime import datetime
from models import db, Venta, VentaItem, Cliente
from sunat_service import SUNATService
import config

# Forzar PRODUCCION
config.Config.SUNAT_AMBIENTE = 'PRODUCCION'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(config.Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 70)
print("  VERIFICACIÓN DE ESTADO EN PRODUCCIÓN")
print("=" * 70)
print(f"\n🔍 Verificando si el SEE del Contribuyente está activo...")
print(f"   RUC: {config.Config.SUNAT_RUC}")
print(f"   Usuario SOL: {config.Config.SUNAT_USUARIO_SOL}")
print(f"   Ambiente: PRODUCCION (forzado)")

# Buscar cliente de prueba
cliente = session.query(Cliente).filter_by(numero_documento="12345678").first()
if not cliente:
    cliente = Cliente(
        numero_documento="12345678",
        tipo_documento="DNI",
        nombres="CLIENTE DE PRUEBA",
        apellido_paterno="VERIFICACION",
        apellido_materno="PRODUCCION",
        direccion="Lima, Perú"
    )
    session.add(cliente)
    session.commit()

# Producto de prueba
class ProductoPrueba:
    id = 999
    nombre = "VERIFICACION PRODUCCION SUNAT"
    precio = 10.00

producto = ProductoPrueba()

# Obtener siguiente correlativo
from models import Usuario
vendedor = session.query(Usuario).first()
if not vendedor:
    print("❌ No hay usuarios en la base de datos.")
    print("   Ejecuta primero: python app.py")
    session.close()
    exit(1)

ultima_venta = session.query(Venta).filter(
    Venta.serie == config.Config.SERIE_BOLETA
).order_by(Venta.correlativo.desc()).first()

siguiente_correlativo = (int(ultima_venta.correlativo) + 1) if ultima_venta else 1
numero_completo = f"{config.Config.SERIE_BOLETA}-{siguiente_correlativo:08d}"

# Crear venta de prueba
venta = Venta(
    cliente_id=cliente.id,
    vendedor_id=vendedor.id,
    fecha_emision=datetime.now(),
    serie=config.Config.SERIE_BOLETA,
    correlativo=str(siguiente_correlativo),
    subtotal=float(producto.precio) / 1.18,
    total=float(producto.precio),
    estado="PENDIENTE",
    numero_completo=numero_completo
)
session.add(venta)
session.flush()

venta_item = VentaItem(
    venta_id=venta.id,
    producto_nombre=producto.nombre,
    cantidad=1,
    precio_unitario=float(producto.precio),
    subtotal=float(producto.precio)
)
session.add(venta_item)
session.commit()

print(f"\n📄 Comprobante de prueba: {numero_completo}")

# Intentar enviar a PRODUCCIÓN
sunat_service = SUNATService(config.Config)

try:
    print("\n⏳ Generando y enviando a PRODUCCIÓN...")

    xml_path, xml_string = sunat_service.generar_xml_boleta(venta)
    xml_path, xml_firmado = sunat_service.firmar_xml(xml_path, xml_string)

    if sunat_service.usar_api_rest:
        resultado = sunat_service.enviar_a_sunat_api_rest(xml_path, venta)
    else:
        resultado = sunat_service.enviar_a_sunat(xml_path, venta)

    print("\n" + "=" * 70)
    print("  RESULTADO")
    print("=" * 70)

    if resultado['success']:
        print("\n✅ ¡EXCELENTE NOTICIA!")
        print("   El SEE del Contribuyente YA ESTÁ ACTIVO en PRODUCCIÓN")
        print("\n📋 Próximos pasos:")
        print("   1. Cambia en .env: SUNAT_AMBIENTE=PRODUCCION")
        print("   2. Tu sistema ya puede emitir comprobantes REALES")
        print("   3. Elimina esta venta de prueba de la base de datos")

        # Eliminar venta de prueba
        session.delete(venta_item)
        session.delete(venta)
        session.commit()
        print("\n🗑️  Venta de prueba eliminada automáticamente")

    else:
        error_msg = resultado['message']
        print(f"\n⏳ RESULTADO: {error_msg}")

        if "0111" in error_msg or "perfil" in error_msg.lower():
            print("\n❌ El SEE del Contribuyente AÚN NO ESTÁ ACTIVO")
            print("\n📞 ACCIONES RECOMENDADAS:")
            print("   1. Llama a Mesa de Ayuda SUNAT: (01) 315-0730")
            print("   2. Indica tu RUC: 10433050709")
            print("   3. Menciona que solicitaste afiliación al SEE del Contribuyente")
            print("   4. Pregunta cuándo estará activo")
            print("\n📧 O envía solicitud por Mesa de Partes Virtual:")
            print("   https://www.sunat.gob.pe/ → Mesa de Partes")
            print("\n💡 Mientras tanto, puedes seguir usando BETA para pruebas")
        else:
            print(f"\n⚠️  Error diferente: {error_msg}")
            print("   Contacta a SUNAT para más información")

        # Eliminar venta de prueba
        session.delete(venta_item)
        session.delete(venta)
        session.commit()
        print("\n🗑️  Venta de prueba eliminada automáticamente")

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

    # Eliminar venta de prueba
    try:
        session.delete(venta_item)
        session.delete(venta)
        session.commit()
    except:
        pass

session.close()

print("\n" + "=" * 70)
print("  FIN DE LA VERIFICACIÓN")
print("=" * 70)
