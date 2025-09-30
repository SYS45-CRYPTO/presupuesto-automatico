from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Genera presupuestos en formato PDF profesional"""
    
    def __init__(self):
        self.page_size = A4
        self.margin = 0.75 * inch
        self.styles = self._create_styles()
    
    def generate_budget_pdf(self, budget_data: Dict[str, Any], output_path: str, 
                          include_logo: bool = True, template: str = 'standard') -> bool:
        """
        Genera un PDF profesional del presupuesto
        
        Args:
            budget_data: Datos completos del presupuesto
            output_path: Ruta de salida del PDF
            include_logo: Si incluir el logo de la empresa
            template: Plantilla a usar
            
        Returns:
            True si se generó exitosamente
        """
        try:
            logger.info(f"Generando PDF de presupuesto: {output_path}")
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin + 0.5 * inch,
                bottomMargin=self.margin
            )
            
            # Construir contenido del PDF
            story = []
            
            # Página de portada
            story.extend(self._create_cover_page(budget_data, include_logo))
            
            # Resumen ejecutivo
            story.extend(self._create_executive_summary(budget_data))
            
            # Desglose por capítulos
            story.extend(self._create_chapter_breakdown(budget_data))
            
            # Detalle de partidas
            story.extend(self._create_detailed_items(budget_data))
            
            # Análisis de costos
            story.extend(self._create_cost_analysis(budget_data))
            
            # Términos y condiciones
            story.extend(self._create_terms_and_conditions())
            
            # Generar PDF
            doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
            
            logger.info(f"PDF generado exitosamente: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generando PDF: {str(e)}")
            return False
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Crea estilos personalizados para el PDF"""
        
        styles = getSampleStyleSheet()
        
        # Estilo para título principal
        styles.add(ParagraphStyle(
            name='BudgetTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#2E4057'),
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos
        styles.add(ParagraphStyle(
            name='BudgetSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=HexColor('#5D6D7E'),
            fontName='Helvetica'
        ))
        
        # Estilo para encabezados de sección
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=20,
            alignment=TA_LEFT,
            textColor=HexColor('#2E4057'),
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=HexColor('#BDC3C7'),
            borderPadding=5
        ))
        
        # Estilo para texto normal
        styles.add(ParagraphStyle(
            name='NormalText',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            textColor=HexColor('#2C3E50'),
            fontName='Helvetica'
        ))
        
        # Estilo para texto en tabla
        styles.add(ParagraphStyle(
            name='TableText',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=3,
            alignment=TA_LEFT,
            textColor=HexColor('#2C3E50'),
            fontName='Helvetica'
        ))
        
        # Estilo para números en tabla
        styles.add(ParagraphStyle(
            name='TableNumber',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=3,
            alignment=TA_RIGHT,
            textColor=HexColor('#2C3E50'),
            fontName='Helvetica'
        ))
        
        # Estilo para encabezados de tabla
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=3,
            alignment=TA_CENTER,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            backColor=HexColor('#34495E')
        ))
        
        # Estilo para totales
        styles.add(ParagraphStyle(
            name='TotalText',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_RIGHT,
            textColor=HexColor('#2E4057'),
            fontName='Helvetica-Bold'
        ))
        
        return styles
    
    def _create_cover_page(self, budget_data: Dict[str, Any], include_logo: bool) -> List:
        """Crea la página de portada del presupuesto"""
        
        story = []
        
        # Espacio inicial
        story.append(Spacer(1, 2 * inch))
        
        # Logo si está disponible
        if include_logo and budget_data.get('company', {}).get('logo_path'):
            try:
                from reportlab.platypus import Image
                logo = Image(budget_data['company']['logo_path'], width=2*inch, height=1*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 0.5 * inch))
            except:
                pass
        
        # Título del documento
        title = Paragraph("PRESUPUESTO DE OBRA", self.styles['BudgetTitle'])
        story.append(title)
        story.append(Spacer(1, 0.5 * inch))
        
        # Información del proyecto
        project_info = f"""
        <para align="center">
        <b>Proyecto:</b> {budget_data.get('project', {}).get('name', 'N/A')}<br/>
        <b>Cliente:</b> {budget_data.get('project', {}).get('client_name', 'N/A')}<br/>
        <b>Ubicación:</b> {budget_data.get('project', {}).get('location', 'N/A')}<br/>
        <b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>
        <b>Versión:</b> {budget_data.get('version', '1.0')}
        </para>
        """
        
        project_paragraph = Paragraph(project_info, self.styles['BudgetSubtitle'])
        story.append(project_paragraph)
        
        story.append(Spacer(1, 2 * inch))
        
        # Información de la empresa
        company_info = f"""
        <para align="center">
        <b>{budget_data.get('company', {}).get('name', 'Constructora')}</b><br/>
        Presupuesto elaborado por: {budget_data.get('prepared_by', 'Departamento de Costos')}<br/>
        Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </para>
        """
        
        company_paragraph = Paragraph(company_info, self.styles['NormalText'])
        story.append(company_paragraph)
        
        story.append(PageBreak())
        
        return story
    
    def _create_executive_summary(self, budget_data: Dict[str, Any]) -> List:
        """Crea el resumen ejecutivo del presupuesto"""
        
        story = []
        
        # Título de sección
        story.append(Paragraph("RESUMEN EJECUTIVO", self.styles['SectionHeader']))
        
        # Resumen de costos
        total_amount = budget_data.get('final_amount', 0)
        profit_amount = budget_data.get('profit_amount', 0)
        
        summary_text = f"""
        <para>
        El presente presupuesto corresponde a los trabajos de construcción para el proyecto 
        <b>{budget_data.get('project', {}).get('name', '')}</b>, con un valor total de 
        <b>${self._format_currency(total_amount)}</b>.
        </para>
        """
        
        story.append(Paragraph(summary_text, self.styles['NormalText']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Tabla de resumen
        summary_data = [
            ['CONCEPTO', 'VALOR', 'PORCENTAJE'],
            ['Costos Directos', f"${self._format_currency(budget_data.get('total_amount', 0) - profit_amount)}", 
             f"{((budget_data.get('total_amount', 0) - profit_amount) / budget_data.get('total_amount', 1) * 100):.1f}%"],
            ['Beneficio', f"${self._format_currency(profit_amount)}", 
             f"{(profit_amount / budget_data.get('total_amount', 1) * 100):.1f}%"],
            ['TOTAL PRESUPUESTO', f"${self._format_currency(total_amount)}", '100.0%']
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch, 1.5*inch])
        summary_table.setStyle(self._get_table_style())
        story.append(summary_table)
        
        story.append(Spacer(1, 0.3 * inch))
        
        return story
    
    def _create_chapter_breakdown(self, budget_data: Dict[str, Any]) -> List:
        """Crea el desglose por capítulos"""
        
        story = []
        
        story.append(Paragraph("DESGLOSE POR CAPÍTULOS", self.styles['SectionHeader']))
        
        # Obtener capítulos
        chapters = self._group_by_chapters(budget_data.get('items', []))
        
        if chapters:
            # Crear tabla de capítulos
            chapter_data = [['CAPÍTULO', 'DESCRIPCIÓN', 'VALOR', '%']]
            
            total_amount = budget_data.get('final_amount', 1)
            
            for chapter, data in chapters.items():
                percentage = (data['total'] / total_amount) * 100
                
                chapter_data.append([
                    chapter,
                    data['description'][:50] + '...' if len(data['description']) > 50 else data['description'],
                    f"${self._format_currency(data['total'])}",
                    f"{percentage:.1f}%"
                ])
            
            chapter_table = Table(chapter_data, colWidths=[1.5*inch, 3*inch, 1.5*inch, 1*inch])
            chapter_table.setStyle(self._get_table_style())
            story.append(chapter_table)
        else:
            story.append(Paragraph("No se encontraron capítulos definidos.", self.styles['NormalText']))
        
        story.append(Spacer(1, 0.3 * inch))
        
        return story
    
    def _create_detailed_items(self, budget_data: Dict[str, Any]) -> List:
        """Crea el detalle de partidas del presupuesto"""
        
        story = []
        
        story.append(Paragraph("DETALLE DE PARTIDAS", self.styles['SectionHeader']))
        
        # Agrupar items por capítulo
        chapters = self._group_by_chapters(budget_data.get('items', []))
        
        for chapter, data in chapters.items():
            # Título del capítulo
            chapter_title = f"CAPÍTULO {chapter}: {data['description']}"
            story.append(Paragraph(chapter_title, self.styles['SectionHeader']))
            
            # Tabla de items del capítulo
            items_data = [['CÓDIGO', 'DESCRIPCIÓN', 'UNIDAD', 'CANTIDAD', 'P. UNITARIO', 'TOTAL']]
            
            for item in data['items']:
                items_data.append([
                    item.get('code', ''),
                    item.get('description', '')[:40] + '...' if len(item.get('description', '')) > 40 else item.get('description', ''),
                    item.get('unit', ''),
                    self._format_number(item.get('quantity', 0)),
                    f"${self._format_currency(item.get('unit_price', 0))}",
                    f"${self._format_currency(item.get('total_price', 0))}"
                ])
            
            # Agregar subtotal del capítulo
            items_data.append(['', '', '', '', 'SUBTOTAL', f"${self._format_currency(data['total'])}"])
            
            items_table = Table(items_data, colWidths=[1*inch, 3*inch, 0.8*inch, 1*inch, 1.2*inch, 1.2*inch])
            items_table.setStyle(self._get_detailed_table_style())
            story.append(items_table)
            
            story.append(Spacer(1, 0.2 * inch))
        
        return story
    
    def _create_cost_analysis(self, budget_data: Dict[str, Any]) -> List:
        """Crea el análisis de costos"""
        
        story = []
        
        story.append(Paragraph("ANÁLISIS DE COSTOS", self.styles['SectionHeader']))
        
        # Desglose de costos
        cost_breakdown = budget_data.get('cost_breakdown', {})
        
        cost_data = [
            ['COMPONENTE', 'VALOR', 'PORCENTAJE SOBRE TOTAL'],
            ['Mano de Obra', 
             f"${self._format_currency(cost_breakdown.get('labor_cost', 0))}",
             f"{(cost_breakdown.get('labor_cost', 0) / budget_data.get('total_amount', 1) * 100):.1f}%"],
            ['Materiales', 
             f"${self._format_currency(cost_breakdown.get('material_cost', 0))}",
             f"{(cost_breakdown.get('material_cost', 0) / budget_data.get('total_amount', 1) * 100):.1f}%"],
            ['Equipo y Maquinaria', 
             f"${self._format_currency(cost_breakdown.get('equipment_cost', 0))}",
             f"{(cost_breakdown.get('equipment_cost', 0) / budget_data.get('total_amount', 1) * 100):.1f}%"],
            ['Costos Indirectos', 
             f"${self._format_currency(cost_breakdown.get('indirect_cost', 0))}",
             f"{(cost_breakdown.get('indirect_cost', 0) / budget_data.get('total_amount', 1) * 100):.1f}%"],
            ['Beneficio', 
             f"${self._format_currency(cost_breakdown.get('profit_amount', 0))}",
             f"{(cost_breakdown.get('profit_amount', 0) / budget_data.get('total_amount', 1) * 100):.1f}%"],
            ['TOTAL', 
             f"${self._format_currency(budget_data.get('total_amount', 0))}", '100.0%']
        ]
        
        cost_table = Table(cost_data, colWidths=[2.5*inch, 2*inch, 2*inch])
        cost_table.setStyle(self._get_table_style())
        story.append(cost_table)
        
        story.append(Spacer(1, 0.3 * inch))
        
        # Notas adicionales
        notes_text = """
        <para>
        <b>Notas:</b><br/>
        • Los precios incluyen todos los costos directos e indirectos necesarios para la ejecución de la obra.<br/>
        • Los precios no incluyen IVA.<br/>
        • La vigencia de este presupuesto es de 30 días calendario.<br/>
        • Cualquier modificación en el alcance de los trabajos deberá ser notificada por escrito.
        </para>
        """
        
        story.append(Paragraph(notes_text, self.styles['NormalText']))
        
        return story
    
    def _create_terms_and_conditions(self) -> List:
        """Crea los términos y condiciones"""
        
        story = []
        
        story.append(Paragraph("TÉRMINOS Y CONDICIONES", self.styles['SectionHeader']))
        
        terms_text = """
        <para>
        1. <b>ALCANCE:</b> Este presupuesto incluye todos los trabajos de construcción especificados en el detalle de partidas.
        </para>
        """
        
        story.append(Paragraph(terms_text, self.styles['NormalText']))
        
        terms_2 = """
        <para>
        2. <b>CONDICIONES DE PAGO:</b> Los pagos se realizarán de acuerdo con los hitos de avance de obra acordados.
        </para>
        """
        
        story.append(Paragraph(terms_2, self.styles['NormalText']))
        
        terms_3 = """
        <para>
        3. <b>TIEMPO DE EJECUCIÓN:</b> El tiempo de ejecución será determinado en el contrato una vez aprobado este presupuesto.
        </para>
        """
        
        story.append(Paragraph(terms_3, self.styles['NormalText']))
        
        terms_4 = """
        <para>
        4. <b>GARANTÍA:</b> Los trabajos ejecutados tendrán la garantía establecida por la normativa vigente.
        </para>
        """
        
        story.append(Paragraph(terms_4, self.styles['NormalText']))
        
        # Espacio para firmas
        story.append(Spacer(1, 1 * inch))
        
        signatures = """
        <para align="center">
        _________________________<br/>
        Aprobado por el Cliente<br/><br/><br/>
        
        _________________________<br/>
        Elaborado por: {prepared_by}<br/>
        {company_name}
        </para>
        """.format(
            prepared_by=budget_data.get('prepared_by', ''),
            company_name=budget_data.get('company', {}).get('name', '')
        )
        
        story.append(Paragraph(signatures, self.styles['NormalText']))
        
        return story
    
    def _header_footer(self, canvas, doc):
        """Agrega encabezado y pie de página"""
        
        # Encabezado
        canvas.saveState()
        
        # Línea superior
        canvas.setStrokeColor(HexColor('#BDC3C7'))
        canvas.setLineWidth(1)
        canvas.line(doc.leftMargin, doc.height + doc.topMargin - 0.5*inch, 
                   doc.width + doc.leftMargin, doc.height + doc.topMargin - 0.5*inch)
        
        # Información del encabezado
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor('#5D6D7E'))
        
        # Fecha y página
        header_text = f"Presupuesto de Obra - Página {doc.page}"
        canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin - 0.3*inch, header_text)
        
        # Pie de página
        footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} - Valido por 30 días"
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.bottomMargin - 0.3*inch, footer_text)
        
        # Línea inferior
        canvas.line(doc.leftMargin, doc.bottomMargin - 0.2*inch, 
                   doc.width + doc.leftMargin, doc.bottomMargin - 0.2*inch)
        
        canvas.restoreState()
    
    def _get_table_style(self) -> TableStyle:
        """Obtiene el estilo base para tablas"""
        
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2C3E50')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#F8F9FA')])
        ])
    
    def _get_detailed_table_style(self) -> TableStyle:
        """Obtiene estilo para tablas detalladas"""
        
        base_style = self._get_table_style()
        
        # Agregar estilo para filas de subtotal
        base_style.add('BACKGROUND', (0, -1), (-1, -1), HexColor('#E8F4FD'))
        base_style.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        base_style.add('TEXTCOLOR', (0, -1), (-1, -1), HexColor('#2E4057'))
        
        return base_style
    
    def _group_by_chapters(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Agrupa items por capítulo"""
        
        chapters = {}
        
        for item in items:
            chapter = item.get('chapter', 'Sin Capítulo')
            
            if chapter not in chapters:
                chapters[chapter] = {
                    'description': f"Capítulo {chapter}",
                    'items': [],
                    'total': Decimal('0.00')
                }
            
            chapters[chapter]['items'].append(item)
            chapters[chapter]['total'] += Decimal(str(item.get('total_price', 0)))
        
        return chapters
    
    def _format_currency(self, amount) -> str:
        """Formatea un monto como moneda"""
        
        try:
            if isinstance(amount, (int, float, Decimal)):
                return f"{Decimal(str(amount)):,.2f}"
            return "0.00"
        except:
            return "0.00"
    
    def _format_number(self, number) -> str:
        """Formatea un número"""
        
        try:
            if isinstance(number, (int, float, Decimal)):
                return f"{Decimal(str(number)):,.2f}"
            return "0.00"
        except:
            return "0.00"
    
    def generate_comparison_pdf(self, budgets_data: List[Dict[str, Any]], 
                              output_path: str) -> bool:
        """
        Genera un PDF comparando múltiples presupuestos
        
        Args:
            budgets_data: Lista de presupuestos a comparar
            output_path: Ruta de salida del PDF
            
        Returns:
            True si se generó exitosamente
        """
        try:
            logger.info(f"Generando PDF de comparación: {output_path}")
            
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin + 0.5 * inch,
                bottomMargin=self.margin
            )
            
            story = []
            
            # Título
            title = Paragraph("COMPARACIÓN DE PRESUPUESTOS", self.styles['BudgetTitle'])
            story.append(title)
            story.append(Spacer(1, 0.5 * inch))
            
            # Tabla comparativa
            comparison_data = [['CONCEPTO']]
            
            # Agregar columnas de presupuestos
            for budget in budgets_data:
                comparison_data[0].append(budget.get('name', f"Presupuesto {budget.get('id', '')}"))
            
            # Agregar filas de comparación
            comparison_rows = [
                ['Subtotal'],
                ['Beneficio'],
                ['Total'],
                ['Margen de Beneficio'],
                ['Número de Partidas'],
                ['Fecha de Creación']
            ]
            
            for i, row in enumerate(comparison_rows):
                row_data = [row[0]]
                for budget in budgets_data:
                    if i == 0:  # Subtotal
                        value = f"${self._format_currency(budget.get('total_amount', 0) - budget.get('profit_amount', 0))}"
                    elif i == 1:  # Beneficio
                        value = f"${self._format_currency(budget.get('profit_amount', 0))}"
                    elif i == 2:  # Total
                        value = f"${self._format_currency(budget.get('final_amount', 0))}"
                    elif i == 3:  # Margen
                        margin = (budget.get('profit_amount', 0) / budget.get('total_amount', 1) * 100)
                        value = f"{margin:.1f}%"
                    elif i == 4:  # Número de partidas
                        value = str(len(budget.get('items', [])))
                    else:  # Fecha
                        value = budget.get('created_at', 'N/A')
                    
                    row_data.append(value)
                
                comparison_data.append(row_data)
            
            # Crear tabla de comparación
            num_budgets = len(budgets_data)
            col_widths = [2.5*inch] + [1.5*inch] * num_budgets
            
            comparison_table = Table(comparison_data, colWidths=col_widths)
            comparison_table.setStyle(self._get_comparison_table_style(num_budgets))
            story.append(comparison_table)
            
            # Análisis de variaciones
            if len(budgets_data) >= 2:
                story.append(Spacer(1, 0.5 * inch))
                story.append(Paragraph("ANÁLISIS DE VARIACIONES", self.styles['SectionHeader']))
                
                variations = self._calculate_variations(budgets_data)
                
                for variation in variations:
                    story.append(Paragraph(variation, self.styles['NormalText']))
            
            doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
            
            logger.info(f"PDF de comparación generado: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generando PDF de comparación: {str(e)}")
            return False
    
    def _get_comparison_table_style(self, num_columns: int) -> TableStyle:
        """Obtiene estilo para tablas de comparación"""
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2C3E50')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ])
        
        # Resaltar diferencias significativas
        for col in range(1, num_columns + 1):
            style.add('TEXTCOLOR', (col, 3), (col, 3), HexColor('#E74C3C'))  # Totales en rojo
            style.add('FONTNAME', (col, 3), (col, 3), 'Helvetica-Bold')
        
        return style
    
    def _calculate_variations(self, budgets_data: List[Dict[str, Any]]) -> List[str]:
        """Calcula variaciones entre presupuestos"""
        
        if len(budgets_data) < 2:
            return []
        
        variations = []
        
        # Comparar presupuesto 1 vs 2
        budget1 = budgets_data[0]
        budget2 = budgets_data[1]
        
        total_diff = budget2.get('final_amount', 0) - budget1.get('final_amount', 0)
        total_pct = (total_diff / budget1.get('final_amount', 1)) * 100 if budget1.get('final_amount', 0) > 0 else 0
        
        if abs(total_pct) > 5:
            variations.append(f"Variación total significativa: {total_pct:.1f}% ({self._format_currency(total_diff)})")
        
        # Comparar número de partidas
        items_diff = len(budget2.get('items', [])) - len(budget1.get('items', []))
        if items_diff != 0:
            variations.append(f"Diferencia en número de partidas: {items_diff}")
        
        # Comparar márgenes
        margin1 = (budget1.get('profit_amount', 0) / budget1.get('total_amount', 1)) * 100
        margin2 = (budget2.get('profit_amount', 0) / budget2.get('total_amount', 1)) * 100
        margin_diff = margin2 - margin1
        
        if abs(margin_diff) > 2:
            variations.append(f"Variación en margen de beneficio: {margin_diff:.1f}%")
        
        return variations