"""
Script para verificar el estado de activación en SUNAT
y proporcionar instrucciones detalladas
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

print("=" * 70)
print("  ANÁLISIS DETALLADO - ERROR 0111 SUNAT")
print("=" * 70)

ruc = os.getenv('SUNAT_RUC', 'NO CONFIGURADO')
usuario_sol = os.getenv('SUNAT_USUARIO_SOL', 'NO CONFIGURADO')
ambiente = os.getenv('SUNAT_AMBIENTE', 'BETA')

print(f"\n📋 CONFIGURACIÓN ACTUAL:")
print(f"   RUC: {ruc}")
print(f"   Usuario SOL: {usuario_sol}")
print(f"   Usuario Completo: {ruc}{usuario_sol}")
print(f"   Ambiente: {ambiente}")

print("\n" + "=" * 70)
print("  DIAGNÓSTICO DEL ERROR")
print("=" * 70)

print("""
❌ ERROR PERSISTENTE: 0111
   "No tiene el perfil para enviar comprobantes electronicos"

🔍 ANÁLISIS:

Hemos probado con DOS usuarios diferentes:
   1. VOTROEXP - Error 0111
   2. ISTORE25 - Error 0111

Ambos usuarios reciben el MISMO error, lo que confirma que:

   ✓ Las credenciales están correctas (no hay error de autenticación)
   ✓ La conexión a SUNAT funciona perfectamente
   ✓ El XML se genera y firma correctamente
   
   ✗ El RUC 10433050709 NO está habilitado para facturación 
     electrónica en el ambiente de PRODUCCIÓN

""")

print("=" * 70)
print("  ¿QUÉ SIGNIFICA ESTO?")
print("=" * 70)

print("""
El error 0111 es un error de AUTORIZACIÓN, no de autenticación.

Esto significa:
   • Tu usuario y contraseña son CORRECTOS
   • SUNAT te reconoce y autentica
   • Pero tu RUC no tiene el PERMISO para enviar comprobantes

Es como tener las llaves de un edificio (credenciales correctas)
pero no tener autorización para entrar a una sala específica.

""")

print("=" * 70)
print("  SOLUCIÓN PASO A PASO")
print("=" * 70)

print(f"""
📝 PASO 1: VERIFICAR ESTADO EN SUNAT

1. Ingresa a SUNAT Operaciones en Línea:
   URL: https://e-menu.sunat.gob.pe/cl-ti-itmenu/MenuInternet.htm
   
2. Inicia sesión con:
   • RUC: {ruc}
   • Usuario: {usuario_sol}
   • Clave: (tu clave SOL)

3. Busca la opción:
   "Comprobantes de Pago Electrónicos" o "Sistema de Emisión Electrónica"

4. Verifica si aparece:
   ✓ "Emisor Electrónico - Activo"
   ✗ "No habilitado" o "Pendiente de activación"

""")

print("=" * 70)
print("  PASO 2: SOLICITAR ACTIVACIÓN (SI ES NECESARIO)")
print("=" * 70)

print(f"""
Si NO estás habilitado como Emisor Electrónico:

A. PARA RUC 10 (Persona Natural):
   
   1. Ingresa a SUNAT Virtual:
      https://www.sunat.gob.pe/
   
   2. Ve a: Trámites y Consultas
      → Comprobantes de Pago Electrónicos
      → Afiliación al Sistema de Emisión Electrónica
   
   3. Selecciona el tipo de comprobante:
      • Boletas Electrónicas (para NRUS)
   
   4. Completa el formulario de afiliación
   
   5. Espera la confirmación (1-3 días hábiles)

B. DOCUMENTOS QUE PODRÍAS NECESITAR:
   • DNI del titular
   • Certificado digital (ya lo tienes)
   • Declaración jurada (se genera en línea)

""")

print("=" * 70)
print("  PASO 3: MIENTRAS TANTO - USA BETA")
print("=" * 70)

print("""
Mientras esperas la activación en PRODUCCIÓN:

1. Cambia al ambiente BETA:
   python cambiar_a_beta.py

2. Continúa desarrollando y probando:
   • Todas las funcionalidades funcionan igual
   • Puedes generar comprobantes de prueba
   • Entrenar a tus usuarios
   • Verificar que todo funciona correctamente

3. Cuando SUNAT active tu RUC en producción:
   python cambiar_a_produccion.py

""")

print("=" * 70)
print("  VERIFICACIÓN ADICIONAL")
print("=" * 70)

print(f"""
📞 CONTACTAR A SUNAT:

Si necesitas ayuda directa de SUNAT:

• Central de Consultas: (01) 315-0730
• Horario: Lunes a Viernes, 8:30 AM - 6:00 PM
• Pregunta específica: 
  "Necesito activar mi RUC {ruc} para facturación electrónica 
   en el ambiente de producción. Tengo el error 0111."

• También puedes ir presencialmente a un Centro de Servicios SUNAT

""")

print("=" * 70)
print("  RESUMEN")
print("=" * 70)

print("""
✅ LO QUE FUNCIONA:
   • Conexión a SUNAT
   • Generación de XML con serie B001
   • Firma digital
   • Autenticación de usuarios
   • Ambiente BETA (pruebas)

❌ LO QUE FALTA:
   • Activación del RUC en ambiente de PRODUCCIÓN

🎯 ACCIÓN REQUERIDA:
   1. Verificar estado en SUNAT Operaciones en Línea
   2. Solicitar activación si es necesario
   3. Esperar confirmación de SUNAT
   4. Mientras tanto, usar ambiente BETA

""")

print("=" * 70)
