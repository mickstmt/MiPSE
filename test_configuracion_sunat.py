"""
Script de verificación completa de la configuración SUNAT
Este script verifica que todo esté correctamente configurado antes de enviar a PRODUCCIÓN
"""

import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from lxml import etree
import base64
import zipfile
from io import BytesIO
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def print_seccion(titulo):
    """Imprime una sección con formato"""
    print("\n" + "="*70)
    print(f"  {titulo}")
    print("="*70)

def print_ok(mensaje):
    """Imprime mensaje de éxito"""
    print(f"[OK] {mensaje}")

def print_error(mensaje):
    """Imprime mensaje de error"""
    print(f"[ERROR] {mensaje}")

def print_warning(mensaje):
    """Imprime mensaje de advertencia"""
    print(f"[WARN] {mensaje}")

def verificar_variables_entorno():
    """Verifica que todas las variables de entorno necesarias estén configuradas"""
    print_seccion("1. VERIFICACIÓN DE VARIABLES DE ENTORNO")

    variables_requeridas = {
        'SUNAT_RUC': os.getenv('SUNAT_RUC'),
        'SUNAT_USUARIO_SOL': os.getenv('SUNAT_USUARIO_SOL'),
        'SUNAT_CLAVE_SOL': os.getenv('SUNAT_CLAVE_SOL'),
        'SUNAT_AMBIENTE': os.getenv('SUNAT_AMBIENTE'),
        'CERT_PATH': os.getenv('CERT_PATH'),
        'CERT_PASSWORD': os.getenv('CERT_PASSWORD'),
        'SERIE_BOLETA': os.getenv('SERIE_BOLETA'),
    }

    errores = []
    for var, valor in variables_requeridas.items():
        if valor:
            # Ocultar contraseñas
            if 'PASSWORD' in var or 'CLAVE' in var:
                print_ok(f"{var} = {'*' * len(valor)}")
            else:
                print_ok(f"{var} = {valor}")
        else:
            print_error(f"{var} NO está configurada")
            errores.append(var)

    # Verificaciones específicas
    ambiente = os.getenv('SUNAT_AMBIENTE', '')
    if ambiente not in ['BETA', 'PRODUCCION']:
        print_error(f"SUNAT_AMBIENTE debe ser 'BETA' o 'PRODUCCION', no '{ambiente}'")
        errores.append('SUNAT_AMBIENTE')

    serie = os.getenv('SERIE_BOLETA', '')
    if len(serie) != 4:
        print_error(f"SERIE_BOLETA debe tener 4 caracteres, tiene {len(serie)}")
        errores.append('SERIE_BOLETA')

    usuario = os.getenv('SUNAT_USUARIO_SOL', '')
    if ambiente == 'PRODUCCION' and usuario != 'IZISTORE':
        print_warning(f"Usuario SOL es '{usuario}', debería ser 'IZISTORE' para PRODUCCION")

    return len(errores) == 0

def verificar_certificado():
    """Verifica que el certificado esté disponible y sea válido"""
    print_seccion("2. VERIFICACIÓN DE CERTIFICADO DIGITAL")

    cert_path = os.getenv('CERT_PATH', '')
    cert_password = os.getenv('CERT_PASSWORD', '')

    if not os.path.exists(cert_path):
        print_error(f"No se encuentra el archivo de certificado: {cert_path}")
        return False

    print_ok(f"Archivo encontrado: {cert_path}")

    # Verificar que se pueda leer el certificado
    try:
        with open(cert_path, 'rb') as f:
            pfx_data = f.read()

        print_ok(f"Tamaño del archivo: {len(pfx_data)} bytes")

        # Intentar cargar el certificado
        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
            pfx_data,
            cert_password.encode('utf-8'),
            backend=default_backend()
        )

        print_ok("Certificado cargado correctamente")

        # Mostrar información del certificado
        subject = certificate.subject
        issuer = certificate.issuer

        print_ok(f"Emitido para: {subject.rfc4514_string()}")
        print_ok(f"Emitido por: {issuer.rfc4514_string()}")
        print_ok(f"Válido desde: {certificate.not_valid_before_utc}")
        print_ok(f"Válido hasta: {certificate.not_valid_after_utc}")

        # Verificar si el certificado está vigente
        from datetime import datetime, timezone
        ahora = datetime.now(timezone.utc)
        if ahora < certificate.not_valid_before_utc:
            print_error("El certificado aún no es válido")
            return False
        elif ahora > certificate.not_valid_after_utc:
            print_error("El certificado ha expirado")
            return False
        else:
            dias_restantes = (certificate.not_valid_after_utc - ahora).days
            print_ok(f"Certificado vigente ({dias_restantes} días restantes)")

        return True

    except Exception as e:
        print_error(f"Error al cargar el certificado: {str(e)}")
        return False

