import re
from typing import Dict, List, Any, Optional, Tuple
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class FormatDetector:
    """Detecta y clasifica diferentes formatos de presupuestos de construcción"""
    
    def __init__(self):
        self.known_formats = {
            'standard_table': {
                'name': 'Tabla Estándar',
                'description': 'Formato de tabla con columnas fijas',
                'indicators': [
                    r'Item|Código|Code',
                    r'Descripción|Description',
                    r'Cantidad|Quantity|Qty',
                    r'Unidad|Unit',
                    r'Precio|Price|Cost',
                    r'Total'
                ]
            },
            'chapters_list': {
                'name': 'Lista por Capítulos',
                'description': 'Organizado por capítulos con items numerados',
                'indicators': [
                    r'Capítulo|Chapter|CAP',
                    r'\d+\.\d+\.\d+',
                    r'\b\d+\.\d+\b',
                    r'\b\d+\s*[.-]'
                ]
            },
            'unit_prices': {
                'name': 'Precios Unitarios',
                'description': 'Lista de precios unitarios por partida',
                'indicators': [
                    r'Precio Unitario|Unit Price',
                    r'PU\s*=',
                    r'\$\s*\d+\.\d{2}',
                    r'\d+\.\d{2}\s*€'
                ]
            },
            'detailed_breakdown': {
                'name': 'Desglose Detallado',
                'description': 'Incluye desglose de materiales, mano de obra, etc.',
                'indicators': [
                    r'Materiales|Materials',
                    r'Mano de Obra|Labor',
                    r'Equipo|Equipment',
                    r'Indirectos|Overhead'
                ]
            }
        }
        
        self.format_scores = {}
    
    def detect_format(self, text: str, ocr_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Detecta el formato del presupuesto
        
        Args:
            text: Texto extraído del PDF
            ocr_data: Datos adicionales de OCR si disponibles
            
        Returns:
            Dict con información del formato detectado
        """
        try:
            # Limpiar texto
            clean_text = text.upper()
            lines = clean_text.split('\n')
            
            # Analizar diferentes aspectos
            structure_analysis = self._analyze_structure(lines)
            content_analysis = self._analyze_content(clean_text)
            pattern_analysis = self._analyze_patterns(lines)
            
            # Calcular puntuaciones para cada formato conocido
            format_scores = {}
            
            for format_key, format_info in self.known_formats.items():
                score = self._calculate_format_score(
                    format_info, structure_analysis, content_analysis, pattern_analysis
                )
                format_scores[format_key] = score
            
            # Determinar formato principal
            best_format = max(format_scores.items(), key=lambda x: x[1])
            
            # Análisis adicional basado en OCR si está disponible
            layout_analysis = {}
            if ocr_data:
                layout_analysis = self._analyze_layout(ocr_data)
            
            result = {
                'detected_format': best_format[0],
                'format_name': self.known_formats[best_format[0]]['name'],
                'confidence': best_format[1],
                'all_scores': format_scores,
                'structure_analysis': structure_analysis,
                'content_analysis': content_analysis,
                'pattern_analysis': pattern_analysis,
                'layout_analysis': layout_analysis,
                'recommendations': self._get_recommendations(best_format[0])
            }
            
            logger.info(f"Formato detectado: {result['format_name']} (confianza: {result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error detectando formato: {str(e)}")
            return {
                'detected_format': 'unknown',
                'format_name': 'Formato Desconocido',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _analyze_structure(self, lines: List[str]) -> Dict[str, Any]:
        """Analiza la estructura del documento"""
        analysis = {
            'total_lines': len(lines),
            'empty_lines': sum(1 for line in lines if not line.strip()),
            'header_lines': 0,
            'table_lines': 0,
            'list_items': 0,
            'section_headers': 0,
            'has_table_structure': False,
            'has_list_structure': False,
            'average_line_length': 0
        }
        
        if lines:
            analysis['average_line_length'] = sum(len(line) for line in lines) / len(lines)
        
        # Analizar tipos de líneas
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detectar encabezados de tabla
            if any(indicator in line.upper() for indicator in ['ITEM', 'CÓDIGO', 'DESCRIPCIÓN', 'CANTIDAD', 'PRECIO']):
                analysis['header_lines'] += 1
            
            # Detectar líneas de tabla (múltiples columnas de números)
            if self._is_table_line(line):
                analysis['table_lines'] += 1
            
            # Detectar items de lista
            if self._is_list_item(line):
                analysis['list_items'] += 1
            
            # Detectar encabezados de sección
            if self._is_section_header(line):
                analysis['section_headers'] += 1
        
        # Determinar estructura predominante
        analysis['has_table_structure'] = analysis['table_lines'] > len(lines) * 0.3
        analysis['has_list_structure'] = analysis['list_items'] > len(lines) * 0.4
        
        return analysis
    
    def _analyze_content(self, text: str) -> Dict[str, Any]:
        """Analiza el contenido del texto"""
        analysis = {
            'has_currency_symbols': '$' in text or '€' in text,
            'has_decimal_numbers': len(re.findall(r'\d+\.\d{2}', text)) > 0,
            'has_thousand_separators': len(re.findall(r'\d,\d{3}', text)) > 0,
            'has_units': any(unit in text.lower() for unit in ['m2', 'm3', 'kg', 'ml', 'l', 'un']),
            'has_chapter_headers': len(re.findall(r'CAPÍTULO|CHAPTER', text)) > 0,
            'has_totals': any(word in text for word in ['TOTAL', 'SUBTOTAL', 'SUB-TOTAL']),
            'has_breakdown': any(word in text for word in ['MATERIALES', 'MANO DE OBRA', 'EQUIPO']),
            'currency_count': len(re.findall(r'[$€]', text)),
            'number_count': len(re.findall(r'\d+\.\d+', text)),
            'unit_count': len(re.findall(r'\b(m2|m3|kg|ml|l|un)\b', text, re.IGNORECASE))
        }
        
        return analysis
    
    def _analyze_patterns(self, lines: List[str]) -> Dict[str, Any]:
        """Analiza patrones en las líneas"""
        patterns = {
            'repeated_patterns': 0,
            'code_patterns': 0,
            'price_patterns': 0,
            'quantity_patterns': 0,
            'consistent_spacing': 0,
            'tab_separated': 0
        }
        
        # Analizar patrones en cada línea
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Contar patrones de códigos
            if re.search(r'\d+(?:\.\d+)+', line):
                patterns['code_patterns'] += 1
            
            # Contar patrones de precios
            if any(re.search(p, line) for p in [r'\$?\d+(?:,\d{3})*\.\d{2}', r'\d+(?:\.\d{3})*,\d{2}']):
                patterns['price_patterns'] += 1
            
            # Contar patrones de cantidades con unidades
            if re.search(r'\d+(?:\.\d+)?\s*(?:m2|m3|kg|ml|l|un|m)', line, re.IGNORECASE):
                patterns['quantity_patterns'] += 1
            
            # Detectar separación por tabulaciones o múltiples espacios
            if '\t' in line or re.search(r'\s{3,}', line):
                patterns['tab_separated'] += 1
        
        # Analizar consistencia de patrones
        total_lines = len([l for l in lines if l.strip()])
        if total_lines > 0:
            patterns['repeated_patterns'] = (
                patterns['code_patterns'] / total_lines +
                patterns['price_patterns'] / total_lines +
                patterns['quantity_patterns'] / total_lines
            ) / 3
        
        return patterns
    
    def _analyze_layout(self, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el layout usando datos de OCR"""
        if 'words' not in ocr_data:
            return {}
        
        words = ocr_data['words']
        if not words:
            return {}
        
        # Analizar distribución espacial
        x_coords = [w['x'] for w in words]
        y_coords = [w['y'] for w in words]
        
        analysis = {
            'has_aligned_columns': self._detect_columns(x_coords, y_coords),
            'has_grid_structure': self._detect_grid_structure(words),
            'text_density': len(words) / (max(y_coords) - min(y_coords)) if y_coords else 0,
            'average_word_spacing': self._calculate_average_spacing(words),
            'alignment_consistency': self._analyze_alignment(words)
        }
        
        return analysis
    
    def _detect_columns(self, x_coords: List[int], y_coords: List[int]) -> bool:
        """Detecta si el texto está organizado en columnas"""
        if not x_coords:
            return False
        
        # Buscar agrupaciones en las coordenadas X
        x_coords_sorted = sorted(x_coords)
        gaps = []
        
        for i in range(1, len(x_coords_sorted)):
            gap = x_coords_sorted[i] - x_coords_sorted[i-1]
            if gap > 50:  # Gap significativo
                gaps.append(gap)
        
        # Si hay suficientes gaps grandes, probablemente hay columnas
        return len(gaps) > 3
    
    def _detect_grid_structure(self, words: List[Dict]) -> bool:
        """Detecta si hay estructura de grill"""
        if len(words) < 10:
            return False
        
        # Verificar alineación en filas y columnas
        y_positions = set(round(w['y'] / 10) for w in words)  # Agrupar por filas
        x_positions = set(round(w['x'] / 10) for w in words)  # Agrupar por columnas
        
        # Si hay muchas posiciones Y similares y X similares, puede ser una grilla
        return len(y_positions) < len(words) * 0.3 and len(x_positions) < len(words) * 0.3
    
    def _calculate_average_spacing(self, words: List[Dict]) -> float:
        """Calcula el espaciado promedio entre palabras"""
        if len(words) < 2:
            return 0.0
        
        spacings = []
        words_sorted = sorted(words, key=lambda w: (w['y'], w['x']))
        
        for i in range(1, len(words_sorted)):
            if abs(words_sorted[i]['y'] - words_sorted[i-1]['y']) < 20:  # Misma línea
                spacing = words_sorted[i]['x'] - (words_sorted[i-1]['x'] + words_sorted[i-1]['width'])
                spacings.append(spacing)
        
        return sum(spacings) / len(spacings) if spacings else 0.0
    
    def _analyze_alignment(self, words: List[Dict]) -> float:
        """Analiza la consistencia del alineamiento"""
        if len(words) < 2:
            return 0.0
        
        # Agrupar palabras por líneas
        lines = {}
        for word in words:
            line_key = round(word['y'] / 15)  # Agrupar por líneas aproximadas
            if line_key not in lines:
                lines[line_key] = []
            lines[line_key].append(word)
        
        # Calcular consistencia de alineamiento
        consistencies = []
        for line_words in lines.values():
            if len(line_words) > 1:
                x_coords = [w['x'] for w in line_words]
                consistency = 1.0 - (max(x_coords) - min(x_coords)) / 1000
                consistencies.append(max(0.0, consistency))
        
        return sum(consistencies) / len(consistencies) if consistencies else 0.0
    
    def _is_table_line(self, line: str) -> bool:
        """Determina si una línea parece ser parte de una tabla"""
        # Contar números y palabras
        numbers = re.findall(r'\d+(?:\.\d+)?', line)
        words = line.split()
        
        # Una línea de tabla típicamente tiene números y múltiples palabras
        return len(numbers) >= 2 and len(words) >= 4
    
    def _is_list_item(self, line: str) -> bool:
        """Determina si una línea parece ser un item de lista"""
        # Patrones comunes de items de lista
        patterns = [
            r'^\s*\d+(?:\.\d+)*\s+',  # 1.1.1
            r'^\s*\d+\s*[.-]\s+',     # 1- o 1.
            r'^\s*[A-Z]{2,3}\d{2,4}\s+'  # AB1234
        ]
        
        return any(re.match(pattern, line) for pattern in patterns)
    
    def _is_section_header(self, line: str) -> bool:
        """Determina si una línea parece ser un encabezado de sección"""
        line = line.strip()
        
        # Es corta, está en mayúsculas, o contiene palabras clave
        is_short = len(line) < 50
        is_uppercase = line.isupper()
        has_keywords = any(keyword in line for keyword in ['CAPÍTULO', 'CHAPTER', 'SECCIÓN', 'SECTION'])
        
        return is_short and (is_uppercase or has_keywords)
    
    def _calculate_format_score(self, format_info: Dict, structure: Dict, content: Dict, patterns: Dict) -> float:
        """Calcula la puntuación de coincidencia para un formato"""
        score = 0.0
        
        # Puntuación basada en indicadores
        for indicator in format_info.get('indicators', []):
            if re.search(indicator, str(structure) + str(content), re.IGNORECASE):
                score += 1.0
        
        # Normalizar por número de indicadores
        if format_info.get('indicators'):
            score /= len(format_info['indicators'])
        
        # Bonificaciones por características específicas
        if content.get('has_table_structure') and 'table' in format_info['name'].lower():
            score += 0.3
        
        if content.get('has_list_structure') and 'list' in format_info['name'].lower():
            score += 0.3
        
        if content.get('has_breakdown') and 'detallado' in format_info['name'].lower():
            score += 0.2
        
        return min(score, 1.0)  # Máximo 1.0
    
    def _get_recommendations(self, format_key: str) -> List[str]:
        """Proporciona recomendaciones basadas en el formato detectado"""
        recommendations = []
        
        if format_key == 'standard_table':
            recommendations = [
                "Usar extracción por columnas fijas",
                "Validar que todas las filas tengan el mismo número de columnas",
                "Buscar encabezados de tabla para mapear campos"
            ]
        elif format_key == 'chapters_list':
            recommendations = [
                "Extraer capítulos como secciones principales",
                "Usar numeración para identificar jerarquía",
                "Agrupar items por capítulo"
            ]
        elif format_key == 'unit_prices':
            recommendations = [
                "Enfocarse en extracción de precios unitarios",
                "Validar precios contra rangos esperados",
                "Buscar actualizaciones de precios"
            ]
        elif format_key == 'detailed_breakdown':
            recommendations = [
                "Extraer desglose de costos por categoría",
                "Sumar componentes para obtener totales",
                "Validar que la suma de componentes coincida con totales"
            ]
        else:
            recommendations = [
                "Usar extracción basada en patrones",
                "Aplicar múltiples estrategias de extracción",
                "Validar resultados manualmente"
            ]
        
        return recommendations