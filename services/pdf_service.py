from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from datetime import datetime
import os
import decimal
from .utils import number_to_words_es

def generar_pdf_boleta(venta, output_path):
    """
    Genera un PDF de la boleta electrónica con el formato solicitado por el usuario
    """
    try:
        # Configuración de página con márgenes mínimos
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=10*mm,
            bottomMargin=10*mm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        style_norm = ParagraphStyle('Normal_Custom', parent=styles['Normal'], fontSize=8, leading=10)
        style_bold = ParagraphStyle('Bold_Custom', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold')
        style_header = ParagraphStyle('Header_Custom', parent=style_bold, textColor=colors.whitesmoke, alignment=TA_CENTER)
        style_small = ParagraphStyle('Small_Custom', parent=styles['Normal'], fontSize=7, leading=9)
        style_right = ParagraphStyle('Right_Custom', parent=styles['Normal'], fontSize=8, leading=10, alignment=TA_RIGHT)
        style_right_bold = ParagraphStyle('RightBold_Custom', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold', alignment=TA_RIGHT)

        # Columna 1: Logo (Ajustado para preservar proporción)
        logo_path = os.path.join('static', 'img', 'logo.png')
        if os.path.exists(logo_path):
            from PIL import Image as PILImage
            img_temp = PILImage.open(logo_path)
            img_w, img_h = img_temp.size
            img_temp.close()
            
            # Ajustar a un máximo de 40mm x 30mm manteniendo la proporción
            max_w = 40 * mm
            max_h = 30 * mm
            aspect = img_h / img_w
            
            if (max_w * aspect) <= max_h:
                final_w = max_w
                final_h = max_w * aspect
            else:
                final_h = max_h
                final_w = max_h / aspect
                
            logo = Image(logo_path, width=final_w, height=final_h)
        else:
            logo = Paragraph("<b>Logo</b>", style_norm)

        # Columna 2: Datos de la Empresa
        empresa_ruc = os.getenv('EMPRESA_RUC', '10433050709')
        empresa_nombre = os.getenv('EMPRESA_RAZON_SOCIAL', 'IZISTORE PERU')
        empresa_dir = os.getenv('EMPRESA_DIRECCION', 'Av. Fray Bartolome de las Casas 249, SMP')
        
        empresa_info = [
            [Paragraph(f'<b>{empresa_nombre}</b>', ParagraphStyle('EmpName', parent=style_norm, fontSize=12, leading=14))],
            [Paragraph(f'{empresa_dir}', style_small)],
        ]
        empresa_info_tab = Table(empresa_info, colWidths=[80*mm])
        empresa_info_tab.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 5*mm),
        ]))

        # Columna 3: Recuadro RUC / Comprobante
        es_nc = getattr(venta, 'tipo_comprobante', 'BOLETA') == 'NOTA_CREDITO'
        titulo_comprobante = 'NOTA DE CRÉDITO<br/>ELECTRÓNICA' if es_nc else 'BOLETA DE VENTA<br/>ELECTRÓNICA'
        ruc_box_data = [
            [Paragraph(f'RUC: {empresa_ruc}', style_norm)],
            [Paragraph(titulo_comprobante, ParagraphStyle('BoletaTitle', parent=style_norm, fontSize=11, leading=13, alignment=TA_CENTER, fontName='Helvetica-Bold'))],
            [Paragraph(f'Nro : {venta.numero_completo}', style_norm)],
        ]
        ruc_box_tab = Table(ruc_box_data, colWidths=[60*mm])
        ruc_box_tab.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 2*mm),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2*mm),
            ('GRID', (0,1), (0,1), 0, colors.gray), # Separador sutil opcional
            ('BACKGROUND', (0,1), (0,1), colors.lightgrey),
        ]))

        header_main_tab = Table([[logo, empresa_info_tab, ruc_box_tab]], colWidths=[45*mm, 85*mm, 60*mm])
        header_main_tab.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(header_main_tab)
        elements.append(Spacer(1, 10))

        # 2. SECCIÓN INFO (Cliente, Venta)
        # ----------------------------------------------------------------------
        
        info_data = [
            [Paragraph('CLIENTE', style_bold), Paragraph(f': {venta.cliente.nombre_completo}', style_norm),
             Paragraph('FECHA EMISION', style_bold), Paragraph(f': {venta.fecha_emision.strftime("%d/%m/%Y")}', style_norm)],
            [Paragraph('RUC / DNI', style_bold), Paragraph(f': {venta.cliente.numero_documento}', style_norm),
             Paragraph('FECHA VENCIMIENTO', style_bold), Paragraph(f': {venta.fecha_emision.strftime("%d/%m/%Y")}', style_norm)], # Generalmente igual
            [Paragraph('DIRECCIÓN', style_bold), Paragraph(f': {venta.cliente.direccion or ""}', style_norm),
             Paragraph('MEDIO DE PAGO', style_bold), Paragraph(': EFECTIVO', style_norm)], # Placeholder por ahora
            [Paragraph('', style_bold), Paragraph('', style_norm),
             Paragraph('MONEDA', style_bold), Paragraph(': SOLES', style_norm)],
        ]
        
        info_tab = Table(info_data, colWidths=[30*mm, 80*mm, 40*mm, 40*mm])
        info_tab.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ]))
        elements.append(info_tab)

        # Para Notas de Crédito: mostrar referencia al documento original y motivo
        if es_nc and venta.venta_referencia:
            elements.append(Spacer(1, 5))
            ref_data = [
                [Paragraph('DOC. REFERENCIA', style_bold),
                 Paragraph(f': {venta.venta_referencia.numero_completo}', style_norm),
                 Paragraph('MOTIVO', style_bold),
                 Paragraph(f': {venta.motivo_nc_codigo} — {venta.motivo_nc_descripcion}', style_norm)],
            ]
            ref_tab = Table(ref_data, colWidths=[30*mm, 80*mm, 25*mm, 55*mm])
            ref_tab.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('BACKGROUND', (0,0), (-1,-1), colors.lightyellow),
            ]))
            elements.append(ref_tab)

        elements.append(Spacer(1, 15))

        # 3. TABLA DE DETALLES
        # ----------------------------------------------------------------------
        
        detalles_header = [
            Paragraph('N°', style_header),
            Paragraph('UNIDAD', style_header),
            Paragraph('CODIGO', style_header),
            Paragraph('DESCRIPCION', style_header),
            Paragraph('CANT.', style_header),
            Paragraph('P. UNIT.', style_header),
            Paragraph('P. TOTAL', style_header)
        ]
        
        detalles_data = [detalles_header]

        tiene_item_envio = any(item.producto_sku == 'ENVIO' for item in venta.items)
        costo_envio_val = float(venta.costo_envio or 0.0)

        for idx, item in enumerate(venta.items, 1):
            detalles_data.append([
                Paragraph(str(idx), style_norm),
                Paragraph('UND', style_norm),
                Paragraph(item.producto_sku or '', style_norm),
                Paragraph(item.producto_nombre, style_norm),
                Paragraph(f"{float(item.cantidad):.2f}", style_right),
                Paragraph(f"{float(item.precio_unitario):.2f}", style_right),
                Paragraph(f"{float(item.subtotal):.2f}", style_right)
            ])

        # Si el envío no existe como item, agregarlo como línea adicional
        if costo_envio_val > 0 and not tiene_item_envio:
            idx_envio = len(venta.items) + 1
            detalles_data.append([
                Paragraph(str(idx_envio), style_norm),
                Paragraph('SRV', style_norm),
                Paragraph('ENVIO', style_norm),
                Paragraph('Gasto de Envío', style_norm),
                Paragraph('1.00', style_right),
                Paragraph(f'{costo_envio_val:.2f}', style_right),
                Paragraph(f'{costo_envio_val:.2f}', style_right)
            ])

        # Rellenar filas vacías para mantener estructura visual (opcional)
        while len(detalles_data) < 7:
             detalles_data.append(['','','','','','',''])

        detalles_tab = Table(detalles_data, colWidths=[10*mm, 15*mm, 15*mm, 90*mm, 15*mm, 22.5*mm, 22.5*mm])
        detalles_tab.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('LINEAFTER', (0,0), (-2,-1), 0.5, colors.black),
            ('BOTTOMPADDING', (0,0), (-1,0), 2*mm),
            ('TOPPADDING', (0,0), (-1,0), 2*mm),
        ]))
        elements.append(detalles_tab)

        # 4. TOTALES Y SON:
        # ----------------------------------------------------------------------

        # RUS — todas las operaciones son inafectas (IGV = 0).
        # productos_total = total sin envío (monto inafecto de productos)
        if tiene_item_envio:
            # El ENVIO item ya está en venta.total → restarlo para obtener solo productos
            productos_total = float(venta.total) - costo_envio_val
        else:
            # Envío separado → venta.total ya es solo productos
            productos_total = float(venta.total)

        val_total    = productos_total + costo_envio_val
        val_subtotal = round(productos_total, 2)  # INAFECTO = monto total de productos
        val_igv      = 0.0

        # Son: [Letras]
        monto_letras = number_to_words_es(val_total)
        son_tab = Table([[Paragraph(f'SON : {monto_letras}', style_bold)]], colWidths=[190*mm])
        son_tab.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        elements.append(son_tab)

        totals_data = [
            [Paragraph('INAFECTO', style_right_bold), Paragraph('S/', style_norm), Paragraph(f'{val_subtotal:.2f}', style_right)],
            [Paragraph('I.G.V', style_right_bold), Paragraph('S/', style_norm), Paragraph(f'{val_igv:.2f}', style_right)],
        ]
        if costo_envio_val > 0:
            totals_data.append([
                Paragraph('ENVÍO (INAFECTO)', style_right_bold), Paragraph('S/', style_norm), Paragraph(f'{costo_envio_val:.2f}', style_right)
            ])
        totals_data.append([
            Paragraph('TOTAL:', style_right_bold), Paragraph('S/', style_norm), Paragraph(f'{val_total:.2f}', style_right)
        ])

        totals_tab = Table(totals_data, colWidths=[130*mm, 15*mm, 45*mm])
        totals_tab.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('RIGHTPADDING', (2,0), (2,-1), 5*mm),
            ('LINEABOVE', (2,-1), (2,-1), 1, colors.black),  # línea sobre la última fila (TOTAL)
        ]))
        
        # Envolver totales en una tabla con bordes laterales si se quiere match exacto
        wrapper_totals_tab = Table([[totals_tab]], colWidths=[190*mm])
        wrapper_totals_tab.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 2*mm),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2*mm),
        ]))
        elements.append(wrapper_totals_tab)
        elements.append(Spacer(1, 10))

        # 5. FOOTER (QR, Disclaimer, Usuario)
        # ----------------------------------------------------------------------
        
        # Generar QR dinámico
        # Formato SUNAT: RUC|TipoDoc|Serie|Correlativo|IGV|Total|Fecha|TipoDocCliente|NumDocCliente|Hash|
        qr_content = f"{empresa_ruc}|03|{venta.serie}|{venta.correlativo}|{val_igv:.2f}|{val_total:.2f}|{venta.fecha_emision.strftime('%Y-%m-%d')}|{venta.cliente.tipo_documento}|{venta.cliente.numero_documento}|{venta.hash_cpe or ''}|"
        qr_code = qr.QrCodeWidget(qr_content)
        qr_code.barWidth = 35*mm
        qr_code.barHeight = 35*mm
        qr_drawing = Drawing(35*mm, 35*mm)
        qr_drawing.add(qr_code)

        vendedor_nombre = venta.vendedor.nombre if venta.vendedor else "SISTEMA"
        fecha_hora = datetime.now().strftime("%d/%m/%Y %I:%M %p").replace("AM", "a.m.").replace("PM", "p.m.")
        
        footer_info = [
            [Paragraph(f'<b>USUARIO {vendedor_nombre.upper()}</b> - {fecha_hora}', style_norm)],
            [Paragraph('<b>RESPUESTA SUNAT</b>', style_bold)],
            [Paragraph('Autorizado mediante resolución N° 034-005-0010431/SUNAT<br/>Representación impresa de la BOLETA ELECTRONICA<br/>generada desde el sistema facturador SUNAT. Puede verificarla utilizando su clave SOL', style_small)],
        ]
        
        footer_info_tab = Table(footer_info, colWidths=[150*mm])
        footer_info_tab.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        footer_main_tab = Table([[footer_info_tab, qr_drawing]], colWidths=[150*mm, 40*mm])
        footer_main_tab.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(footer_main_tab)

        # Construir PDF
        doc.build(elements)
        return True
        
    except Exception as e:
        print(f"Error al generar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def render_template_html(venta, template_html):
    """
    Toma una venta y un string HTML (template) y retorna el HTML con las variables reemplazadas.
    """
    import os
    
    # Preparar datos dinámicos (Variables)
    empresa_ruc = os.getenv('EMPRESA_RUC', '10433050709')
    empresa_nombre = os.getenv('EMPRESA_RAZON_SOCIAL', 'IZISTORE PERU')
    empresa_direccion = os.getenv('EMPRESA_DIRECCION', '')
    
    # Generar HTML de la tabla de productos
    items_html = ""
    for idx, item in enumerate(venta.items, 1):
        items_html += f"""
        <tr>
            <td style="border: 1px solid black; padding: 5px;">{item.producto_nombre}</td>
            <td style="border: 1px solid black; padding: 5px; text-align: center;">{float(item.cantidad):.2f}</td>
            <td style="border: 1px solid black; padding: 5px; text-align: right;">{float(item.precio_unitario):.2f}</td>
            <td style="border: 1px solid black; padding: 5px; text-align: right;">{float(item.subtotal):.2f}</td>
        </tr>
        """

    # Mapeo de variables
    replacements = {
        '[[EMPRESA_NOMBRE]]': empresa_nombre,
        '[[EMPRESA_RUC]]': empresa_ruc,
        '[[EMPRESA_DIRECCION]]': empresa_direccion,
        '[[NRO_COMPROBANTE]]': venta.numero_completo,
        '[[CLIENTE_NOMBRE]]': venta.cliente.nombre_completo,
        '[[CLIENTE_DOCUMENTO]]': venta.cliente.numero_documento,
        '[[FECHA_EMISION]]': venta.fecha_emision.strftime("%d/%m/%Y"),
        '[[TOTAL]]': f"S/ {float(venta.total):.2f}",
        '[[DETALLE_PRODUCTOS]]': f'<table style="width: 100%; border-collapse: collapse;">{items_html}</table>',
        '[[TOTAL_LETRAS]]': number_to_words_es(float(venta.total))
    }

    # Aplicar reemplazos en el HTML
    final_html = template_html
    for key, value in replacements.items():
        final_html = final_html.replace(key, str(value))
    
    return final_html

def generar_pdf_html(venta, output_path, force_html=False):
    """
    Genera un PDF de la boleta electrónica usando una plantilla HTML personalizada con WeasyPrint.
    Si force_html es False, caerá en el diseño antiguo si falla WeasyPrint.
    """
    try:
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            print(" [PDF-HTML] ❌ WeasyPrint no está instalado. Instalado 'weasyprint'?")
            if force_html:
                raise ImportError("WeasyPrint no está configurado correctamente en este sistema.")
            return generar_pdf_boleta(venta, output_path)
            
        from models import InvoiceTemplate
        import os
        
        # 1. Obtener plantilla activa
        template = InvoiceTemplate.query.filter_by(es_activo=True).first()
        if not template:
            print(" [PDF-HTML] ⚠️ No hay plantilla activa, usando fallback ReportLab")
            return generar_pdf_boleta(venta, output_path)

        # 2. Renderizar HTML con variables
        final_html = render_template_html(venta, template.html_content)

        # 3. Renderizar PDF
        # Combinar HTML con CSS de la plantilla
        HTML(string=final_html).write_pdf(output_path, stylesheets=[CSS(string=template.css_content or "")])
        
        print(f" [PDF-HTML] ✅ PDF generado exitosamente en {output_path}")
        return True

    except Exception as e:
        print(f" [PDF-HTML] ❌ Error crítico: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
