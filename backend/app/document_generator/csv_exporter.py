import csv
import io
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CSVExporter:
    """Exporta datos a formato CSV"""
    
    def __init__(self):
        self.encoding = 'utf-8'
        self.delimiter = ','
    
    def export_budget_to_csv(self, budget_data: Dict[str, Any], output_path: str) -> bool:
        """
        Exporta un presupuesto a CSV
        
        Args:
            budget_data: Datos del presupuesto
            output_path: Ruta de salida
            
        Returns:
            True si se exportó exitosamente
        """
        try:
            logger.info(f"Exportando presupuesto a CSV: {output_path}")
            
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                # Crear escritor CSV
                writer = csv.writer(csvfile, delimiter=self.delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                
                # Información del presupuesto
                writer.writerow(['PRESUPUESTO DE OBRA'])
                writer.writerow([])
                writer.writerow(['Proyecto:', budget_data.get('project', {}).get('name', '')])
                writer.writerow(['Cliente:', budget_data.get('project', {}).get('client_name', '')])
                writer.writerow(['Ubicación:', budget_data.get('project', {}).get('location', '')])
                writer.writerow(['Fecha:', datetime.now().strftime('%d/%m/%Y')])
                writer.writerow([])
                
                # Resumen de costos
                writer.writerow(['RESUMEN DE COSTOS'])
                writer.writerow(['Concepto', 'Valor', 'Porcentaje'])
                
                subtotal = budget_data.get('total_amount', 0) - budget_data.get('profit_amount', 0)
                profit = budget_data.get('profit_amount', 0)
                total = budget_data.get('final_amount', 0)
                
                writer.writerow(['Costos Directos', f"${subtotal:,.2f}", f"{(subtotal/total*100):.1f}%"])
                writer.writerow(['Beneficio', f"${profit:,.2f}", f"{(profit/total*100):.1f}%"])
                writer.writerow(['TOTAL', f"${total:,.2f}", '100.0%'])
                writer.writerow([])
                
                # Detalle de partidas por capítulo
                chapters = self._group_items_by_chapter(budget_data.get('items', []))
                
                for chapter, data in chapters.items():
                    writer.writerow([f"CAPÍTULO {chapter}: {data['description']}"])
                    writer.writerow(['Código', 'Descripción', 'Unidad', 'Cantidad', 'P. Unitario', 'Total'])
                    
                    for item in data['items']:
                        writer.writerow([
                            item.get('code', ''),
                            item.get('description', ''),
                            item.get('unit', ''),
                            item.get('quantity', 0),
                            f"${item.get('unit_price', 0):,.2f}",
                            f"${item.get('total_price', 0):,.2f}"
                        ])
                    
                    writer.writerow(['', '', '', '', 'SUBTOTAL', f"${data['total']:,.2f}"])
                    writer.writerow([])
                
                # Análisis de costos
                writer.writerow(['ANÁLISIS DE COSTOS'])
                cost_breakdown = budget_data.get('cost_breakdown', {})
                
                writer.writerow(['Componente', 'Valor', 'Porcentaje'])
                writer.writerow(['Mano de Obra', f"${cost_breakdown.get('labor_cost', 0):,.2f}", 
                               f"{(cost_breakdown.get('labor_cost', 0)/total*100):.1f}%"])
                writer.writerow(['Materiales', f"${cost_breakdown.get('material_cost', 0):,.2f}", 
                               f"{(cost_breakdown.get('material_cost', 0)/total*100):.1f}%"])
                writer.writerow(['Equipo y Maquinaria', f"${cost_breakdown.get('equipment_cost', 0):,.2f}", 
                               f"{(cost_breakdown.get('equipment_cost', 0)/total*100):.1f}%"])
                writer.writerow(['Costos Indirectos', f"${cost_breakdown.get('indirect_cost', 0):,.2f}", 
                               f"{(cost_breakdown.get('indirect_cost', 0)/total*100):.1f}%"])
                writer.writerow(['Beneficio', f"${cost_breakdown.get('profit_amount', 0):,.2f}", 
                               f"{(cost_breakdown.get('profit_amount', 0)/total*100):.1f}%"])
                writer.writerow(['TOTAL', f"${total:,.2f}", '100.0%'])
            
            logger.info(f"Presupuesto exportado a CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando a CSV: {str(e)}")
            return False
    
    def export_price_book_to_csv(self, price_book_data: Dict[str, Any], output_path: str) -> bool:
        """
        Exporta un libro de precios a CSV
        
        Args:
            price_book_data: Datos del libro de precios
            output_path: Ruta de salida
            
        Returns:
            True si se exportó exitosamente
        """
        try:
            logger.info(f"Exportando libro de precios a CSV: {output_path}")
            
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                
                # Información del libro de precios
                writer.writerow(['LIBRO DE PRECIOS'])
                writer.writerow(['Nombre:', price_book_data.get('name', '')])
                writer.writerow(['Descripción:', price_book_data.get('description', '')])
                writer.writerow(['Fecha:', datetime.now().strftime('%d/%m/%Y')])
                writer.writerow([])
                
                # Encabezados
                writer.writerow(['Código', 'Descripción', 'Unidad', 'Precio Unitario', 'Categoría', 
                               '% Mano de Obra', '% Materiales', '% Equipo', 'Rendimiento', 'Notas'])
                
                # Datos de precios
                entries = price_book_data.get('entries', [])
                for entry in entries:
                    writer.writerow([
                        entry.get('code', ''),
                        entry.get('description', ''),
                        entry.get('unit', ''),
                        f"${entry.get('unit_price', 0):,.2f}",
                        entry.get('category', ''),
                        f"{entry.get('labor_percentage', 40):.1f}%",
                        f"{entry.get('material_percentage', 50):.1f}%",
                        f"{entry.get('equipment_percentage', 10):.1f}%",
                        f"{entry.get('performance_rate', 1.0):.2f}",
                        entry.get('notes', '')
                    ])
                
                # Estadísticas
                if entries:
                    writer.writerow([])
                    writer.writerow(['ESTADÍSTICAS'])
                    
                    prices = [entry.get('unit_price', 0) for entry in entries]
                    categories = list(set(entry.get('category', 'General') for entry in entries))
                    units = list(set(entry.get('unit', 'un') for entry in entries))
                    
                    writer.writerow(['Total de Partidas', len(entries)])
                    writer.writerow(['Precio Promedio', f"${sum(prices) / len(prices):,.2f}"])
                    writer.writerow(['Precio Mínimo', f"${min(prices):,.2f}"])
                    writer.writerow(['Precio Máximo', f"${max(prices):,.2f}"])
                    writer.writerow(['Número de Categorías', len(categories)])
                    writer.writerow(['Número de Unidades', len(units)])
            
            logger.info(f"Libro de precios exportado a CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando libro de precios a CSV: {str(e)}")
            return False
    
    def export_comparison_to_csv(self, budgets_data: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Exporta comparación de presupuestos a CSV
        
        Args:
            budgets_data: Lista de presupuestos
            output_path: Ruta de salida
            
        Returns:
            True si se exportó exitosamente
        """
        try:
            logger.info(f"Exportando comparación a CSV: {output_path}")
            
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                
                writer.writerow(['COMPARACIÓN DE PRESUPUESTOS'])
                writer.writerow(['Fecha:', datetime.now().strftime('%d/%m/%Y')])
                writer.writerow([])
                
                # Tabla comparativa
                headers = ['CONCEPTO'] + [budget.get('name', f"Presupuesto {i+1}") for i, budget in enumerate(budgets_data)]
                writer.writerow(headers)
                
                # Datos de comparación
                comparison_data = [
                    ['Subtotal', 'total_amount - profit_amount'],
                    ['Beneficio', 'profit_amount'],
                    ['Total', 'final_amount'],
                    ['Margen de Beneficio (%)', 'profit_margin'],
                    ['Número de Partidas', 'item_count'],
                    ['Fecha de Creación', 'created_at']
                ]
                
                for concept, field in comparison_data:
                    row_data = [concept]
                    
                    for budget in budgets_data:
                        if field == 'total_amount - profit_amount':
                            value = budget.get('total_amount', 0) - budget.get('profit_amount', 0)
                        elif field == 'profit_amount':
                            value = budget.get('profit_amount', 0)
                        elif field == 'final_amount':
                            value = budget.get('final_amount', 0)
                        elif field == 'profit_margin':
                            total = budget.get('total_amount', 1)
                            profit = budget.get('profit_amount', 0)
                            value = (profit / total * 100) if total > 0 else 0
                            value = f"{value:.1f}%"
                        elif field == 'item_count':
                            value = len(budget.get('items', []))
                        elif field == 'created_at':
                            value = budget.get('created_at', 'N/A')
                        else:
                            value = budget.get(field, '')
                        
                        if isinstance(value, (int, float)) and field not in ['profit_margin', 'item_count', 'created_at']:
                            value = f"${value:,.2f}"
                        
                        row_data.append(value)
                    
                    writer.writerow(row_data)
                
                # Análisis de variaciones si hay al menos 2 presupuestos
                if len(budgets_data) >= 2:
                    writer.writerow([])
                    writer.writerow(['ANÁLISIS DE VARIACIONES'])
                    
                    budget1 = budgets_data[0]
                    budget2 = budgets_data[1]
                    
                    total_diff = budget2.get('final_amount', 0) - budget1.get('final_amount', 0)
                    total_pct = (total_diff / budget1.get('final_amount', 1) * 100) if budget1.get('final_amount', 0) > 0 else 0
                    
                    items_diff = len(budget2.get('items', [])) - len(budget1.get('items', []))
                    
                    margin1 = (budget1.get('profit_amount', 0) / budget1.get('total_amount', 1) * 100)
                    margin2 = (budget2.get('profit_amount', 0) / budget2.get('total_amount', 1) * 100)
                    margin_diff = margin2 - margin1
                    
                    writer.writerow(['Variación Total', f"${total_diff:,.2f}", f"{total_pct:.1f}%"])
                    writer.writerow(['Diferencia en Partidas', items_diff, 'partidas'])
                    writer.writerow(['Variación de Margen', f"{margin_diff:.1f}%", 'puntos'])
            
            logger.info(f"Comparación exportada a CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando comparación a CSV: {str(e)}")
            return False
    
    def export_materials_list_to_csv(self, materials_data: Dict[str, Any], output_path: str) -> bool:
        """
        Exporta lista de materiales a CSV
        
        Args:
            materials_data: Datos de materiales
            output_path: Ruta de salida
            
        Returns:
            True si se exportó exitosamente
        """
        try:
            logger.info(f"Exportando lista de materiales a CSV: {output_path}")
            
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                
                writer.writerow(['LISTA DE MATERIALES'])
                writer.writerow(['Fecha:', datetime.now().strftime('%d/%m/%Y')])
                writer.writerow([])
                
                writer.writerow(['Material', 'Unidad', 'Cantidad Total', 'Costo Estimado', 'Items Relacionados'])
                
                materials = materials_data.get('materials', {})
                
                for material_key, material_data in materials.items():
                    writer.writerow([
                        material_key,
                        material_data.get('unit', ''),
                        material_data.get('quantity', 0),
                        f"${material_data.get('estimated_cost', 0):,.2f}",
                        len(material_data.get('items', []))
                    ])
                
                # Total
                writer.writerow([])
                writer.writerow(['TOTAL ESTIMADO', '', '', f"${materials_data.get('total_cost', 0):,.2f}", ''])
            
            logger.info(f"Lista de materiales exportada a CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando lista de materiales: {str(e)}")
            return False
    
    def export_labor_analysis_to_csv(self, labor_data: Dict[str, Any], output_path: str) -> bool:
        """
        Exporta análisis de mano de obra a CSV
        
        Args:
            labor_data: Datos de mano de obra
            output_path: Ruta de salida
            
        Returns:
            True si se exportó exitosamente
        """
        try:
            logger.info(f"Exportando análisis de mano de obra a CSV: {output_path}")
            
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
                
                writer.writerow(['ANÁLISIS DE MANO DE OBRA'])
                writer.writerow(['Fecha:', datetime.now().strftime('%d/%m/%Y')])
                writer.writerow([])
                
                writer.writerow(['Resumen General'])
                writer.writerow(['Costo Total de Mano de Obra:', f"${labor_data.get('total_labor_cost', 0):,.2f}"])
                writer.writerow(['Horas Totales Estimadas:', f"{labor_data.get('total_estimated_hours', 0):,.1f}"])
                writer.writerow(['Costo por Hora Promedio:', f"${labor_data.get('average_hourly_rate', 0):,.2f}"])
                writer.writerow([])
                
                writer.writerow(['Desglose por Categoría'])
                writer.writerow(['Categoría', 'Costo de Mano de Obra', 'Horas Estimadas'])
                
                categories = labor_data.get('categories', {})
                for category, data in categories.items():
                    writer.writerow([
                        category,
                        f"${data.get('labor_cost', 0):,.2f}",
                        f"{data.get('estimated_hours', 0):,.1f}"
                    ])
            
            logger.info(f"Análisis de mano de obra exportado a CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando análisis de mano de obra: {str(e)}")
            return False
    
    def _group_items_by_chapter(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Agrupa items por capítulo"""
        
        chapters = {}
        
        for item in items:
            chapter = item.get('chapter', 'Sin Capítulo')
            
            if chapter not in chapters:
                chapters[chapter] = {
                    'description': f"Capítulo {chapter}",
                    'items': [],
                    'total': 0.0
                }
            
            chapters[chapter]['items'].append(item)
            chapters[chapter]['total'] += float(item.get('total_price', 0))
        
        return chapters
    
    def get_csv_content(self, data: List[List[Any]], headers: Optional[List[str]] = None) -> str:
        """
        Genera contenido CSV en memoria
        
        Args:
            data: Datos a exportar
            headers: Encabezados opcionales
            
        Returns:
            Contenido CSV como string
        """
        try:
            output = io.StringIO()
            writer = csv.writer(output, delimiter=self.delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            if headers:
                writer.writerow(headers)
            
            for row in data:
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error generando contenido CSV: {str(e)}")
            return ""
    
    def set_delimiter(self, delimiter: str):
        """Cambia el delimitador CSV"""
        self.delimiter = delimiter
    
    def set_encoding(self, encoding: str):
        """Cambia la codificación"""
        self.encoding = encoding