def verificar_certificado_cer():
    """Verifica que exista el archivo .cer para subir a SUNAT"""
    print_seccion("3. VERIFICACIÓN DE CERTIFICADO .CER (para subir a SUNAT)")

    cert_path = os.getenv('CERT_PATH', '')
    cer_path = cert_path.replace('.pfx', '.cer')

    if not os.path.exists(cer_path):
        print_warning(f"No se encuentra el archivo .cer: {cer_path}")
        print("  Este archivo es necesario para subirlo a SUNAT.")
        print("  Puedes generarlo con:")
        print(f"  openssl pkcs12 -in {cert_path} -clcerts -nokeys -out temp.pem -password pass:TU_PASSWORD -legacy")
        print(f"  openssl x509 -in temp.pem -outform DER -out {cer_path}")
        return False

    print_ok(f"Archivo .cer encontrado: {cer_path}")

    # Verificar tamaño
    size = os.path.getsize(cer_path)
    print_ok(f"Tamaño: {size} bytes")

    return True

def verificar_estructura_directorios():
    """Verifica que existan las carpetas necesarias"""
    print_seccion("4. VERIFICACIÓN DE ESTRUCTURA DE DIRECTORIOS")

    directorios = [
        'xml_generados',
        'cdr_recibidos',
        'certificados',
        'comprobantes'
    ]

    todos_ok = True
    for dir_name in directorios:
        if os.path.exists(dir_name):
            archivos = len(os.listdir(dir_name))
            print_ok(f"{dir_name}/ existe ({archivos} archivos)")
        else:
            print_warning(f"{dir_name}/ NO existe (se creará automáticamente)")

    return True

def verificar_base_datos():
    """Verifica la conexión a la base de datos"""
    print_seccion("5. VERIFICACIÓN DE BASE DE DATOS")

    try:
        from config import Config
        from models import db, Venta
        from flask import Flask

        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)

        with app.app_context():
            # Intentar contar ventas
            total_ventas = Venta.query.count()
            print_ok(f"Conexión exitosa a la base de datos")
            print_ok(f"Total de ventas registradas: {total_ventas}")

            # Verificar ventas por serie
            serie = os.getenv('SERIE_BOLETA', 'B010')
            ventas_serie = Venta.query.filter_by(serie=serie).count()
            print_ok(f"Ventas con serie {serie}: {ventas_serie}")

            # Obtener el último correlativo de esta serie
            max_correlativo = db.session.query(db.func.max(db.cast(Venta.correlativo, db.Integer)))\
                .filter(Venta.serie == serie)\
                .scalar()

            if max_correlativo:
                print_ok(f"Último correlativo de {serie}: {max_correlativo}")
                print(f"  Próximo comprobante será: {serie}-{str(max_correlativo + 1).zfill(8)}")
            else:
                print_ok(f"No hay ventas con serie {serie}")
                print(f"  Próximo comprobante será: {serie}-00000001")

            return True

    except Exception as e:
        print_error(f"Error al conectar con la base de datos: {str(e)}")
        return False

