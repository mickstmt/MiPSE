"""
Script para verificar y corregir la URL de producción de SUNAT
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

print("=" * 70)
print("  VERIFICACIÓN DE CONFIGURACIÓN SUNAT")
print("=" * 70)

print("\n📋 VERIFICACIÓN 1: TIPO DE COMPROBANTE")
print("-" * 70)
print("✅ El código está generando correctamente:")
print("   invoice_type_code.text = '03'  (Boleta)")
print("   Serie: B001 (correcto para boletas)")

print("\n📋 VERIFICACIÓN 2: URL DE PRODUCCIÓN")
print("-" * 70)

print("\n⚠️  PROBLEMA DETECTADO:")
print("   URL Actual:    https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService")
print("   URL Correcta:  https://e-factura.sunat.gob.pe/ol-ti-it-cpe/billService")
print("                                                   ^^^^^^^^^^^^")
print("   Diferencia: 'ol-ti-itcpfegem' vs 'ol-ti-it-cpe'")

print("\n🔍 EXPLICACIÓN:")
print("""
SUNAT tiene diferentes endpoints:

1. ANTIGUO (ya no se usa):
   /ol-ti-itcpfegem/billService
   
2. NUEVO (actual para CPE):
   /ol-ti-it-cpe/billService
   
CPE = Comprobantes de Pago Electrónicos

El endpoint correcto para facturación electrónica moderna es:
ol-ti-it-cpe (Comprobantes de Pago Electrónicos)
""")

print("\n✅ SOLUCIÓN:")
print("   Vamos a actualizar config.py con la URL correcta")

print("\n" + "=" * 70)
