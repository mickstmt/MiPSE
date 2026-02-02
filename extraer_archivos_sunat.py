"""
Script para extraer archivos necesarios para enviar a SUNAT:
1. Archivo XML de la boleta
2. Trama SOAP Request (Envío)
3. Trama SOAP Response (Respuesta con error)

Uso:
    python extraer_archivos_sunat.py [numero_boleta]
    
Ejemplo:
    python extraer_archivos_sunat.py B001-00000010
"""

import os
import sys
import shutil
from datetime import datetime

def extraer_archivos_sunat(numero_boleta=None):
    """
    Extrae los archivos necesarios para enviar a SUNAT
    
    Args:
        numero_boleta: Número de boleta (ej: B001-00000010). Si es None, usa el último generado.
    """
    
    # Configuración
    RUC = "10433050709"
    TIPO_DOC = "03"  # 03 = Boleta
    
    # Crear carpeta de salida con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta_salida = f"archivos_sunat_{timestamp}"
    
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)
    
    print(f"\n{'='*60}")
    print(f"EXTRACCIÓN DE ARCHIVOS PARA SUNAT")
    print(f"{'='*60}\n")
    
    # Si no se especifica número de boleta, buscar el último
    if numero_boleta is None:
        xml_generados = "xml_generados"
        if os.path.exists(xml_generados):
            archivos = [f for f in os.listdir(xml_generados) if f.endswith('.xml')]
            if archivos:
                # Ordenar por nombre (el último será el más reciente)
                archivos.sort()
                ultimo_archivo = archivos[-1]
                # Extraer número de boleta del nombre del archivo
                # Formato: 10433050709-03-B001-00000010.xml
                numero_boleta = ultimo_archivo.replace(f"{RUC}-{TIPO_DOC}-", "").replace(".xml", "")
                print(f"📋 Usando última boleta generada: {numero_boleta}")
            else:
                print("❌ No se encontraron archivos XML generados")
                return False
        else:
            print("❌ No existe la carpeta xml_generados")
            return False
    
    # Construir nombres de archivos
    nombre_base = f"{RUC}-{TIPO_DOC}-{numero_boleta}"
    
    # 1. ARCHIVO XML DE LA BOLETA
    xml_origen = os.path.join("xml_generados", f"{nombre_base}.xml")
    xml_destino = os.path.join(carpeta_salida, f"1_XML_BOLETA_{numero_boleta}.xml")
    
    if os.path.exists(xml_origen):
        shutil.copy2(xml_origen, xml_destino)
        print(f"✅ 1. XML de la boleta copiado:")
        print(f"   📄 {xml_destino}")
        print(f"   📊 Tamaño: {os.path.getsize(xml_destino)} bytes\n")
    else:
        print(f"❌ No se encontró el archivo XML: {xml_origen}\n")
    
    # 2. TRAMA SOAP REQUEST (Envío)
    soap_request_origen = "sunat_request_debug.xml"
    soap_request_destino = os.path.join(carpeta_salida, f"2_SOAP_REQUEST_{numero_boleta}.xml")
    
    if os.path.exists(soap_request_origen):
        shutil.copy2(soap_request_origen, soap_request_destino)
        print(f"✅ 2. Trama SOAP Request copiada:")
        print(f"   📄 {soap_request_destino}")
        print(f"   📊 Tamaño: {os.path.getsize(soap_request_destino)} bytes\n")
        
        # Leer y mostrar información del request
        with open(soap_request_origen, 'r', encoding='utf-8') as f:
            contenido = f.read()
            if '<fileName>' in contenido:
                inicio = contenido.find('<fileName>') + len('<fileName>')
                fin = contenido.find('</fileName>')
                archivo_zip = contenido[inicio:fin]
                print(f"   📦 Archivo ZIP enviado: {archivo_zip}")
    else:
        print(f"❌ No se encontró el archivo SOAP Request: {soap_request_origen}\n")
    
    # 3. TRAMA SOAP RESPONSE (Respuesta con error)
    soap_response_origen = "sunat_response_debug.xml"
    soap_response_destino = os.path.join(carpeta_salida, f"3_SOAP_RESPONSE_{numero_boleta}.xml")
    
    if os.path.exists(soap_response_origen):
        shutil.copy2(soap_response_origen, soap_response_destino)
        print(f"✅ 3. Trama SOAP Response copiada:")
        print(f"   📄 {soap_response_destino}")
        print(f"   📊 Tamaño: {os.path.getsize(soap_response_destino)} bytes\n")
        
        # Leer y analizar la respuesta
        with open(soap_response_origen, 'r', encoding='utf-8') as f:
            contenido = f.read()
            
            # Verificar si es un error 404
            if '404 Not Found' in contenido:
                print(f"   ⚠️  RESPUESTA: Error 404 - URL no encontrada")
                print(f"   ℹ️  Esto indica que la URL de SUNAT no es correcta")
            # Verificar si hay un SOAP Fault
            elif 'faultcode' in contenido or 'faultstring' in contenido:
                print(f"   ⚠️  RESPUESTA: SOAP Fault detectado")
                if 'faultcode' in contenido:
                    inicio = contenido.find('<faultcode>') + len('<faultcode>')
                    fin = contenido.find('</faultcode>')
                    if inicio > 0 and fin > 0:
                        codigo = contenido[inicio:fin]
                        print(f"   🔴 Código de error: {codigo}")
                if 'faultstring' in contenido:
                    inicio = contenido.find('<faultstring>') + len('<faultstring>')
                    fin = contenido.find('</faultstring>')
                    if inicio > 0 and fin > 0:
                        mensaje = contenido[inicio:fin]
                        print(f"   📝 Mensaje: {mensaje}")
            else:
                print(f"   ℹ️  Respuesta guardada para análisis")
    else:
        print(f"❌ No se encontró el archivo SOAP Response: {soap_response_origen}\n")
    
    # 4. ARCHIVO ZIP (si existe)
    zip_origen = os.path.join("xml_generados", f"{nombre_base}.zip")
    zip_destino = os.path.join(carpeta_salida, f"4_ZIP_ENVIADO_{numero_boleta}.zip")
    
    if os.path.exists(zip_origen):
        shutil.copy2(zip_origen, zip_destino)
        print(f"✅ 4. Archivo ZIP copiado (BONUS):")
        print(f"   📄 {zip_destino}")
        print(f"   📊 Tamaño: {os.path.getsize(zip_destino)} bytes\n")
    
    # 5. Crear archivo README con información
    readme_path = os.path.join(carpeta_salida, "README.txt")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("ARCHIVOS PARA ENVIAR A SUNAT\n")
        f.write("="*60 + "\n\n")
        f.write(f"Boleta: {numero_boleta}\n")
        f.write(f"RUC: {RUC}\n")
        f.write(f"Fecha de extracción: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("ARCHIVOS INCLUIDOS:\n\n")
        f.write("1. XML de la boleta (1_XML_BOLETA_*.xml)\n")
        f.write("   - Archivo XML firmado digitalmente de la boleta electrónica\n")
        f.write("   - Formato UBL 2.1 según estándar SUNAT\n\n")
        f.write("2. Trama SOAP Request (2_SOAP_REQUEST_*.xml)\n")
        f.write("   - Solicitud SOAP enviada a SUNAT\n")
        f.write("   - Incluye el archivo ZIP en base64\n")
        f.write("   - Método: sendBill\n\n")
        f.write("3. Trama SOAP Response (3_SOAP_RESPONSE_*.xml)\n")
        f.write("   - Respuesta recibida de SUNAT\n")
        f.write("   - Puede contener errores o CDR (Constancia de Recepción)\n\n")
        f.write("4. Archivo ZIP (4_ZIP_ENVIADO_*.zip) [BONUS]\n")
        f.write("   - Archivo ZIP que contiene el XML\n")
        f.write("   - Este es el archivo que se envía a SUNAT\n\n")
        f.write("="*60 + "\n")
        f.write("NOTAS:\n")
        f.write("="*60 + "\n\n")
        f.write("- Estos archivos son necesarios para reportar problemas a SUNAT\n")
        f.write("- El error 0111 indica problemas con el formato del XML o la firma\n")
        f.write("- Verificar que el certificado digital sea válido\n")
        f.write("- Verificar que las credenciales SOL sean correctas\n\n")
    
    print(f"✅ 5. README creado:")
    print(f"   📄 {readme_path}\n")
    
    print(f"{'='*60}")
    print(f"✅ EXTRACCIÓN COMPLETADA")
    print(f"{'='*60}\n")
    print(f"📁 Carpeta de salida: {carpeta_salida}")
    print(f"📊 Total de archivos: {len(os.listdir(carpeta_salida))}\n")
    print(f"💡 Puedes comprimir esta carpeta y enviarla a SUNAT para soporte.\n")
    
    return True

if __name__ == "__main__":
    # Verificar argumentos
    numero_boleta = None
    if len(sys.argv) > 1:
        numero_boleta = sys.argv[1]
        print(f"📋 Extrayendo archivos para boleta: {numero_boleta}\n")
    else:
        print(f"📋 No se especificó número de boleta, usando la última generada...\n")
    
    # Ejecutar extracción
    exito = extraer_archivos_sunat(numero_boleta)
    
    if not exito:
        print("\n❌ La extracción falló. Verifica que existan archivos generados.")
        sys.exit(1)
    else:
        print("✅ Proceso completado exitosamente.")
        sys.exit(0)
