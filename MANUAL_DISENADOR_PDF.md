# 🎨 Manual del Diseñador Visual de Boletas (No-Code)

Este documento es una guía rápida para entender cómo funciona el nuevo módulo de diseño de comprobantes basado en HTML y CSS.

## 🚀 Conceptos Básicos
El diseñador utiliza una herramienta llamada **GrapesJS**, que permite arrastrar y soltar elementos para armar el diseño. Lo que ves en el editor se traduce a un archivo PDF real cuando se genera una boleta.

---

## 🏷️ Diccionario de Variables
Para que el sistema ponga los datos reales de la venta, debes usar etiquetas especiales llamadas "Variables". El sistema las reconocerá y las reemplazará automáticamente.

### Datos de la Empresa
| Variable | Descripción |
| :--- | :--- |
| `[[EMPRESA_NOMBRE]]` | Nombre o Razón Social de tu negocio. |
| `[[EMPRESA_RUC]]` | Tu número de RUC configurado. |
| `[[EMPRESA_DIRECCION]]` | Dirección fiscal de tu empresa. |

### Datos del Comprobante
| Variable | Descripción |
| :--- | :--- |
| `[[NRO_COMPROBANTE]]` | Serie y Correlativo (ej: B001-000001). |
| `[[FECHA_EMISION]]` | Fecha de la boleta (DD/MM/AAAA). |
| `[[TOTAL]]` | El monto total a pagar con símbolo (S/). |
| `[[TOTAL_LETRAS]]` | El monto total escrito en letras (SOLES). |

### Datos del Cliente
| Variable | Descripción |
| :--- | :--- |
| `[[CLIENTE_NOMBRE]]` | Nombre completo del cliente. |
| `[[CLIENTE_DOCUMENTO]]` | DNI o RUC del cliente. |

### El Detalle de Productos
| Variable | Descripción |
| :--- | :--- |
| `[[DETALLE_PRODUCTOS]]` | **¡Importante!** Inserta una tabla con todos los items comprados. |

---

## 🛠️ Tutorial: Cómo modificar el diseño

### 1. Panel de Elementos (Iconos en la esquina superior derecha)
- **Icono de Cuadros (Bloques):** Aquí encuentras componentes pre-armados como el "Recuadro RUC" o la "Tabla de Items". Solo arrástralos a la hoja.
- **Icono de Pincel (Estilos):** Haz clic en cualquier texto o cuadro y usa este panel para cambiar el color, tamaño de letra, márgenes o bordes.
- **Icono de Engranaje (Atributos):** Para configuraciones avanzadas.
- **Icono de Capas:** Muestra la estructura de tu diseño (como en Photoshop).

### 2. Edición de Texto
Simplemente haz **doble clic** sobre cualquier texto para editarlo. Puedes escribir texto fijo (ej: "Gracias por su compra") o meter una variable (ej: `[[CLIENTE_NOMBRE]]`).

### 3. Vista Previa
- **Vista Previa Navegador (Botón Amarillo):** Úsalo mientras diseñas en tu PC. Es rápido y no da errores de sistema.
- **Vista Previa PDF (Botón Azul):** Genera el PDF real. Úsalo en el servidor de producción para confirmar el resultado final.

---

## ⚠️ Notas de Seguridad (Modo Sandbox)
- Por defecto, tus cambios **NO afectan** a las boletas que imprimes normalmente. 
- Este módulo es un entorno de pruebas ("Juego") para que encuentres el diseño perfecto.
- Una vez que tengas un diseño listo y quieras que sea el oficial, solicita al administrador activar el "Motor HTML" para producción.

---

## 💻 Notas para Desarrolladores
- El motor de renderizado es **WeasyPrint**.
- Los estilos deben ser CSS estándar (evitar funciones muy modernas de CSS).
- El sistema utiliza `A4` por defecto, pero se puede configurar para `Ticket 80mm` en las opciones avanzadas.
