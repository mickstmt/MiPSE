"""
Script de prueba básica para verificar la configuración
Ejecuta: python test_basico.py
"""

print("="*60)
print("PRUEBA BÁSICA DE CONFIGURACIÓN")
print("="*60)

# 1. Verificar importaciones
print("\n1. Verificando importaciones...")
try:
    from config import Config
    from models import db, Usuario, Cliente, Venta, VentaItem
    from sunat_service import SUNATService
    from scheduler_service import SchedulerService
    print("   ✓ Todas las importaciones correctas")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 2. Verificar configuración
print("\n2. Verificando configuración...")
config = Config()
print(f"   RUC: {config.EMPRESA_RUC}")
print(f"   Razón Social: {config.EMPRESA_RAZON_SOCIAL}")
print(f"   Usuario SOL: {config.SUNAT_USUARIO_SOL}")
print(f"   URL SUNAT: {config.SUNAT_URL_BETA}")
print(f"   Certificado: {config.CERT_PATH}")

# 3. Verificar que existe el certificado
import os
print("\n3. Verificando certificado...")
if os.path.exists(config.CERT_PATH):
    print(f"   ✓ Certificado encontrado en: {config.CERT_PATH}")
    file_size = os.path.getsize(config.CERT_PATH)
    print(f"   ✓ Tamaño: {file_size} bytes")
else:
    print(f"   ✗ Certificado NO encontrado en: {config.CERT_PATH}")
    print("   → Copia el archivo CT2510134109.pfx a la carpeta certificados/")

# 4. Verificar contraseña del certificado
print("\n4. Verificando contraseña del certificado...")
if config.CERT_PASSWORD and config.CERT_PASSWORD != "TU_CONTRASEÑA_AQUI":
    print(f"   ✓ Contraseña configurada (longitud: {len(config.CERT_PASSWORD)} caracteres)")
else:
    print("   ✗ Contraseña NO configurada o es la de ejemplo")
    print("   → Edita el archivo .env y pon la contraseña del certificado")

# 5. Verificar carpetas
print("\n5. Verificando carpetas...")
carpetas = ['certificados', 'xml_generados', 'cdr_recibidos', 'comprobantes']
for carpeta in carpetas:
    if os.path.exists(carpeta):
        print(f"   ✓ {carpeta}/")
    else:
        print(f"   ✗ {carpeta}/ no existe")
        os.makedirs(carpeta, exist_ok=True)
        print(f"     ✓ Carpeta creada")

# 6. Verificar base de datos
print("\n6. Verificando conexión a base de datos...")
try:
    from app import app
    with app.app_context():
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1')).scalar()
        if result == 1:
            print("   ✓ Conexión a base de datos exitosa")

            # Verificar tabla de ventas
            ventas_count = Venta.query.count()
            print(f"   ✓ Ventas en la base de datos: {ventas_count}")
except Exception as e:
    print(f"   ✗ Error de conexión: {e}")

print("\n" + "="*60)
print("RESUMEN")
print("="*60)

# Crear checklist
checks = []

# Check certificado
checks.append(("Certificado copiado", os.path.exists(config.CERT_PATH)))

# Check contraseña
checks.append(("Contraseña configurada", config.CERT_PASSWORD and config.CERT_PASSWORD != "TU_CONTRASEÑA_AQUI"))

# Check carpetas
checks.append(("Carpetas creadas", all(os.path.exists(c) for c in carpetas)))

# Mostrar checklist
for item, status in checks:
    symbol = "✓" if status else "✗"
    print(f"{symbol} {item}")

# Verificar si está listo
if all(status for _, status in checks):
    print("\n🎉 ¡TODO LISTO PARA PROBAR!")
    print("\nEjecuta: python app.py")
else:
    print("\n⚠️  Aún faltan algunas configuraciones (ver arriba)")

print("="*60)
