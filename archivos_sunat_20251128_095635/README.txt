============================================================
ARCHIVOS PARA ENVIAR A SUNAT
============================================================

Boleta: B001-00000010
RUC: 10433050709
Fecha de extracción: 2025-11-28 09:56:35

ARCHIVOS INCLUIDOS:

1. XML de la boleta (1_XML_BOLETA_*.xml)
   - Archivo XML firmado digitalmente de la boleta electrónica
   - Formato UBL 2.1 según estándar SUNAT

2. Trama SOAP Request (2_SOAP_REQUEST_*.xml)
   - Solicitud SOAP enviada a SUNAT
   - Incluye el archivo ZIP en base64
   - Método: sendBill

3. Trama SOAP Response (3_SOAP_RESPONSE_*.xml)
   - Respuesta recibida de SUNAT
   - Puede contener errores o CDR (Constancia de Recepción)

4. Archivo ZIP (4_ZIP_ENVIADO_*.zip) [BONUS]
   - Archivo ZIP que contiene el XML
   - Este es el archivo que se envía a SUNAT

============================================================
NOTAS:
============================================================

- Estos archivos son necesarios para reportar problemas a SUNAT
- El error 0111 indica problemas con el formato del XML o la firma
- Verificar que el certificado digital sea válido
- Verificar que las credenciales SOL sean correctas

