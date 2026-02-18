
📝 Especificaciones Técnicas del Requerimiento
1. Interfaz de Usuario (Frontend - UX Eficiente)El diseño debe ser minimalista y enfocado en velocidad (tipo POS):

Encabezado:

Buscador Cliente(ya se hizo): Input conectado a API (Reniec/Sunat). Al digitar DNI (8 dígitos) o RUC (11 dígitos), autocompletar Nombre/Razón Social y Dirección.

Validación RUC: Si detecta RUC 20 (Personas Jurídicas), bloquear o lanzar alerta, ya que el RUS no puede emitir a empresas que exijan crédito fiscal (solo consumidores finales).

Cuerpo (Grid de Venta):

Estructura de filas dinámicas.

Columnas: [SKU/Buscador] | [Descripción] | [Cantidad] | [Precio Unitario (Editable)] 
agregar un (+) para agregar filas para escribir mas productos| [Subtotal]

Lógica de Buscador: Al escribir en SKU/Buscador, debe consultar la DB de WooCommerce en tiempo real (AJAX) y traer el producto.

Precio Editable: El precio debe cargar el de Woo por defecto, pero permitir sobrescritura manual (para descuentos rápidos o ajustes).

Botón (+): Agrega nueva fila.

Cálculo: Footer con Total a Pagar. (Ocultar desglose de IGV en la vista, mostrar solo "Importe Total" dado que es RUS).

2. Backend & Lógica de Negocio (El Cerebro)

Conexión:

Lectura: Base de datos WooCommerce (Tabla wp_posts y wp_postmeta) para obtener SKU y Nombres.

Escritura: API del PSE (Proveedor de Servicios Electrónicos) que ya validaste.

Gestión de Series y Correlativos:

El sistema debe llevar el control del correlativo (Ej: B001-0000002) ya que el 01 ya se hizo para pruebas.

Crucial: Evitar saltos de numeración. Si la API falla, el correlativo no debe avanzar hasta confirmar éxito.

Estructura XML (UBL 2.1 - SUNAT):

Aunque sea RUS y "no paguemos IGV" (en la práctica), el XML debe estructurarse correctamente.

Tipo de Operación: Venta Interna (0101). Le dice a la SUNAT que esta transacción es una venta realizada dentro del territorio peruano.

Código de Tributo: Configurar como Exonerado o Inafecto según corresponda la configuración del RUS en el XML para que no desglose IGV, O bien enviarlo como Gravado (IGV 18%) internamente si el PSE lo exige, pero visualmente en el PDF mostrar "Precio Incluye IGV". Recomendación: Mapear como Gravado IGV incluido para estandarización, pero el reporte contable interno lo trata como RUS.

3. Módulo de Control y Almacenamiento (Compliance)

Semáforo RUS (Vital):

Implementar una barra de progreso en el Dashboard principal.

Debe sumar el total emitido del mes en curso.

Alerta: Si supera S/ 5,000 (Categoría 1) -> Aviso Amarillo. Si se acerca a S/ 8,000 (Tope Categoría 2) -> Alerta Roja Bloqueante. Esto es para evitar que la SUNAT nos recategorice de oficio al Régimen Especial o Mype Tributario. no dejar boletear si se trata de superar los 8000 soles

Persistencia:

Guardar en base de datos local (MySQL): ID_Venta | PDF_Generado (Ruta) | XML (Ruta) | CDR (Ruta) | Estado_Sunat (Aceptado/Rechazado).

Backup automático de los XML y CDR (Constancia de Recepción) en una carpeta segura (VPS y local).

4. Generación de PDF (Representación Impresa)

Librería sugerida: TCPDF o FPDF.

Formato: A4 y Ticket (80mm).

Elementos obligatorios SUNAT:

QR (Codificado según norma).

Hash (Resumen).

Texto legal pie de página.

Datos del emisor (Tu RUC, Dirección Fiscal).

Saludos!
