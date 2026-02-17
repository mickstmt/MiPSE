"""
Servicio de integración con SUNAT para facturación electrónica
Maneja la generación de XML, firma digital y envío a SUNAT
"""

import sys

# Configurar encoding para Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

import os

# Habilitar SHA1 para signxml (SUNAT requiere SHA1 aunque esté deprecado)
# Debe configurarse ANTES de importar signxml
os.environ["SIGNXML_INSECURE_FEATURES"] = "sha1"

import base64
import zipfile
from datetime import datetime
from lxml import etree
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
import hashlib
from requests import Session
import requests
from requests.auth import HTTPBasicAuth


class SUNATService:
    """Servicio para interactuar con SUNAT"""

    def __init__(self, config):
        self.config = config
        self.ruc = config.EMPRESA_RUC
        self.razon_social = config.EMPRESA_RAZON_SOCIAL
        self.direccion = config.EMPRESA_DIRECCION
        self.ubigeo = config.EMPRESA_UBIGEO

        # Rutas
        self.cert_path = config.CERT_PATH
        self.cert_password = config.CERT_PASSWORD

        # URLs SUNAT - Usar ambiente configurado
        if config.SUNAT_AMBIENTE == 'PRODUCCION':
            self.url_servicio = config.SUNAT_URL_PRODUCCION
            self.wsdl_url = config.SUNAT_WSDL_PRODUCCION
            print(f"🚀 SUNAT: Usando ambiente de PRODUCCIÓN")
            print(f"   URL: {self.url_servicio}")
        else:
            self.url_servicio = config.SUNAT_URL_BETA
            self.wsdl_url = config.SUNAT_WSDL_BETA
            print(f"🧪 SUNAT: Usando ambiente de PRUEBAS (Beta)")
            print(f"   URL: {self.url_servicio}")

        self.usuario_sol = config.SUNAT_USUARIO_SOL
        self.clave_sol = config.SUNAT_CLAVE_SOL
        self.ambiente = config.SUNAT_AMBIENTE

        # Credenciales API REST
        self.api_client_id = getattr(config, 'SUNAT_API_CLIENT_ID', None)
        self.api_client_secret = getattr(config, 'SUNAT_API_CLIENT_SECRET', None)
        self.api_url = getattr(config, 'SUNAT_API_URL', None)

        # Determinar método de envío (preferir API REST si está configurado)
        self.usar_api_rest = bool(self.api_client_id and self.api_client_secret)

        if self.usar_api_rest:
            print(f"🔑 Credenciales API REST detectadas - Se usará API REST")
            print(f"   Client ID: {self.api_client_id[:20]}...")
        else:
            print(f"🔑 Usando autenticación SOAP con usuario SOL")

        # Asegurar que existan las carpetas necesarias
        os.makedirs("xml_generados", exist_ok=True)
        os.makedirs("cdr_recibidos", exist_ok=True)
        print(f"📁 Directorios xml_generados y cdr_recibidos verificados")

    def generar_xml_boleta(self, venta):
        """
        Genera el XML de la boleta según el formato UBL 2.1 de SUNAT
        """
        try:
            # Namespace UBL 2.1
            nsmap = {
                None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
                'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
                'cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
                'ccts': "urn:un:unece:uncefact:documentation:2",
                'ds': "http://www.w3.org/2000/09/xmldsig#",
                'ext': "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
                'qdt': "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2",
                'udt': "urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2",
            }

            # Crear elemento raíz
            invoice = etree.Element("Invoice", nsmap=nsmap)

            # UBLExtensions (para la firma digital)
            ublext = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtensions")
            ublext_elem = etree.SubElement(ublext, "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtension")
            ext_content = etree.SubElement(ublext_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent")

            # UBLVersionID
            etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UBLVersionID").text = "2.1"

            # CustomizationID
            etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID").text = "2.0"

            # ID del comprobante
            etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = venta.numero_completo

            # Fecha de emisión
            fecha_emision = venta.fecha_emision.strftime("%Y-%m-%d")
            etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate").text = fecha_emision

            # Hora de emisión
            hora_emision = venta.fecha_emision.strftime("%H:%M:%S")
            etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueTime").text = hora_emision

            # Tipo de comprobante (03 = Boleta) con tipo de operación en listID
            invoice_type_code = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode")
            invoice_type_code.set("listAgencyName", "PE:SUNAT")
            invoice_type_code.set("listID", "0101")  # Tipo de operación: Venta Interna
            invoice_type_code.set("listName", "Tipo de Documento")
            invoice_type_code.set("listSchemeURI", "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo51")
            invoice_type_code.set("listURI", "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01")
            invoice_type_code.set("name", "Tipo de Operacion")
            invoice_type_code.text = "03"

            # Moneda
            currency_code = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode")
            currency_code.set("listAgencyName", "United Nations Economic Commission for Europe")
            currency_code.set("listID", "ISO 4217 Alpha")
            currency_code.set("listName", "Currency")
            currency_code.text = "PEN"

            # === SIGNATURE ===
            signature = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Signature")
            etree.SubElement(signature, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = self.ruc
            etree.SubElement(signature, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Note").text = "Elaborado por Sistema de Emision Electronica Facturador SUNAT (SEE-SFS) 1.4"

            sig_party = etree.SubElement(signature, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}SignatoryParty")
            party_id = etree.SubElement(sig_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification")
            id_elem = etree.SubElement(party_id, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
            id_elem.text = self.ruc

            party_name = etree.SubElement(sig_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
            etree.SubElement(party_name, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name").text = self.razon_social

            dig_sig_attach = etree.SubElement(signature, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}DigitalSignatureAttachment")
            ext_ref = etree.SubElement(dig_sig_attach, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}ExternalReference")
            etree.SubElement(ext_ref, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}URI").text = "SIGN"

            # === ACCOUNTING SUPPLIER PARTY (Emisor) ===
            supplier = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty")
            supplier_party = etree.SubElement(supplier, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")

            # RUC del emisor
            party_ident = etree.SubElement(supplier_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification")
            id_elem = etree.SubElement(party_ident, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
            id_elem.set("schemeAgencyName", "PE:SUNAT")
            id_elem.set("schemeID", "6")  # 6 = RUC
            id_elem.set("schemeName", "Documento de Identidad")
            id_elem.set("schemeURI", "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06")
            id_elem.text = self.ruc

            # Nombre comercial
            party_name = etree.SubElement(supplier_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
            etree.SubElement(party_name, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name").text = self.config.EMPRESA_NOMBRE_COMERCIAL

            # Dirección
            postal_addr = etree.SubElement(supplier_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PostalAddress")
            etree.SubElement(postal_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = self.ubigeo
            etree.SubElement(postal_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}StreetName").text = self.direccion

            country = etree.SubElement(postal_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Country")
            etree.SubElement(country, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IdentificationCode").text = "PE"

            # Razón social
            party_legal = etree.SubElement(supplier_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyLegalEntity")
            etree.SubElement(party_legal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}RegistrationName").text = self.razon_social

            # === ACCOUNTING CUSTOMER PARTY (Cliente) ===
            customer = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty")
            customer_party = etree.SubElement(customer, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")

            # Documento del cliente
            party_ident = etree.SubElement(customer_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification")
            id_elem = etree.SubElement(party_ident, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
            
            # Map tipos de documento a códigos SUNAT (Catálogo 06)
            # 1 = DNI, 4 = Carnet de Extranjería, 6 = RUC, 7 = Pasaporte, 0 = Sin Documento
            doc_map = {
                'DNI': '1',
                'CE': '4',
                'RUC': '6',
                'PASAPORTE': '7'
            }
            tipo_doc = doc_map.get(venta.cliente.tipo_documento, '1')
            
            id_elem.set("schemeAgencyName", "PE:SUNAT")
            id_elem.set("schemeID", tipo_doc)
            id_elem.set("schemeName", "Documento de Identidad")
            id_elem.set("schemeURI", "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06")
            id_elem.text = venta.cliente.numero_documento

            # Nombre/Razón social del cliente
            party_legal = etree.SubElement(customer_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyLegalEntity")
            etree.SubElement(party_legal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}RegistrationName").text = venta.cliente.nombre_completo

            # === TAX TOTAL (IGV) ===
            # Calcular IGV (18%)
            subtotal = float(venta.total) / 1.18
            igv = float(venta.total) - subtotal

            tax_total = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal")
            tax_amount = etree.SubElement(tax_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount")
            tax_amount.set("currencyID", "PEN")
            tax_amount.text = f"{igv:.2f}"

            tax_subtotal = etree.SubElement(tax_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxSubtotal")
            taxable_amount = etree.SubElement(tax_subtotal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxableAmount")
            taxable_amount.set("currencyID", "PEN")
            taxable_amount.text = f"{subtotal:.2f}"

            tax_amount2 = etree.SubElement(tax_subtotal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount")
            tax_amount2.set("currencyID", "PEN")
            tax_amount2.text = f"{igv:.2f}"

            tax_category = etree.SubElement(tax_subtotal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxCategory")
            tax_scheme = etree.SubElement(tax_category, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme")
            tax_id = etree.SubElement(tax_scheme, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
            tax_id.set("schemeAgencyName", "PE:SUNAT")
            tax_id.set("schemeID", "UN/ECE 5153")
            tax_id.set("schemeName", "Codigo de tributos")
            tax_id.text = "1000"  # IGV
            etree.SubElement(tax_scheme, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name").text = "IGV"
            etree.SubElement(tax_scheme, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxTypeCode").text = "VAT"

            # === LEGAL MONETARY TOTAL ===
            monetary_total = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal")

            line_ext_amount = etree.SubElement(monetary_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount")
            line_ext_amount.set("currencyID", "PEN")
            line_ext_amount.text = f"{subtotal:.2f}"

            tax_inc_amount = etree.SubElement(monetary_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxInclusiveAmount")
            tax_inc_amount.set("currencyID", "PEN")
            tax_inc_amount.text = f"{float(venta.total):.2f}"

            payable_amount = etree.SubElement(monetary_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount")
            payable_amount.set("currencyID", "PEN")
            payable_amount.text = f"{float(venta.total):.2f}"

            # === INVOICE LINES (Items) ===
            for idx, item in enumerate(venta.items, start=1):
                invoice_line = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine")
                etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = str(idx)

                # Cantidad
                invoiced_qty = etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoicedQuantity")
                invoiced_qty.set("unitCode", "NIU")  # NIU = Unidad
                invoiced_qty.set("unitCodeListAgencyName", "United Nations Economic Commission for Europe")
                invoiced_qty.set("unitCodeListID", "UN/ECE rec 20")
                invoiced_qty.text = f"{float(item.cantidad):.2f}"

                # Monto de la línea (sin IGV)
                item_subtotal = float(item.subtotal) / 1.18
                line_ext = etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount")
                line_ext.set("currencyID", "PEN")
                line_ext.text = f"{item_subtotal:.2f}"

                # Precio unitario (sin IGV)
                pricing_ref = etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PricingReference")
                alt_condition = etree.SubElement(pricing_ref, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AlternativeConditionPrice")
                price_amount = etree.SubElement(alt_condition, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceAmount")
                price_amount.set("currencyID", "PEN")
                price_amount.text = f"{float(item.precio_unitario):.2f}"
                price_type_code = etree.SubElement(alt_condition, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceTypeCode")
                price_type_code.set("listAgencyName", "PE:SUNAT")
                price_type_code.set("listName", "Tipo de Precio")
                price_type_code.set("listURI", "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16")
                price_type_code.text = "01"

                # IGV del item
                item_igv = item_subtotal * 0.18
                item_tax_total = etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal")
                item_tax_amount = etree.SubElement(item_tax_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount")
                item_tax_amount.set("currencyID", "PEN")
                item_tax_amount.text = f"{item_igv:.2f}"

                item_tax_subtotal = etree.SubElement(item_tax_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxSubtotal")
                item_taxable = etree.SubElement(item_tax_subtotal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxableAmount")
                item_taxable.set("currencyID", "PEN")
                item_taxable.text = f"{item_subtotal:.2f}"

                item_tax_amt2 = etree.SubElement(item_tax_subtotal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount")
                item_tax_amt2.set("currencyID", "PEN")
                item_tax_amt2.text = f"{item_igv:.2f}"

                item_tax_cat = etree.SubElement(item_tax_subtotal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxCategory")
                etree.SubElement(item_tax_cat, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Percent").text = "18.00"
                tax_exemption_code = etree.SubElement(item_tax_cat, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxExemptionReasonCode")
                tax_exemption_code.set("listAgencyName", "PE:SUNAT")
                tax_exemption_code.set("listName", "Afectacion del IGV")
                tax_exemption_code.set("listURI", "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07")
                tax_exemption_code.text = "10"

                item_tax_scheme = etree.SubElement(item_tax_cat, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme")
                tax_id = etree.SubElement(item_tax_scheme, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
                tax_id.set("schemeAgencyName", "PE:SUNAT")
                tax_id.set("schemeID", "UN/ECE 5153")
                tax_id.set("schemeName", "Codigo de tributos")
                tax_id.text = "1000"
                etree.SubElement(item_tax_scheme, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name").text = "IGV"
                etree.SubElement(item_tax_scheme, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxTypeCode").text = "VAT"

                # Descripción del item (limpiar tabs y saltos de línea)
                item_elem = etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Item")
                item_desc = etree.SubElement(item_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Description")
                # Limpiar el nombre del producto: quitar tabs, saltos de línea y tomar solo la primera parte antes del primer tab
                producto_nombre_limpio = str(item.producto_nombre).split('\t')[0].strip()
                item_desc.text = producto_nombre_limpio

                # Precio unitario sin IGV
                price = etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Price")
                price_amt = etree.SubElement(price, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceAmount")
                precio_sin_igv = float(item.precio_unitario) / 1.18
                price_amt.set("currencyID", "PEN")
                price_amt.text = f"{precio_sin_igv:.2f}"

            # Generar XML string con encoding ISO-8859-1 como SUNAT requiere
            xml_string = etree.tostring(invoice, pretty_print=True, xml_declaration=True, encoding='ISO-8859-1')

            # Guardar XML
            xml_filename = f"{self.ruc}-03-{venta.numero_completo}.xml"
            xml_path = os.path.join("xml_generados", xml_filename)

            with open(xml_path, 'wb') as f:
                f.write(xml_string)

            return xml_path, xml_string

        except Exception as e:
            print(f"Error generando XML: {str(e)}")
            raise

    def firmar_xml(self, xml_path, xml_string):
        """
        Firma digitalmente el XML con el certificado .pfx usando signxml
        """
        try:
            from signxml import XMLSigner
            from cryptography.hazmat.primitives import serialization

            # Monkeypatch para permitir SHA1 (SUNAT lo requiere)
            XMLSigner.check_deprecated_methods = lambda self: None

            # Cargar el certificado
            with open(self.cert_path, 'rb') as f:
                pfx_data = f.read()

            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data,
                self.cert_password.encode() if self.cert_password else None,
                backend=default_backend()
            )

            # Parsear el XML
            root = etree.fromstring(xml_string)

            # Encontrar el ExtensionContent donde va la firma
            ext_content = root.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent')

            if ext_content is None:
                raise Exception("No se encontró ExtensionContent en el XML")

            # Convertir clave privada a formato PEM
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )

            # Convertir certificado a formato PEM
            cert_pem = certificate.public_bytes(serialization.Encoding.PEM)

            # Configurar el firmante con los parámetros correctos para SUNAT
            # SUNAT requiere SHA1 aunque esté deprecado
            signer = XMLSigner(
                signature_algorithm="rsa-sha1",
                digest_algorithm="sha1",
                c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
            )

            # Firmar el XML - enveloped signature
            # No especificamos reference_uri para que firme todo el documento
            signed_root = signer.sign(
                root,
                key=key_pem,
                cert=cert_pem,
                always_add_key_value=False
            )

            # Encontrar el ExtensionContent en el árbol firmado (no en el original)
            ext_content_signed = signed_root.find('.//{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent')

            # Mover la firma al ExtensionContent
            signature_elem = signed_root.find('.//{http://www.w3.org/2000/09/xmldsig#}Signature')
            if signature_elem is not None and ext_content_signed is not None:
                # Remover la firma de donde está
                parent = signature_elem.getparent()
                if parent is not None:
                    parent.remove(signature_elem)

                # Agregar la firma al ExtensionContent
                ext_content_signed.append(signature_elem)

                # Agregar el atributo Id a la firma - debe ser "SignSUNAT" según formato SUNAT
                signature_elem.set('Id', 'SignSUNAT')

                # Limpiar saltos de línea del certificado X509
                x509_cert_elem = signature_elem.find('.//{http://www.w3.org/2000/09/xmldsig#}X509Certificate')
                if x509_cert_elem is not None and x509_cert_elem.text:
                    # Quitar todos los saltos de línea y espacios del certificado
                    x509_cert_elem.text = x509_cert_elem.text.replace('\n', '').replace('\r', '').replace(' ', '')

            # Generar el XML firmado SIN pretty_print para evitar saltos de línea
            xml_firmado = etree.tostring(signed_root, pretty_print=False, xml_declaration=True, encoding='UTF-8')

            # Guardar el XML firmado
            with open(xml_path, 'wb') as f:
                f.write(xml_firmado)

            print(f"✅ XML firmado correctamente con signxml")
            return xml_path, xml_firmado

        except Exception as e:
            print(f"Error firmando XML: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def enviar_a_sunat(self, xml_path, venta):
        """
        Envía el comprobante a SUNAT usando SOAP directo
        """
        try:
            # Leer el XML
            with open(xml_path, 'rb') as f:
                xml_content = f.read()

            # Nombre del archivo ZIP
            zip_filename = f"{self.ruc}-03-{venta.numero_completo}.zip"
            zip_path = os.path.join("xml_generados", zip_filename)

            # Crear ZIP con el XML
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(os.path.basename(xml_path), xml_content)

            # Leer el ZIP y codificarlo en base64
            with open(zip_path, 'rb') as f:
                zip_content = f.read()

            zip_base64 = base64.b64encode(zip_content).decode()

            print(f"📡 Enviando a SUNAT: {self.url_servicio}")
            print(f"   Archivo: {zip_filename}")
            print(f"   Usuario: {self.ruc}{self.usuario_sol}")

            # Crear el request SOAP manualmente con el formato correcto para SUNAT
            soap_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.sunat.gob.pe">
   <soapenv:Header/>
   <soapenv:Body>
      <ser:sendBill>
         <fileName>{zip_filename}</fileName>
         <contentFile>{zip_base64}</contentFile>
      </ser:sendBill>
   </soapenv:Body>
</soapenv:Envelope>"""

            # Headers SOAP - SUNAT requiere SOAPAction específico
            headers = {
                'Content-Type': 'text/xml;charset=UTF-8',
                'SOAPAction': 'urn:sendBill',
            }

            # Debug: guardar el request SOAP
            with open("sunat_request_debug.xml", "w", encoding="utf-8") as f:
                f.write(soap_request)
            print(f"💾 Request SOAP guardado en: sunat_request_debug.xml")

            # Enviar request HTTP
            response = requests.post(
                self.url_servicio,
                data=soap_request.encode('utf-8'),
                headers=headers,
                auth=HTTPBasicAuth(f"{self.ruc}{self.usuario_sol}", self.clave_sol),
                timeout=30
            )

            print(f"📥 Respuesta de SUNAT:")
            print(f"   Status: {response.status_code}")

            # Guardar la respuesta completa para debug
            with open("sunat_response_debug.xml", "wb") as f:
                f.write(response.content)
            print(f"💾 Respuesta guardada en: sunat_response_debug.xml")

            if response.status_code == 200:
                # Parsear la respuesta SOAP
                response_root = etree.fromstring(response.content)

                # Buscar si hay un SOAP Fault (error)
                namespaces = {
                    'soap-env': 'http://schemas.xmlsoap.org/soap/envelope/',
                    'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                    'ns2': 'http://service.sunat.gob.pe'
                }

                # Verificar si hay un Fault
                fault = response_root.find('.//soap-env:Fault', namespaces)
                if fault is None:
                    fault = response_root.find('.//soap:Fault', namespaces)

                if fault is not None:
                    # Es un error de SUNAT
                    faultcode = fault.find('.//faultcode')
                    faultstring = fault.find('.//faultstring')

                    error_code = faultcode.text if faultcode is not None else 'UNKNOWN'
                    error_msg = faultstring.text if faultstring is not None else 'Sin descripción'

                    print(f"❌ SOAP Fault de SUNAT:")
                    print(f"   Código: {error_code}")
                    print(f"   Mensaje: {error_msg}")

                    return {
                        'success': False,
                        'message': f'Error SUNAT [{error_code}]: {error_msg}'
                    }

                # Buscar applicationResponse
                app_response = response_root.find('.//applicationResponse', namespaces)
                if app_response is None:
                    app_response = response_root.find('.//{http://service.sunat.gob.pe}applicationResponse')

                if app_response is not None and app_response.text:
                    # Decodificar el CDR
                    cdr_zip = base64.b64decode(app_response.text)

                    # Guardar el CDR
                    cdr_filename = f"R-{zip_filename}"
                    cdr_path = os.path.join("cdr_recibidos", cdr_filename)

                    with open(cdr_path, 'wb') as f:
                        f.write(cdr_zip)

                    print(f"✅ CDR guardado en: {cdr_path}")

                    # Extraer el CDR
                    try:
                        with zipfile.ZipFile(cdr_path, 'r') as zipf:
                            zipf.extractall("cdr_recibidos")
                            print(f"✅ CDR extraído correctamente")
                    except:
                        print(f"⚠️  CDR no se pudo extraer")

                    return {
                        'success': True,
                        'cdr_path': cdr_path,
                        'message': 'Comprobante enviado y aceptado por SUNAT'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Respuesta de SUNAT sin CDR. Ver sunat_response_debug.xml'
                    }

            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"   Respuesta: {response.text[:500]}")

                return {
                    'success': False,
                    'message': f'Error HTTP {response.status_code}: {response.text[:200]}'
                }

        except requests.exceptions.HTTPError as e:
            print(f"❌ Error HTTP: {e}")
            return {
                'success': False,
                'message': f'Error HTTP: {str(e)}'
            }

        except Exception as e:
            print(f"❌ Error general:")
            print(f"   {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Error al enviar a SUNAT: {str(e)}'
            }

    def enviar_a_sunat_api_rest(self, xml_path, venta):
        """
        Envía el comprobante a SUNAT usando API REST con autenticación OAuth
        """
        try:
            # Leer el XML
            with open(xml_path, 'rb') as f:
                xml_content = f.read()

            # Nombre del archivo ZIP
            zip_filename = f"{self.ruc}-03-{venta.numero_completo}.zip"
            zip_path = os.path.join("xml_generados", zip_filename)

            # Crear ZIP con el XML
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(os.path.basename(xml_path), xml_content)

            # Leer el ZIP y codificarlo en base64
            with open(zip_path, 'rb') as f:
                zip_content = f.read()

            zip_base64 = base64.b64encode(zip_content).decode()

            print(f"📡 Enviando a SUNAT vía API REST")
            print(f"   URL: {self.api_url}")
            print(f"   Client ID: {self.api_client_id[:20]}...")
            print(f"   Archivo: {zip_filename}")

            # Paso 1: Obtener el token de acceso
            print(f"🔑 Obteniendo token de acceso...")
            token_url = f"{self.api_url}/api/v1/oauth/token"

            token_data = {
                'grant_type': 'client_credentials',
                'client_id': self.api_client_id,
                'client_secret': self.api_client_secret,
                'scope': 'https://api.sunat.gob.pe/v1/contribuyente/contribuyentes'
            }

            token_response = requests.post(token_url, data=token_data, timeout=30)

            if token_response.status_code != 200:
                print(f"❌ Error obteniendo token: {token_response.status_code}")
                print(f"   Respuesta: {token_response.text[:500]}")
                return {
                    'success': False,
                    'message': f'Error obteniendo token de acceso: {token_response.text[:200]}'
                }

            token_json = token_response.json()
            access_token = token_json.get('access_token')

            if not access_token:
                return {
                    'success': False,
                    'message': 'No se recibió access_token en la respuesta'
                }

            print(f"✅ Token obtenido correctamente")

            # Paso 2: Enviar el comprobante con el token
            print(f"📤 Enviando comprobante...")
            envio_url = f"{self.api_url}/api/v1/contribuyente/contribuyentes/{self.ruc}/comprobantes"

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'archivo': {
                    'nomArchivo': zip_filename,
                    'arcGreZip': zip_base64,
                    'hashZip': hashlib.sha256(zip_content).hexdigest()
                }
            }

            # Debug: guardar el payload
            with open("sunat_api_request_debug.json", "w", encoding="utf-8") as f:
                import json
                json.dump(payload, f, indent=2, ensure_ascii=False)
            print(f"💾 Request API guardado en: sunat_api_request_debug.json")

            envio_response = requests.post(
                envio_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            print(f"📥 Respuesta de SUNAT API:")
            print(f"   Status: {envio_response.status_code}")

            # Guardar la respuesta completa para debug
            with open("sunat_api_response_debug.json", "wb") as f:
                f.write(envio_response.content)
            print(f"💾 Respuesta guardada en: sunat_api_response_debug.json")

            if envio_response.status_code == 200 or envio_response.status_code == 201:
                response_json = envio_response.json()

                # Verificar si hay CDR en la respuesta
                if 'cdr' in response_json or 'constanciaRecepcion' in response_json:
                    # Extraer el CDR
                    cdr_data = response_json.get('cdr') or response_json.get('constanciaRecepcion')

                    if isinstance(cdr_data, str):
                        # Si viene en base64
                        cdr_zip = base64.b64decode(cdr_data)
                    else:
                        # Si viene como objeto
                        cdr_content = cdr_data.get('arcGreZip') or cdr_data.get('contenido')
                        if cdr_content:
                            cdr_zip = base64.b64decode(cdr_content)
                        else:
                            cdr_zip = None

                    if cdr_zip:
                        # Guardar el CDR
                        cdr_filename = f"R-{zip_filename}"
                        cdr_path = os.path.join("cdr_recibidos", cdr_filename)

                        with open(cdr_path, 'wb') as f:
                            f.write(cdr_zip)

                        print(f"✅ CDR guardado en: {cdr_path}")

                        # Extraer el CDR
                        try:
                            with zipfile.ZipFile(cdr_path, 'r') as zipf:
                                zipf.extractall("cdr_recibidos")
                                print(f"✅ CDR extraído correctamente")
                        except:
                            print(f"⚠️  CDR no se pudo extraer")

                        return {
                            'success': True,
                            'cdr_path': cdr_path,
                            'message': 'Comprobante enviado y aceptado por SUNAT (API REST)',
                            'response_data': response_json
                        }
                    else:
                        return {
                            'success': True,
                            'message': 'Comprobante recibido por SUNAT (API REST) - Sin CDR en respuesta',
                            'response_data': response_json
                        }
                else:
                    return {
                        'success': True,
                        'message': 'Comprobante recibido por SUNAT (API REST)',
                        'response_data': response_json
                    }

            else:
                print(f"❌ Error HTTP: {envio_response.status_code}")
                print(f"   Respuesta: {envio_response.text[:500]}")

                return {
                    'success': False,
                    'message': f'Error HTTP {envio_response.status_code}: {envio_response.text[:200]}'
                }

        except Exception as e:
            print(f"❌ Error general en API REST:")
            print(f"   {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Error al enviar a SUNAT API REST: {str(e)}'
            }

    def procesar_venta(self, venta):
        """
        Proceso completo: generar XML, firmar y enviar a SUNAT
        """
        try:
            # 1. Generar XML
            xml_path, xml_string = self.generar_xml_boleta(venta)

            # 2. Firmar XML
            xml_path, xml_firmado = self.firmar_xml(xml_path, xml_string)

            # 3. Enviar a SUNAT (usar API REST si está configurado, sino SOAP)
            if self.usar_api_rest:
                print(f"📡 Usando método API REST para envío...")
                resultado = self.enviar_a_sunat_api_rest(xml_path, venta)
            else:
                print(f"📡 Usando método SOAP para envío...")
                resultado = self.enviar_a_sunat(xml_path, venta)

            return resultado

        except Exception as e:
            return {
                'success': False,
                'message': f'Error en el proceso: {str(e)}'
            }
