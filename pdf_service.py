from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
import os

def generar_pdf_boleta(venta, output_path):
    """
    Genera un PDF de la boleta electrónica
    """
    try:
        # Crear el PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Contenedor para los elementos
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilo personalizado para el título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Estilo para texto centrado
        centered_style = ParagraphStyle(
            'Centered',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=10
        )
        
        # HEADER - Datos de la empresa
        empresa_data = [
            [Paragraph('<b>IZISTORE PERU</b>', centered_style)],
            [Paragraph('RUC: 10433050709', centered_style)],
            [Paragraph('Av Fray Bartolome de las Casas 249', centered_style)],
            [Paragraph('San Martin de Porres - Lima', centered_style)],
            [Paragraph('Tel: 935403614', centered_style)],
            [Paragraph('ventas@izistoreperu.com', centered_style)],
        ]
        
        empresa_table = Table(empresa_data, colWidths=[6*inch])
        empresa_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3f4f6')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(empresa_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Título del comprobante
        comprobante_data = [
            [Paragraph('<b>BOLETA DE VENTA ELECTRÓNICA</b>', title_style)],
            [Paragraph(f'<b>{venta.numero_completo}</b>', centered_style)],
        ]
        
        comprobante_table = Table(comprobante_data, colWidths=[6*inch])
        comprobante_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e0e7ff')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(comprobante_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Datos del cliente
        cliente_data = [
            ['Cliente:', venta.cliente.nombre_completo],
            [f'{venta.cliente.tipo_documento}:', venta.cliente.numero_documento],
            ['Fecha de Emisión:', venta.fecha_emision.strftime('%d/%m/%Y %H:%M')],
            ['Vendedor:', venta.vendedor.nombre],
        ]
        
        if venta.numero_orden:
            cliente_data.insert(0, ['N° Orden:', venta.numero_orden])
        
        cliente_table = Table(cliente_data, colWidths=[1.5*inch, 4.5*inch])
        cliente_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(cliente_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Detalle de productos
        productos_data = [
            ['Descripción', 'Cantidad', 'P. Unit.', 'Subtotal']
        ]
        
        for item in venta.items:
            productos_data.append([
                item.producto_nombre,
                f"{float(item.cantidad):.2f}",
                f"S/ {float(item.precio_unitario):.2f}",
                f"S/ {float(item.subtotal):.2f}"
            ])
        
        productos_table = Table(productos_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        productos_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        elements.append(productos_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Total
        total_data = [
            ['', '', 'TOTAL:', f"S/ {float(venta.total):.2f}"]
        ]
        
        total_table = Table(total_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (2, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 0), (-1, 0), 12),
            ('ALIGN', (2, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (2, 0), (-1, 0), colors.HexColor('#e0e7ff')),
            ('BOX', (2, 0), (-1, 0), 2, colors.black),
            ('TOPPADDING', (2, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (2, 0), (-1, 0), 8),
        ]))
        elements.append(total_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Pie de página
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=8,
            textColor=colors.gray
        )
        
        elements.append(Paragraph('Este es un comprobante de pago electrónico', footer_style))
        elements.append(Paragraph(f'Representación impresa - {venta.estado}', footer_style))
        
        # Generar el PDF
        doc.build(elements)
        return True
        
    except Exception as e:
        print(f"Error al generar PDF: {str(e)}")
        return False
