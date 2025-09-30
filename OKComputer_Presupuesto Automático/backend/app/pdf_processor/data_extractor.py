import re
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

class DataExtractor:
    """Extrae datos estructurados de presupuestos de construcción"""
    
    def __init__(self):
        self.common_units = {
            'm2', 'm3', 'kg', 'ml', 'l', 'un', 'hm', 'km', 'm', 'pieza', 'juego', 'global',
            'metros', 'kilogramos', 'litros', 'unidades', 'metros cuadrados', 'metros cúbicos'
        }
        
        self.currency_patterns = [
            r'\$?\d{1,3}(?:,\d{3})*\.?\d{0,2}',  # $1,234.56 o 1234.56
            r'\d{1,3}(?:\.\d{3})*,\d{2}',         # 1.234,56
            r'\b\d+\.\d{2}\b'                    # 123.45
        ]
    
    def extract_budget_items(self, text: str, format_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extrae partidas de presupuesto del texto
        
        Args:
            text: Texto extraído del PDF
            format_type: Tipo de formato detectado (opcional)
            
        Returns:
            Lista de partidas de presupuesto
        """
        try:
            # Limpiar texto
            clean_text = self._clean_text(text)
            lines = clean_text.split('\n')
            
            # Detectar formato si no se proporciona
            if not format_type:
                format_type = self._detect_format(lines)
            
            logger.info(f"Procesando presupuesto con formato: {format_type}")
            
            # Extraer según el formato detectado
            if format_type == "table":
                items = self._extract_from_table(lines)
            elif format_type == "list":
                items = self._extract_from_list(lines)
            elif format_type == "mixed":
                items = self._extract_from_mixed(lines)
            else:
                items = self._extract_with_patterns(lines)
            
            # Validar y limpiar items extraídos
            validated_items = self._validate_and_clean_items(items)
            
            logger.info(f"Extraídas {len(validated_items)} partidas de presupuesto")
            return validated_items
            
        except Exception as e:
            logger.error(f"Error extrayendo partidas de presupuesto: {str(e)}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Limpia y normaliza el texto"""
        # Eliminar caracteres de control
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        # Normalizar saltos de línea
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def _detect_format(self, lines: List[str]) -> str:
        """Detecta el formato del presupuesto"""
        if len(lines) < 3:
            return "unknown"
        
        # Contar líneas que parecen ser filas de tabla
        table_lines = 0
        list_lines = 0
        
        for line in lines:
            # Patrón de tabla: múltiples columnas de números
            if self._is_table_row(line):
                table_lines += 1
            # Patrón de lista: código + descripción + cantidad
            elif self._is_list_item(line):
                list_lines += 1
        
        # Determinar formato basado en predominancia
        if table_lines > len(lines) * 0.6:
            return "table"
        elif list_lines > len(lines) * 0.4:
            return "list"
        else:
            return "mixed"
    
    def _is_table_row(self, line: str) -> bool:
        """Determina si una línea parece ser una fila de tabla"""
        # Buscar múltiples números separados por espacios o tabulaciones
        numbers = re.findall(r'\d+(?:\.\d+)?', line)
        return len(numbers) >= 3 and len(line.split()) >= 4
    
    def _is_list_item(self, line: str) -> bool:
        """Determina si una línea parece ser un item de lista"""
        # Buscar patrón: código + texto + número + unidad
        has_code = re.match(r'^\s*\d+(?:\.\d+)*', line) is not None
        has_number = re.search(r'\d+(?:\.\d+)?\s*(?:m2|m3|kg|ml|l|un|m)\b', line, re.IGNORECASE) is not None
        has_price = any(re.search(pattern, line) for pattern in self.currency_patterns)
        
        return has_code and (has_number or has_price)
    
    def _extract_from_table(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extrae partidas de formato de tabla"""
        items = []
        
        for line in lines:
            # Intentar dividir la línea en columnas
            columns = self._split_table_row(line)
            
            if len(columns) >= 4:  # Mínimo 4 columnas para una partida válida
                item = self._parse_table_columns(columns)
                if item:
                    items.append(item)
        
        return items
    
    def _split_table_row(self, line: str) -> List[str]:
        """Divide una fila de tabla en columnas"""
        # Intentar dividir por múltiples espacios o tabulaciones
        columns = re.split(r'\s{2,}|\t', line.strip())
        
        # Filtrar columnas vacías
        columns = [col.strip() for col in columns if col.strip()]
        
        return columns
    
    def _parse_table_columns(self, columns: List[str]) -> Optional[Dict[str, Any]]:
        """Parsea las columnas de una tabla en una partida"""
        try:
            item = {
                'code': '',
                'description': '',
                'unit': '',
                'quantity': None,
                'unit_price': None,
                'total_price': None
            }
            
            # Buscar código (primera columna que parezca un código)
            for i, col in enumerate(columns[:2]):  # Solo las primeras 2 columnas
                if re.match(r'^\d+(?:\.\d+)*$', col):
                    item['code'] = col
                    # La siguiente columna probablemente sea la descripción
                    if i + 1 < len(columns):
                        item['description'] = columns[i + 1]
                    break
            
            # Si no encontramos código, la primera columna puede ser descripción
            if not item['code']:
                item['description'] = columns[0]
            
            # Buscar unidad y cantidad
            for col in columns:
                # Buscar cantidad con unidad
                qty_match = re.search(r'(\d+(?:\.\d+)?)\s*(m2|m3|kg|ml|l|un|m)\b', col, re.IGNORECASE)
                if qty_match and not item['quantity']:
                    item['quantity'] = Decimal(qty_match.group(1))
                    item['unit'] = qty_match.group(2)
                
                # Buscar solo unidad
                unit_match = re.search(r'\b(m2|m3|kg|ml|l|un|m)\b', col, re.IGNORECASE)
                if unit_match and not item['unit']:
                    item['unit'] = unit_match.group(1)
            
            # Buscar precios
            prices = []
            for col in columns:
                for pattern in self.currency_patterns:
                    price_matches = re.findall(pattern, col)
                    for price in price_matches:
                        try:
                            clean_price = price.replace('$', '').replace(',', '')
                            prices.append(Decimal(clean_price))
                        except:
                            pass
            
            # Asignar precios basándose en valores y posición
            if len(prices) >= 2:
                # Asumir que el menor es precio unitario, mayor es total
                prices_sorted = sorted(prices)
                item['unit_price'] = prices_sorted[0]
                item['total_price'] = prices_sorted[-1]
            elif len(prices) == 1:
                # Solo un precio, asumir que es unitario
                item['unit_price'] = prices[0]
                if item['quantity']:
                    item['total_price'] = item['quantity'] * item['unit_price']
            
            # Validar item mínimo
            if item['description'] and (item['quantity'] or item['unit_price']):
                return item
            
            return None
            
        except Exception as e:
            logger.error(f"Error parseando columnas de tabla: {str(e)}")
            return None
    
    def _extract_from_list(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extrae partidas de formato de lista"""
        items = []
        current_item = None
        
        for line in lines:
            # Buscar inicio de nueva partida
            new_item = self._parse_list_item(line)
            
            if new_item:
                # Guardar item anterior si existe
                if current_item:
                    items.append(current_item)
                
                current_item = new_item
            elif current_item:
                # Si no es nueva partida, puede ser continuación de descripción
                if len(line.strip()) > 10 and not line.strip()[0].isdigit():
                    current_item['description'] += ' ' + line.strip()
        
        # Guardar último item
        if current_item:
            items.append(current_item)
        
        return items
    
    def _parse_list_item(self, line: str) -> Optional[Dict[str, Any]]:
        """Parsea una línea de lista en una partida"""
        line = line.strip()
        if not line:
            return None
        
        # Patrón común: Código Descripción Cantidad Unidad Precio
        patterns = [
            # Formato: 01.01.01 Descripción 100 m2 $50.00
            r'^(\d+(?:\.\d+)*)\s+(.+?)\s+(\d+(?:\.\d+)?)\s*(m2|m3|kg|ml|l|un|m)\s+([$\d,\.]+)',
            # Formato: 001 Descripción 100 50.00
            r'^(\d+)\s+(.+?)\s+(\d+(?:\.\d+)?)\s+([$\d,\.]+)',
            # Formato: AB1234 Descripción 100 m2
            r'^([A-Z]{2,3}\d{2,4})\s+(.+?)\s+(\d+(?:\.\d+)?)\s*(m2|m3|kg|ml|l|un|m)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                item = {
                    'code': groups[0],
                    'description': groups[1].strip(),
                    'quantity': Decimal(groups[2]) if len(groups) > 2 else None,
                    'unit': groups[3] if len(groups) > 3 and groups[3] in self.common_units else '',
                    'unit_price': None,
                    'total_price': None
                }
                
                # Buscar precio adicional
                if len(groups) > 4:
                    try:
                        price_str = groups[4].replace('$', '').replace(',', '')
                        item['unit_price'] = Decimal(price_str)
                    except:
                        pass
                
                return item
        
        return None
    
    def _extract_from_mixed(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extrae partidas de formato mixto usando múltiples estrategias"""
        items = []
        
        # Intentar diferentes estrategias
        strategies = [
            self._extract_with_line_breaks,
            self._extract_with_context,
            self._extract_with_patterns
        ]
        
        for strategy in strategies:
            try:
                strategy_items = strategy(lines)
                if len(strategy_items) > len(items):
                    items = strategy_items
            except Exception as e:
                logger.warning(f"Estrategia {strategy.__name__} falló: {str(e)}")
                continue
        
        return items
    
    def _extract_with_line_breaks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extrae partidas considerando saltos de línea"""
        items = []
        buffer = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Si la línea parece ser una nueva partida
            if self._is_new_item_line(line):
                # Procesar buffer acumulado
                if buffer:
                    item = self._parse_buffered_lines(buffer)
                    if item:
                        items.append(item)
                    buffer = []
            
            buffer.append(line)
        
        # Procesar último buffer
        if buffer:
            item = self._parse_buffered_lines(buffer)
            if item:
                items.append(item)
        
        return items
    
    def _is_new_item_line(self, line: str) -> bool:
        """Determina si una línea parece ser el inicio de una nueva partida"""
        # Comienza con código
        if re.match(r'^\s*\d+(?:\.\d+)*', line):
            return True
        
        # Comienza con patrón de código de obra
        if re.match(r'^\s*[A-Z]{2,3}\d{2,4}', line):
            return True
        
        return False
    
    def _parse_buffered_lines(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Parsea múltiples líneas acumuladas en una partida"""
        if not lines:
            return None
        
        # Unir líneas
        full_text = ' '.join(lines)
        
        # Intentar parsear como una sola línea
        item = self._parse_list_item(full_text)
        
        if not item:
            # Si falla, intentar extraer información con patrones
            item = self._extract_item_with_patterns(full_text)
        
        return item
    
    def _extract_with_context(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extrae partidas usando contexto de líneas adyacentes"""
        items = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Considerar contexto de líneas cercanas
            context_lines = lines[max(0, i-1):i+2]
            context_text = ' '.join(context_lines)
            
            item = self._extract_item_with_patterns(context_text)
            if item and self._is_valid_item(item):
                items.append(item)
        
        return items
    
    def _extract_with_patterns(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extrae partidas usando patrones regex avanzados"""
        items = []
        full_text = '\n'.join(lines)
        
        # Patrones para diferentes formatos de presupuesto
        budget_patterns = [
            # Formato complejo con múltiples campos
            r'(?P<code>\d+(?:\.\d+)*)\s+(?P<desc>.+?)\s+(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>m2|m3|kg|ml|l|un|m)\s+(?P<uprice>\d+(?:\.\d{2})?)\s+(?P<total>\d+(?:\.\d{2})?)',
            # Formato con código y cantidad
            r'(?P<code>[A-Z]{2,3}\d{2,4})\s+(?P<desc>.+?)\s+(?P<qty>\d+(?:\.\d+)?)\s+(?P<unit>m2|m3|kg|ml|l|un|m)',
            # Formato simple con descripción y precio
            r'(?P<desc>.+?)\s+(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>m2|m3|kg|ml|l|un|m)\s+(?P<price>\d+(?:\.\d{2})?)'
        ]
        
        for pattern in budget_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                groups = match.groupdict()
                item = {
                    'code': groups.get('code', ''),
                    'description': groups.get('desc', '').strip(),
                    'quantity': Decimal(groups['qty']) if 'qty' in groups and groups['qty'] else None,
                    'unit': groups.get('unit', ''),
                    'unit_price': None,
                    'total_price': None
                }
                
                # Parsear precios
                if 'uprice' in groups and groups['uprice']:
                    try:
                        item['unit_price'] = Decimal(groups['uprice'])
                    except:
                        pass
                
                if 'total' in groups and groups['total']:
                    try:
                        item['total_price'] = Decimal(groups['total'])
                    except:
                        pass
                elif 'price' in groups and groups['price']:
                    try:
                        item['unit_price'] = Decimal(groups['price'])
                    except:
                        pass
                
                if self._is_valid_item(item):
                    items.append(item)
        
        return items
    
    def _extract_item_with_patterns(self, text: str) -> Optional[Dict[str, Any]]:
        """Extrae información de partida usando patrones en texto arbitrario"""
        item = {
            'code': '',
            'description': '',
            'unit': '',
            'quantity': None,
            'unit_price': None,
            'total_price': None
        }
        
        # Buscar código
        code_match = re.search(r'\b(\d+(?:\.\d+)*)\b', text)
        if code_match:
            item['code'] = code_match.group(1)
        
        # Buscar cantidad
        qty_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(m2|m3|kg|ml|l|un|m)\b', text, re.IGNORECASE)
        if qty_match:
            item['quantity'] = Decimal(qty_match.group(1))
            item['unit'] = qty_match.group(2)
        
        # Buscar precio
        for pattern in self.currency_patterns:
            price_matches = re.findall(pattern, text)
            if price_matches:
                try:
                    clean_price = price_matches[0].replace('$', '').replace(',', '')
                    item['unit_price'] = Decimal(clean_price)
                    break
                except:
                    pass
        
        # Extraer descripción (texto sin números al principio)
        desc_match = re.search(r'[a-zA-Z].*', text)
        if desc_match:
            item['description'] = desc_match.group(0).strip()
        
        return item if self._is_valid_item(item) else None
    
    def _validate_and_clean_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Valida y limpia las partidas extraídas"""
        validated_items = []
        
        for item in items:
            if self._is_valid_item(item):
                # Limpiar y normalizar
                cleaned_item = self._clean_item(item)
                validated_items.append(cleaned_item)
        
        # Eliminar duplicados basados en código y descripción
        unique_items = []
        seen_items = set()
        
        for item in validated_items:
            item_key = f"{item.get('code', '')}_{item.get('description', '')[:50]}"
            if item_key not in seen_items:
                seen_items.add(item_key)
                unique_items.append(item)
        
        return unique_items
    
    def _is_valid_item(self, item: Dict[str, Any]) -> bool:
        """Valida si un item tiene los campos mínimos requeridos"""
        has_description = bool(item.get('description', '').strip())
        has_quantity = item.get('quantity') is not None and item['quantity'] > 0
        has_price = item.get('unit_price') is not None and item['unit_price'] > 0
        
        return has_description and (has_quantity or has_price)
    
    def _clean_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia y normaliza un item"""
        cleaned = item.copy()
        
        # Limpiar descripción
        cleaned['description'] = re.sub(r'\s+', ' ', cleaned.get('description', '')).strip()
        
        # Normalizar unidad
        unit = cleaned.get('unit', '').lower()
        unit_mapping = {
            'metros cuadrados': 'm2',
            'metros cúbicos': 'm3',
            'kilogramos': 'kg',
            'litros': 'l',
            'unidades': 'un',
            'metros': 'm'
        }
        cleaned['unit'] = unit_mapping.get(unit, cleaned.get('unit', ''))
        
        # Calcular precio total si falta
        if cleaned.get('quantity') and cleaned.get('unit_price') and not cleaned.get('total_price'):
            cleaned['total_price'] = cleaned['quantity'] * cleaned['unit_price']
        
        # Generar código si falta
        if not cleaned.get('code'):
            cleaned['code'] = f"AUTO_{len(cleaned) + 1:03d}"
        
        return cleaned
    
    def extract_totals(self, text: str) -> Dict[str, Decimal]:
        """
        Extrae totales del presupuesto
        """
        totals = {
            'subtotal': Decimal('0.00'),
            'tax': Decimal('0.00'),
            'total': Decimal('0.00'),
            'profit': Decimal('0.00')
        }
        
        lines = text.upper().split('\n')
        
        for line in lines:
            # Buscar patrones de totales
            if any(keyword in line for keyword in ['SUBTOTAL', 'SUB-TOTAL', 'SUB TOTAL']):
                amount = self._extract_amount_from_line(line)
                if amount:
                    totals['subtotal'] = amount
            
            elif any(keyword in line for keyword in ['IVA', 'TAX', 'IMPUESTO']):
                amount = self._extract_amount_from_line(line)
                if amount:
                    totals['tax'] = amount
            
            elif any(keyword in line for keyword in ['TOTAL', 'TOTAL GENERAL']):
                amount = self._extract_amount_from_line(line)
                if amount:
                    totals['total'] = amount
            
            elif any(keyword in line for keyword in ['BENEFICIO', 'GANANCIA', 'PROFIT']):
                amount = self._extract_amount_from_line(line)
                if amount:
                    totals['profit'] = amount
        
        return totals
    
    def _extract_amount_from_line(self, line: str) -> Optional[Decimal]:
        """Extrae un monto de una línea de texto"""
        for pattern in self.currency_patterns:
            matches = re.findall(pattern, line)
            if matches:
                try:
                    clean_amount = matches[-1].replace('$', '').replace(',', '')
                    return Decimal(clean_amount)
                except:
                    continue
        
        return None