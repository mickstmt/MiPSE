# Guía Completa: Configuración de Certificado SUNAT

Esta guía te ayudará a configurar la facturación electrónica con SUNAT en tu sistema de ventas.

---

## 📋 PASO 1: Copiar el Certificado Digital

1. Abre el explorador de archivos
2. Copia el archivo `CT2510134109.pfx` desde tu escritorio
3. Pégalo en la carpeta: `c:\Users\FranksM\sistema-ventas-izistore\certificados\`

**Comando alternativo (PowerShell):**
```powershell
copy "C:\Users\FranksM\Desktop\CT2510134109.pfx" "c:\Users\FranksM\sistema-ventas-izistore\certificados\"
```

---

## 🔑 PASO 2: Obtener la Contraseña del Certificado

1. Abre el archivo `CT2510134109-CONTRASEÑA.txt` de tu escritorio
2. Copia la contraseña que aparece dentro
3. **GUÁRDALA** - la necesitarás en el siguiente paso

---

## ⚙️ PASO 3: Configurar Variables de Entorno

1. Abre el archivo `.env` en la raíz de tu proyecto
2. Agrega o actualiza estas líneas:

```env
# Certificado Digital de SUNAT
CERT_PATH=certificados/CT2510134109.pfx
CERT_PASSWORD=AQUI_VA_LA_CONTRASEÑA_DEL_PASO_2

# Credenciales SUNAT SOL (Para ambiente Beta/Pruebas)
SUNAT_USUARIO_SOL=MODDATOS
SUNAT_CLAVE_SOL=MODDATOS
```

**IMPORTANTE:**
- Reemplaza `AQUI_VA_LA_CONTRASEÑA_DEL_PASO_2` con la contraseña real del certificado
- Las credenciales `MODDATOS/MODDATOS` son para el ambiente de **pruebas (Beta)**
- Cuando pases a producción, cambia estas credenciales por las reales de SUNAT

---

## 📦 PASO 4: Instalar Dependencias

Abre PowerShell o CMD en la carpeta del proyecto y ejecuta:

```bash
# Activar el entorno virtual
venv\Scripts\activate

# Instalar las nuevas dependencias
pip install lxml pyOpenSSL zeep

# Verificar que se instalaron correctamente
pip list | findstr "lxml\|pyOpenSSL\|zeep"
```

Deberías ver algo como:
```
lxml              5.1.0
pyOpenSSL         23.3.0
zeep              4.2.1
```

---

## 🗄️ PASO 5: Actualizar la Base de Datos

Asegúrate de que tu base de datos tenga todas las columnas necesarias:

```bash
# Con el entorno virtual activado
python
```

Luego en el intérprete de Python:
```python
from app import app, db
with app.app_context():
    db.create_all()
    print("✓ Base de datos actualizada")
exit()
```

---

## 🚀 PASO 6: Probar el Sistema

### 6.1 Iniciar la Aplicación

```bash
python app.py
```

### 6.2 Crear una Venta de Prueba

1. Ve a http://localhost:5000
2. Inicia sesión
3. Crea una nueva venta
4. Ve al detalle de la venta

### 6.3 Enviar a SUNAT

En la página de detalle de venta verás:

**Si la venta AÚN NO fue enviada:**
- Botón azul: "📤 Enviar a SUNAT"

**Si la venta YA fue enviada:**
- Badge verde: "Enviado a SUNAT"
- Botón: "📄 Descargar XML"
- Botón: "🛡️ Descargar CDR"

---

## 📁 Archivos y Carpetas Creados

El sistema ahora tiene estas carpetas:

```
sistema-ventas-izistore/
├── certificados/          ← Tu archivo .pfx va aquí
├── xml_generados/         ← XMLs generados automáticamente
├── cdr_recibidos/         ← Respuestas de SUNAT (CDR)
└── comprobantes/          ← PDFs de boletas
```

---

## 🔄 Flujo de Facturación Electrónica

1. **Usuario crea una venta** → Estado: `PENDIENTE`
2. **Usuario hace clic en "Enviar a SUNAT"**
3. El sistema:
   - Genera el XML según formato UBL 2.1
   - Firma digitalmente con tu certificado .pfx
   - Comprime el XML en un archivo .zip
   - Envía a SUNAT vía Web Service
4. **SUNAT responde con un CDR** (Constancia de Recepción)
5. **Estado cambia a** `ENVIADO`
6. El usuario puede descargar:
   - PDF de la boleta
   - XML firmado
   - CDR de SUNAT

---

## 🧪 Ambiente de Pruebas vs Producción

### Ambiente BETA (Pruebas)
```env
SUNAT_URL_BETA=https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService
SUNAT_USUARIO_SOL=MODDATOS
SUNAT_CLAVE_SOL=MODDATOS
```

### Ambiente PRODUCCIÓN
```env
SUNAT_URL_PRODUCCION=https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService
SUNAT_USUARIO_SOL=TU_USUARIO_SOL_REAL
SUNAT_CLAVE_SOL=TU_CLAVE_SOL_REAL
```

**Para cambiar a producción:**
1. Actualiza el archivo `config.py`
2. Cambia `SUNAT_URL_BETA` por `SUNAT_URL_PRODUCCION`
3. Actualiza las credenciales en el archivo `.env`

---

## ❓ Solución de Problemas

### Error: "No such file or directory: certificado.pfx"
**Solución:** Verifica que copiaste el archivo .pfx a la carpeta `certificados/`

### Error: "Wrong password"
**Solución:** Verifica la contraseña en el archivo `.env`, debe ser la misma del archivo .txt

### Error: "Connection refused" o "Timeout"
**Solución:**
- Verifica tu conexión a internet
- Verifica que la URL de SUNAT sea correcta
- Si estás en pruebas, usa la URL Beta

### Error: "Invalid credentials"
**Solución:**
- Para Beta usa: MODDATOS/MODDATOS
- Para Producción usa tus credenciales SOL reales

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en la consola donde corre Flask
2. Verifica que todas las dependencias estén instaladas
3. Asegúrate de que el certificado no haya expirado

---

## ✅ Checklist Final

- [ ] Certificado .pfx copiado a carpeta `certificados/`
- [ ] Contraseña del certificado en archivo `.env`
- [ ] Credenciales SUNAT configuradas en `.env`
- [ ] Dependencias instaladas (lxml, pyOpenSSL, zeep)
- [ ] Base de datos actualizada
- [ ] Aplicación corriendo sin errores
- [ ] Venta de prueba enviada exitosamente

---

**¡Listo! Tu sistema ya está configurado para facturación electrónica con SUNAT** 🎉
