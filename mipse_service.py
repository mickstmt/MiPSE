"""
Servicio de integracion con MiPSE (Proveedor de Servicios Electronicos)
para facturacion electronica SUNAT

Flujo segun manual MiPSE:
1. Obtener token_acceso con usuario/password de la empresa
2. Usar token_acceso para firmar XML (cpe/generar)
3. Usar token_acceso para enviar a SUNAT (cpe/enviar)
"""

import sys

# Configurar encoding para Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

import os
import base64
import requests
from datetime import datetime, timedelta


class MiPSEService:
    """Servicio para enviar comprobantes electronicos via MiPSE"""

    def __init__(self, config=None):
        # Cargar configuracion desde variables de entorno o config
        if config:
            self.url = getattr(config, 'MIPSE_URL', os.getenv('MIPSE_URL', 'https://api.mipse.pe'))
            self.system = getattr(config, 'MIPSE_SYSTEM', os.getenv('MIPSE_SYSTEM', 'produccion'))
            self.usuario = getattr(config, 'MIPSE_USUARIO', os.getenv('MIPSE_USUARIO'))
            self.password = getattr(config, 'MIPSE_PASSWORD', os.getenv('MIPSE_PASSWORD'))
            self.ruc = getattr(config, 'EMPRESA_RUC', os.getenv('EMPRESA_RUC'))
            self.razon_social = getattr(config, 'EMPRESA_RAZON_SOCIAL', os.getenv('EMPRESA_RAZON_SOCIAL'))
        else:
            self.url = os.getenv('MIPSE_URL', 'https://api.mipse.pe')
            self.system = os.getenv('MIPSE_SYSTEM', 'produccion')
            self.usuario = os.getenv('MIPSE_USUARIO')
            self.password = os.getenv('MIPSE_PASSWORD')
            self.ruc = os.getenv('EMPRESA_RUC')
            self.razon_social = os.getenv('EMPRESA_RAZON_SOCIAL')

        self.token_acceso = None
        self.token_expiry = None

        print(f"[MiPSE] Configurado:")
        print(f"   URL: {self.url}")
        print(f"   Sistema: {self.system}")
        print(f"   Usuario: {self.usuario}")
        print(f"   RUC: {self.ruc}")

    def obtener_token_acceso(self):
        """
        Obtiene el token_acceso usando usuario/password de la empresa.
        El token expira en 600 segundos (10 minutos).
        """
        try:
            url = f"{self.url}/pro/{self.system}/auth/cpe/token"

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

            # Segun manual: usuario y contraseña (con ñ)
            payload = {
                "usuario": self.usuario,
                "contraseña": self.password
            }

            print(f"[MiPSE] Obteniendo token_acceso...")
            print(f"[MiPSE] URL: {url}")
            print(f"[MiPSE] Usuario: {self.usuario}")

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            print(f"[MiPSE] Respuesta: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                self.token_acceso = data.get('token_acceso')
                expira_en = int(data.get('expira_en', 600))
                self.token_expiry = datetime.now() + timedelta(seconds=expira_en - 60)  # 1 min antes

                print(f"[MiPSE] Token obtenido exitosamente")
                print(f"[MiPSE] Expira en: {expira_en} segundos")

                return {
                    'success': True,
                    'token_acceso': self.token_acceso,
                    'expira_en': expira_en
                }
            else:
                error_msg = response.text
                try:
                    error_json = response.json()
                    error_msg = (
                        error_json.get('mensaje') or 
                        error_json.get('message') or 
                        error_json.get('errores') or 
                        error_json.get('error') or 
                        response.text
                    )
                except:
                    pass
                print(f"[MiPSE] Error obteniendo token: {error_msg}")
                return {
                    'success': False,
                    'error': f"Error {response.status_code}: {error_msg}",
                    'message': f"Error {response.status_code}: {error_msg}"
                }

        except Exception as e:
            print(f"[MiPSE] Excepcion obteniendo token: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': str(e)
            }

    def _get_token(self):
        """Obtiene token valido, renovando si es necesario"""
        if not self.token_acceso or not self.token_expiry or datetime.now() >= self.token_expiry:
            result = self.obtener_token_acceso()
            if not result['success']:
                raise Exception(f"Error obteniendo token: {result.get('error')}")
        return self.token_acceso

    def _get_headers(self):
        """Retorna headers con autenticacion"""
        token = self._get_token()
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

    def firmar_xml(self, nombre_archivo, contenido_xml_base64):
        """
        Firma el XML usando MiPSE (endpoint cpe/generar)

        Args:
            nombre_archivo: Nombre del archivo sin extension (ej: 10433050709-03-B001-00000001)
            contenido_xml_base64: Contenido del XML en base64

        Response esperada:
            {
                "estado": 200,
                "xml": "base64...",
                "codigo_hash": "vEZR9aRkrRc02s9PfpL//TmPFbA=",
                "mensaje": "XML firmado correctamente",
                "external_id": "uuid"
            }
        """
        try:
            url = f"{self.url}/pro/{self.system}/cpe/generar"

            payload = {
                "tipo_integracion": 0,
                "nombre_archivo": nombre_archivo,
                "contenido_archivo": contenido_xml_base64
            }

            print(f"[MiPSE] Firmando XML: {nombre_archivo}")
            print(f"[MiPSE] URL: {url}")

            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=60)

            print(f"[MiPSE] Respuesta firma: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                estado = data.get('estado')
                xml_firmado = data.get('xml')
                codigo_hash = data.get('codigo_hash')
                mensaje = data.get('mensaje')
                external_id = data.get('external_id')

                print(f"[MiPSE] Estado: {estado}")
                print(f"[MiPSE] Mensaje: {mensaje}")
                if codigo_hash:
                    print(f"[MiPSE] Hash: {codigo_hash}")

                return {
                    'success': estado == 200 or xml_firmado is not None,
                    'xml_firmado': xml_firmado,
                    'hash': codigo_hash,
                    'mensaje': mensaje,
                    'external_id': external_id
                }
            else:
                error_msg = response.text
                try:
                    error_json = response.json()
                    error_msg = error_json.get('message') or error_json.get('error') or response.text
                except:
                    pass
                print(f"[MiPSE] Error firmando: {error_msg}")
                return {
                    'success': False,
                    'error': f"Error {response.status_code}: {error_msg}",
                    'message': f"Error en firma: {error_msg}"
                }

        except Exception as e:
            print(f"[MiPSE] Excepcion firmando XML: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Excepción en firma: {str(e)}"
            }

    def enviar_comprobante(self, nombre_archivo, xml_firmado_base64):
        """
        Envia el comprobante firmado a SUNAT via MiPSE (endpoint cpe/enviar)

        Args:
            nombre_archivo: Nombre del archivo sin extension
            xml_firmado_base64: XML firmado en base64

        Response esperada:
            {
                "estado": 200,
                "mensaje": "La Factura numero F001-17, ha sido aceptada",
                "cdr": "base64..."
            }
        """
        try:
            url = f"{self.url}/pro/{self.system}/cpe/enviar"

            payload = {
                "nombre_xml_firmado": nombre_archivo,
                "contenido_xml_firmado": xml_firmado_base64
            }

            print(f"[MiPSE] Enviando a SUNAT: {nombre_archivo}")
            print(f"[MiPSE] URL: {url}")

            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=120)

            print(f"[MiPSE] Respuesta envio: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                estado = data.get('estado')
                mensaje = data.get('mensaje')
                cdr = data.get('cdr')
                ticket = data.get('ticket')  # Para resumenes/anulaciones

                print(f"[MiPSE] Estado: {estado}")
                print(f"[MiPSE] Mensaje: {mensaje}")

                return {
                    'success': estado == 200,
                    'estado': estado,
                    'mensaje': mensaje,
                    'cdr': cdr,
                    'ticket': ticket,
                    'respuesta_completa': data
                }
            else:
                error_text = response.text
                try:
                    error_json = response.json()
                    # Extraer el mensaje mas descriptivo
                    error_text = (
                        error_json.get('mensaje') or 
                        error_json.get('message') or 
                        error_json.get('errores') or 
                        error_json.get('error') or 
                        response.text
                    )
                except:
                    pass

                print(f"[MiPSE] Error enviando: {error_text}")
                return {
                    'success': False,
                    'estado': response.status_code,
                    'mensaje': error_text,
                    'error': error_text
                }

        except Exception as e:
            print(f"[MiPSE] Excepcion enviando: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Excepción en envío: {str(e)}"
            }

    def consultar_estado(self, nombre_archivo):
        """
        Consulta el estado de un comprobante/ticket en SUNAT

        Args:
            nombre_archivo: Nombre del archivo o ticket
        """
        try:
            url = f"{self.url}/pro/{self.system}/cpe/consultar/{nombre_archivo}"

            print(f"[MiPSE] Consultando: {nombre_archivo}")

            response = requests.get(url, headers=self._get_headers(), timeout=60)

            print(f"[MiPSE] Respuesta consulta: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': data.get('estado') == 200,
                    'estado': data.get('estado'),
                    'mensaje': data.get('mensaje'),
                    'cdr': data.get('cdr'),
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'error': f"Error {response.status_code}: {response.text}"
                }

        except Exception as e:
            print(f"[MiPSE] Excepcion consultando: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def procesar_venta(self, venta, xml_string=None):
        """
        Procesa una venta completa: genera XML, firma y envia

        Args:
            venta: Objeto Venta con los datos del comprobante
            xml_string: XML ya generado (opcional). Si no se provee, se genera.
        """
        try:
            # Generar nombre del archivo
            # Formato: RUC-TIPO-SERIE-CORRELATIVO
            # Tipo 03 = Boleta, 01 = Factura, 07 = Nota de Crédito
            tipo_comprobante = getattr(venta, 'tipo_comprobante', None)
            if tipo_comprobante == 'NOTA_CREDITO':
                tipo_doc = "07"
            elif venta.serie and venta.serie.startswith('F'):
                tipo_doc = "01"  # Factura
            else:
                tipo_doc = "03"  # Boleta por defecto

            # Formatear correlativo con ceros
            correlativo = str(venta.correlativo).zfill(8) if isinstance(venta.correlativo, int) else venta.correlativo

            nombre_archivo = f"{self.ruc}-{tipo_doc}-{venta.serie}-{correlativo}"

            print(f"\n{'='*50}")
            print(f"[MiPSE] Procesando venta")
            print(f"   Nombre archivo: {nombre_archivo}")
            print(f"{'='*50}\n")

            # Si no hay XML, necesitamos generarlo
            if not xml_string:
                from sunat_service import SUNATService
                from config import Config

                sunat_service = SUNATService(Config)
                if tipo_doc == "07":
                    # Nota de Crédito
                    xml_path, xml_string = sunat_service.generar_xml_nota_credito(venta)
                else:
                    # Boleta o Factura
                    xml_path, xml_string = sunat_service.generar_xml_boleta(venta)

                if not xml_string:
                    return {
                        'success': False,
                        'error': "Error generando XML: xml_string vacio"
                    }

            # Convertir XML a base64
            if isinstance(xml_string, str):
                xml_bytes = xml_string.encode('utf-8')
            else:
                xml_bytes = xml_string

            xml_base64 = base64.b64encode(xml_bytes).decode('utf-8')

            # Paso 1: Firmar XML
            print("[MiPSE] Paso 1: Firmando XML...")
            firma_result = self.firmar_xml(nombre_archivo, xml_base64)
            if not firma_result['success']:
                return {
                    'success': False,
                    'error': f"Error firmando XML: {firma_result.get('error')}",
                    'message': firma_result.get('message') or firma_result.get('error')
                }

            xml_firmado = firma_result.get('xml_firmado')
            hash_cpe = firma_result.get('hash')

            # Paso 2: Enviar a SUNAT
            print("\n[MiPSE] Paso 2: Enviando a SUNAT...")
            envio_result = self.enviar_comprobante(nombre_archivo, xml_firmado)

            # Preparar resultado final
            resultado = {
                'success': envio_result.get('success', False),
                'estado': envio_result.get('estado'),
                'message': envio_result.get('mensaje'),
                'hash': hash_cpe,
                'external_id': firma_result.get('external_id'),
                'nombre_archivo': nombre_archivo,
                'xml_firmado': xml_firmado,
                'cdr': envio_result.get('cdr')
            }

            # --- MANEJO DE DUPLICADOS ---
            # Si el envio fallo pero el mensaje indica que ya existe, consultamos el estado
            if not envio_result.get('success'):
                error_msg = str(envio_result.get('mensaje', '')).lower()
                # Lista de frases comunes que indican que el comprobante ya llego a SUNAT
                duplicado_keywords = [
                    "registrado previamente", 
                    "informado anteriormente", 
                    "ya existe", 
                    "duplicado",
                    "cpe ya informado",
                    "serie y número ya están registrados"
                ]
                
                if any(kw in error_msg for kw in duplicado_keywords):
                    print(f"[MiPSE] Detectado comprobante ya informado. Consultando estado...")
                    consulta = self.consultar_estado(nombre_archivo)
                    
                    if consulta.get('success'):
                        print(f"[MiPSE] Consulta exitosa. Recuperando datos del comprobante previo.")
                        resultado['success'] = True
                        resultado['estado'] = 200
                        resultado['message'] = f"Comprobante ya registrado: {consulta.get('mensaje')}"
                        resultado['cdr'] = consulta.get('cdr')
                        envio_result['success'] = True
            # ----------------------------

            if envio_result.get('success'):
                print(f"\n[MiPSE] EXITO - Comprobante enviado correctamente")
                print(f"[MiPSE] Mensaje: {resultado.get('message')}")
            else:
                print(f"\n[MiPSE] ERROR - {envio_result.get('mensaje')}")
                resultado['message'] = envio_result.get('error') or envio_result.get('mensaje')

            return resultado

        except Exception as e:
            print(f"[MiPSE] Excepcion procesando venta: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f"Error crítico: {str(e)}"
            }


# Funcion de prueba
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    service = MiPSEService()

    print("\n=== Probando conexion con MiPSE ===\n")

    # Probar obtener token
    result = service.obtener_token_acceso()
    print(f"Resultado token: {result}")
