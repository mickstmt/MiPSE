# Sistema de Facturación Electrónica - SUNAT

## Estado Actual del Proyecto

### ✅ Completado y Funcionando

1. **Integración SUNAT Completa**
   - ✅ Generación de XML en formato UBL 2.1
   - ✅ Firma digital con certificado (Serie: 5e96483cba10b45)
   - ✅ Envío SOAP a SUNAT
   - ✅ Recepción y procesamiento de CDR
   - ✅ **FUNCIONANDO EN AMBIENTE BETA**

2. **Configuración SUNAT**
   - ✅ Certificado digital subido y activo
   - ✅ Usuario SOL: VOTROEXP
   - ✅ RUC: 10433050709
   - ✅ Serie de boletas: B001
   - ✅ Correo registrado: ventas@izistoreperu.com

3. **Código y Sistema**
   - ✅ Base de datos PostgreSQL configurada
   - ✅ Modelos de datos completos
   - ✅ Integración con APISPeru (DNI/RUC)
   - ✅ Sistema de ventas funcional
   - ✅ Generación automática de comprobantes

### ⏳ Pendiente de Activación

**SEE del Contribuyente en PRODUCCIÓN**
- Checkbox marcado: ✅ "Deseo emitir a través del SEE - Del Contribuyente"
- Permisos asignados: ✅ Todos los permisos necesarios
- Estado: Esperando activación de SUNAT (24-48 horas)

## Cómo Usar el Sistema

### Ambiente BETA (Actual - Funcionando)

El sistema está configurado en modo BETA y funciona perfectamente:

```bash
# Ejecutar prueba en BETA
python crear_venta_prueba.py
```

**Resultado esperado:**
```
✅ SUCCESS: Comprobante enviado y aceptado por SUNAT
📦 CDR recibido: cdr_recibidos\R-10433050709-03-B001-00000010.zip
```

### Cambiar a PRODUCCIÓN

Cuando SUNAT active tu afiliación al SEE del Contribuyente:

1. Editar `.env` y cambiar:
```env
SUNAT_AMBIENTE=PRODUCCION
```

2. Ejecutar la prueba:
```bash
python crear_venta_prueba.py
```

3. Si funciona, verás el mismo resultado exitoso

## Verificar Activación de PRODUCCIÓN

Para saber si ya está activo:

```bash
# Cambiar temporalmente a PRODUCCION en .env
SUNAT_AMBIENTE=PRODUCCION

# Ejecutar prueba
python crear_venta_prueba.py

# Si sale error "0111 - No tiene el perfil" → Aún no activo
# Si sale "✅ SUCCESS" → Ya está activo!
```

## Estructura del Proyecto

```
sistema-ventas-izistore/
├── .env                          # Configuración (credenciales SUNAT, DB, etc.)
├── app.py                        # Aplicación Flask principal
├── models.py                     # Modelos de base de datos
├── config.py                     # Configuración central
├── sunat_service.py              # Servicio de integración SUNAT
├── crear_venta_prueba.py         # Script de prueba
├── certificados/
│   ├── CT2510134109.pfx          # Certificado digital con clave privada
│   └── CT2510134109.cer          # Certificado público (subido a SUNAT)
├── xml_generados/                # XMLs generados de comprobantes
├── cdr_recibidos/                # CDRs recibidos de SUNAT
└── comprobantes/                 # PDFs de comprobantes

```

## Configuración de Variables de Entorno

Archivo `.env` principal:

```env
# Base de datos
DB_USER=postgres
DB_PASSWORD=***
DB_HOST=localhost
DB_PORT=5432
DB_NAME=izistore_ventas

# SUNAT
SUNAT_RUC=10433050709
SUNAT_USUARIO_SOL=VOTROEXP
SUNAT_CLAVE_SOL=***
SUNAT_AMBIENTE=BETA              # Cambiar a PRODUCCION cuando esté activo

# Certificado digital
CERT_PATH=certificados/CT2510134109.pfx
CERT_PASSWORD=***

# Empresa
EMPRESA_RUC=10433050709
EMPRESA_RAZON_SOCIAL=LEON GARGATE JHONATAN DAVIS
EMPRESA_NOMBRE_COMERCIAL=Izistore Peru
EMPRESA_DIRECCION=Av Fray Bartolome de las Casas 249, San Martin de Porres Lima
EMPRESA_TELEFONO=935403614
EMPRESA_EMAIL=ventas@izistoreperu.com
EMPRESA_UBIGEO=150117

# Serie de comprobantes
SERIE_BOLETA=B001
```

## Integración con la Aplicación Web

Desde tu aplicación Flask, puedes enviar comprobantes así:

```python
from sunat_service import SUNATService
import config

# Crear servicio SUNAT
sunat = SUNATService(config.Config)

# Después de registrar una venta:
resultado = sunat.procesar_venta(venta)

if resultado['success']:
    print(f"✅ Comprobante enviado correctamente")
    print(f"CDR: {resultado.get('cdr_path')}")
else:
    print(f"❌ Error: {resultado['message']}")
```

## Solución de Problemas

### Error "No tiene el perfil para enviar comprobantes"

**En BETA:** No debería ocurrir
**En PRODUCCIÓN:** Significa que aún no se activó el SEE del Contribuyente

**Solución:**
1. Esperar 24-48 horas después de marcar el checkbox
2. Si persiste, contactar Mesa de Ayuda SUNAT: (01) 315-0730

### Error de certificado

**Síntoma:** Error al firmar XML
**Solución:** Verificar que `CERT_PATH` y `CERT_PASSWORD` sean correctos

### Error de base de datos

**Síntoma:** Error al conectar a PostgreSQL
**Solución:** Verificar credenciales en `.env`

## Próximos Pasos

1. **Esperar activación de PRODUCCIÓN** (24-48 horas)
2. **Probar en PRODUCCIÓN** cuando esté activo
3. **Integrar con la interfaz web** de tu sistema de ventas
4. **Configurar envío automático** de comprobantes
5. **Implementar generación de PDF** de boletas

## Contacto SUNAT

- **Mesa de Ayuda:** (01) 315-0730
- **Portal:** https://www.sunat.gob.pe/
- **Email registrado:** ventas@izistoreperu.com

## Notas Técnicas

- **Formato XML:** UBL 2.1 (estándar SUNAT)
- **Firma digital:** SHA1 con RSA (requerido por SUNAT)
- **Protocolo:** SOAP 1.1
- **Encoding:** ISO-8859-1 en XML, UTF-8 internamente
- **Compresión:** ZIP antes de enviar

## Verificación del Sistema

Ejecutar todas las verificaciones:

```bash
python test_configuracion_sunat.py
```

Resultado esperado: **8/8 verificaciones pasadas** ✅