def verificar_config_flask():
    """Verifica la configuración de Flask"""
    print_seccion("6. VERIFICACIÓN DE CONFIGURACIÓN FLASK")

    try:
        from config import Config

        config = Config()

        print_ok(f"SUNAT_AMBIENTE: {config.SUNAT_AMBIENTE}")
        print_ok(f"SERIE_BOLETA: {config.SERIE_BOLETA}")
        print_ok(f"SUNAT_RUC: {config.SUNAT_RUC}")
        print_ok(f"SUNAT_USUARIO_SOL: {config.SUNAT_USUARIO_SOL}")

        if config.SUNAT_AMBIENTE == 'PRODUCCION':
            url = config.SUNAT_URL_PRODUCCION
            print_ok(f"URL de envío: {url}")
        else:
            url = config.SUNAT_URL_BETA
            print_ok(f"URL de envío: {url}")

        return True

    except Exception as e:
        print_error(f"Error al cargar configuración: {str(e)}")
        return False

def test_generacion_xml():
    """Prueba la generación de un XML de ejemplo (sin enviar)"""
    print_seccion("7. TEST DE GENERACIÓN DE XML")

    try:
        from lxml import etree
        from datetime import datetime

        # Datos de prueba
        ruc = os.getenv('SUNAT_RUC', '10433050709')
        serie = os.getenv('SERIE_BOLETA', 'B010')
        correlativo = '00000001'
        fecha = datetime.now().strftime('%Y-%m-%d')

        # Crear un XML básico
        invoice = etree.Element(
            "{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice",
            nsmap={
                None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
                "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
                "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
            }
        )

        # Agregar elementos básicos
        cbc_ns = "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"

        ubl_version = etree.SubElement(invoice, f"{cbc_ns}UBLVersionID")
        ubl_version.text = "2.1"

        customization = etree.SubElement(invoice, f"{cbc_ns}CustomizationID")
        customization.text = "2.0"

        id_elem = etree.SubElement(invoice, f"{cbc_ns}ID")
        id_elem.text = f"{serie}-{correlativo}"

        issue_date = etree.SubElement(invoice, f"{cbc_ns}IssueDate")
        issue_date.text = fecha

        print_ok("XML de prueba creado correctamente")

        # Convertir a string
        xml_string = etree.tostring(invoice, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        print_ok(f"Tamaño del XML: {len(xml_string)} bytes")

        # Verificar que sea XML válido
        etree.fromstring(xml_string)
        print_ok("XML es sintácticamente válido")

        return True

    except Exception as e:
        print_error(f"Error al generar XML de prueba: {str(e)}")
        return False

def test_firma_xml():
    """Prueba la firma digital de un XML de ejemplo"""
    print_seccion("8. TEST DE FIRMA DIGITAL")

    try:
        from signxml import XMLSigner
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import pkcs12
        from cryptography.hazmat.backends import default_backend
        from lxml import etree
        import os

        # Habilitar SHA1 (requerido por SUNAT)
        os.environ["SIGNXML_INSECURE_FEATURES"] = "sha1"
        XMLSigner.check_deprecated_methods = lambda self: None

        # Cargar certificado
        cert_path = os.getenv('CERT_PATH', '')
        cert_password = os.getenv('CERT_PASSWORD', '')

        with open(cert_path, 'rb') as f:
            pfx_data = f.read()

        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
            pfx_data,
            cert_password.encode('utf-8'),
            backend=default_backend()
        )

        print_ok("Certificado cargado para firma")

        # Crear un XML simple de prueba
        root = etree.Element("TestDocument")
        etree.SubElement(root, "Data").text = "Test de firma digital"

        # Convertir clave privada a PEM
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Convertir certificado a PEM
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)

        # Firmar
        signer = XMLSigner(
            signature_algorithm="rsa-sha1",
            digest_algorithm="sha1",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
        )

        signed_root = signer.sign(root, key=key_pem, cert=cert_pem, always_add_key_value=False)

        print_ok("XML firmado correctamente")

        # Verificar que la firma existe
        signature = signed_root.find('.//{http://www.w3.org/2000/09/xmldsig#}Signature')
        if signature is not None:
            print_ok("Elemento Signature encontrado en el XML")

            # Verificar elementos de la firma
            signature_value = signature.find('.//{http://www.w3.org/2000/09/xmldsig#}SignatureValue')
            if signature_value is not None:
                print_ok("SignatureValue presente")

            x509_cert = signature.find('.//{http://www.w3.org/2000/09/xmldsig#}X509Certificate')
            if x509_cert is not None:
                print_ok("X509Certificate presente")
                cert_len = len(x509_cert.text) if x509_cert.text else 0
                print_ok(f"Longitud del certificado: {cert_len} caracteres")
        else:
            print_error("No se encontró el elemento Signature")
            return False

        return True

    except Exception as e:
        print_error(f"Error al firmar XML de prueba: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def mostrar_checklist_sunat():
    """Muestra la checklist de pasos a completar en SUNAT"""
    print_seccion("9. CHECKLIST DE AFILIACION EN SUNAT")

    print("\n[!] IMPORTANTE: Antes de enviar comprobantes a PRODUCCION, debes completar:")
    print("\n[ ] 1. Subir el certificado .cer a SUNAT")
    print("       - Ir a: SOL SUNAT > Registro de Certificados Digitales")
    print(f"       - Subir archivo: {os.getenv('CERT_PATH', '').replace('.pfx', '.cer')}")

    print("\n[ ] 2. Afiliarte al Sistema de Emision Electronica (SEE)")
    print("       - Ir a: Afiliacion SEE")
    print("       - Marcar: 'Deseo emitir a traves del SEE - Del Contribuyente'")

    print("\n[ ] 3. Registrar la serie en SUNAT")
    print(f"       - Ir a: Registro de Puntos de Emision")
    print(f"       - Registrar serie: {os.getenv('SERIE_BOLETA', 'B010')}")
    print("       - Tipo: Boleta de Venta Electronica")

    print("\n[ ] 4. Reiniciar el servidor Flask")
    print("       - Despues de completar los pasos anteriores")
    print("       - Para que cargue las nuevas configuraciones")

    print("\n[ ] 5. Generar una venta de prueba")
    print("       - El sistema generara automaticamente el comprobante")
    print(f"       - Numero: {os.getenv('SERIE_BOLETA', 'B010')}-00000001")

def main():
    """Función principal"""
    print("\n" + "="*70)
    print("  TEST DE CONFIGURACIÓN SUNAT - SISTEMA DE VENTAS IZISTORE")
    print("="*70)

    resultados = []

    # Ejecutar todas las verificaciones
    resultados.append(("Variables de entorno", verificar_variables_entorno()))
    resultados.append(("Certificado digital (.pfx)", verificar_certificado()))
    resultados.append(("Certificado .cer", verificar_certificado_cer()))
    resultados.append(("Estructura de directorios", verificar_estructura_directorios()))
    resultados.append(("Base de datos", verificar_base_datos()))
    resultados.append(("Configuración Flask", verificar_config_flask()))
    resultados.append(("Generación de XML", test_generacion_xml()))
    resultados.append(("Firma digital", test_firma_xml()))

    # Mostrar checklist
    mostrar_checklist_sunat()

    # Resumen final
    print_seccion("RESUMEN DE VERIFICACIÓN")

    total = len(resultados)
    exitosos = sum(1 for _, r in resultados if r)
    fallidos = total - exitosos

    for nombre, resultado in resultados:
        if resultado:
            print_ok(f"{nombre}")
        else:
            print_error(f"{nombre}")

    print(f"\nTotal: {exitosos}/{total} verificaciones exitosas")

    if fallidos == 0:
        print("\n[OK] TODAS LAS VERIFICACIONES PASARON")
        print("  El sistema esta listo tecnicamente.")
        print("  Completa la checklist de SUNAT y estaras listo para PRODUCCION.")
        return 0
    else:
        print(f"\n[ERROR] {fallidos} VERIFICACION(ES) FALLARON")
        print("  Revisa los errores anteriores antes de continuar.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
