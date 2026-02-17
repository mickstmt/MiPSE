import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # PostgreSQL - Codificar la contraseña para manejar caracteres especiales
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = quote_plus(os.getenv('DB_PASSWORD', ''))
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'izistore_ventas')
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # WooCommerce (MySQL) - Lectura de productos
    WOO_DB_USER = os.getenv('WOO_DB_USER', 'root')
    WOO_DB_PASSWORD = os.getenv('WOO_DB_PASSWORD', '')
    WOO_DB_HOST = os.getenv('WOO_DB_HOST', 'localhost')
    WOO_DB_PORT = os.getenv('WOO_DB_PORT', '3306')
    WOO_DB_NAME = os.getenv('WOO_DB_NAME', 'wordpress')
    
    # URI de conexión para WooCommerce (MySQL)
    # Se usará para consultas directas vía SQLAlchemy o conexión manual
    WOO_DATABASE_URI = f"mysql+pymysql://{WOO_DB_USER}:{WOO_DB_PASSWORD}@{WOO_DB_HOST}:{WOO_DB_PORT}/{WOO_DB_NAME}"
    
    # APIs Peru
    APISPERU_TOKEN = os.getenv('APISPERU_TOKEN')
    APISPERU_DNI_URL = 'https://dniruc.apisperu.com/api/v1/dni'
    APISPERU_RUC_URL = 'https://dniruc.apisperu.com/api/v1/ruc'
    
    # SUNAT - Autenticación SOAP
    SUNAT_RUC = os.getenv('SUNAT_RUC', '10433050709')
    SUNAT_USUARIO_SOL = os.getenv('SUNAT_USUARIO_SOL')
    SUNAT_CLAVE_SOL = os.getenv('SUNAT_CLAVE_SOL')

    # SUNAT - API REST (opcional, si está configurado se usa en lugar de SOAP)
    SUNAT_API_CLIENT_ID = os.getenv('SUNAT_API_CLIENT_ID')
    SUNAT_API_CLIENT_SECRET = os.getenv('SUNAT_API_CLIENT_SECRET')
    SUNAT_API_URL = os.getenv('SUNAT_API_URL')

    # URLs SUNAT (Beta para pruebas, Producción para envío real)
    SUNAT_URL_BETA = 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService'
    SUNAT_URL_PRODUCCION = 'https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService'

    # WSDL URLs (para el cliente SOAP)
    SUNAT_WSDL_BETA = 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl'
    SUNAT_WSDL_PRODUCCION = 'https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService?wsdl'

    # Ambiente activo (lee desde .env: BETA o PRODUCCION)
    SUNAT_AMBIENTE = os.getenv('SUNAT_AMBIENTE', 'PRODUCCION')
    
    # Certificado Digital
    CERT_PATH = os.getenv('CERT_PATH', 'certificados/certificado.pfx')
    CERT_PASSWORD = os.getenv('CERT_PASSWORD')
    
    # Datos de la empresa
    EMPRESA_RUC = os.getenv('EMPRESA_RUC', '10433050709')
    EMPRESA_RAZON_SOCIAL = os.getenv('EMPRESA_RAZON_SOCIAL', 'LEON GARGATE JHONATAN DAVIS')
    EMPRESA_NOMBRE_COMERCIAL = os.getenv('EMPRESA_NOMBRE_COMERCIAL', 'Izistore Peru')
    EMPRESA_DIRECCION = os.getenv('EMPRESA_DIRECCION', 'Av Fray Bartolome de las Casas 249, San Martin de Porres Lima')
    EMPRESA_TELEFONO = os.getenv('EMPRESA_TELEFONO', '935403614')
    EMPRESA_EMAIL = os.getenv('EMPRESA_EMAIL', 'ventas@izistoreperu.com')
    EMPRESA_UBIGEO = os.getenv('EMPRESA_UBIGEO', '150117')
    
    # Configuración de boletas
    # Serie para boletas electrónicas (debe tener 4 caracteres)
    # Para RUC 10 (personas naturales) puede ser: E001, E002, etc.
    # Para RUC 20 (empresas): B001, B002, etc.
    SERIE_BOLETA = os.getenv('SERIE_BOLETA', 'B001')
    
    # Carpetas
    COMPROBANTES_PATH = 'comprobantes'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    
    # Horarios de envío automático (24h format)
    HORARIOS_ENVIO = ['12:00', '18:00']
