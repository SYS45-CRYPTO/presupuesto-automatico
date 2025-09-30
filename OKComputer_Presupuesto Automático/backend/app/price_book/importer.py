import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import io

logger = logging.getLogger(__name__)

class PriceBookImporter:
    """Importa libros de precios desde archivos Excel o CSV"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        self.required_columns = ['code', 'description', 'unit', 'unit_price']
        self.optional_columns = [
            'category', 'labor_percentage', 'material_percentage', 
            'equipment_percentage', 'performance_rate', 'notes'
        ]
        
        # Mapeo de nombres de columnas comunes
        self.column_mappings = {
            'code': ['code', 'codigo', 'código', 'item_code', 'partida', 'numero'],
            'description': ['description', 'descripcion', 'descripción', 'desc', 'concepto', 'work_item'],
            'unit': ['unit', 'unidad', 'unit_of_measure', 'uom', 'medida'],
            'unit_price': ['unit_price', 'precio_unitario', 'precio', 'price', 'cost', 'costo'],
            'category': ['category', 'categoria', 'categoría', 'type', 'tipo', 'class', 'clase'],
            'labor_percentage': ['labor_pct', 'mano_obra_pct', 'labor_percentage', 'porcentaje_mano_obra'],
            'material_percentage': ['material_pct', 'materiales_pct', 'material_percentage', 'porcentaje_materiales'],
            'equipment_percentage': ['equipment_pct', 'equipo_pct', 'equipment_percentage', 'porcentaje_equipo'],
            'performance_rate': ['performance', 'rendimiento', 'performance_rate', 'output_rate'],
            'notes': ['notes', 'notas', 'comments', 'comentarios', 'observations', 'observaciones']
        }
    
    def import_from_file(self, file_path: str, price_book_id: int, 
                        mapping_overrides: Optional[Dict] = None,
                        validation_rules: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Importa un libro de precios desde un archivo
        
        Args:
            file_path: Ruta al archivo
            price_book_id: ID del libro de precios
            mapping_overrides: Mapeos personalizados de columnas
            validation_rules: Reglas de validación personalizadas
            
        Returns:
            Dict con resultado de la importación
        """
        try:
            # Validar archivo
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            if file_path.suffix.lower() not in self.supported_formats:
                raise ValueError(f"Formato no soportado: {file_path.suffix}")
            
            # Leer archivo
            logger.info(f"Leyendo archivo: {file_path}")
            df = self._read_file(file_path)
            
            if df.empty:
                raise ValueError("El archivo está vacío")
            
            # Mapear columnas
            column_mapping = self._map_columns(df.columns.tolist(), mapping_overrides)
            
            # Renombrar columnas según el mapeo
            df = df.rename(columns=column_mapping)
            
            # Limpiar y validar datos
            df = self._clean_data(df)
            validation_result = self._validate_data(df, validation_rules)
            
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'errors': validation_result['errors'],
                    'warnings': validation_result['warnings'],
                    'total_rows': len(df),
                    'processed_rows': 0
                }
            
            # Convertir a formato de entrada de base de datos
            entries = self._convert_to_entries(df, price_book_id)
            
            # Estadísticas de importación
            stats = {
                'total_rows': len(df),
                'valid_entries': len(entries),
                'validation_errors': len(validation_result['errors']),
                'warnings': len(validation_result['warnings']),
                'price_range': self._calculate_price_range(entries),
                'categories_found': self._extract_categories(entries),
                'units_found': self._extract_units(entries)
            }
            
            logger.info(f"Importación completada: {len(entries)} entradas válidas de {len(df)} filas")
            
            return {
                'success': True,
                'entries': entries,
                'stats': stats,
                'warnings': validation_result['warnings']
            }
            
        except Exception as e:
            logger.error(f"Error en importación: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total_rows': 0,
                'processed_rows': 0
            }
    
    def import_from_bytes(self, file_content: bytes, filename: str, price_book_id: int,
                         mapping_overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Importa un libro de precios desde contenido en memoria
        
        Args:
            file_content: Contenido del archivo como bytes
            filename: Nombre original del archivo
            price_book_id: ID del libro de precios
            mapping_overrides: Mapeos personalizados de columnas
            
        Returns:
            Dict con resultado de la importación
        """
        try:
            # Determinar formato
            suffix = Path(filename).suffix.lower()
            
            # Leer desde bytes
            if suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(io.BytesIO(file_content))
            elif suffix == '.csv':
                # Intentar diferentes encodings
                encodings = ['utf-8', 'latin-1', 'cp1252']
                df = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(io.StringIO(file_content.decode(encoding)))
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    raise ValueError("No se pudo decodificar el archivo CSV")
            else:
                raise ValueError(f"Formato no soportado: {suffix}")
            
            if df.empty:
                raise ValueError("El archivo está vacío")
            
            # Mapear columnas
            column_mapping = self._map_columns(df.columns.tolist(), mapping_overrides)
            df = df.rename(columns=column_mapping)
            
            # Limpiar y validar datos
            df = self._clean_data(df)
            validation_result = self._validate_data(df)
            
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'errors': validation_result['errors'],
                    'warnings': validation_result['warnings']
                }
            
            # Convertir a entradas
            entries = self._convert_to_entries(df, price_book_id)
            
            return {
                'success': True,
                'entries': entries,
                'stats': {
                    'total_rows': len(df),
                    'valid_entries': len(entries),
                    'categories_found': self._extract_categories(entries),
                    'units_found': self._extract_units(entries)
                }
            }
            
        except Exception as e:
            logger.error(f"Error importando desde bytes: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _read_file(self, file_path: Path) -> pd.DataFrame:
        """Lee el archivo según su formato"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.csv':
            # Intentar diferentes encodings para CSV
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    return pd.read_csv(file_path, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("No se pudo decodificar el archivo CSV")
        
        elif suffix in ['.xlsx', '.xls']:
            # Para Excel, intentar leer todas las hojas y usar la más grande
            excel_file = pd.ExcelFile(file_path)
            
            if len(excel_file.sheet_names) == 1:
                return pd.read_excel(file_path)
            else:
                # Buscar la hoja con más datos
                best_sheet = None
                max_rows = 0
                
                for sheet_name in excel_file.sheet_names:
                    try:
                        df_temp = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10)
                        if len(df_temp) > max_rows:
                            max_rows = len(df_temp)
                            best_sheet = sheet_name
                    except:
                        continue
                
                if best_sheet:
                    return pd.read_excel(file_path, sheet_name=best_sheet)
                else:
                    # Usar la primera hoja como fallback
                    return pd.read_excel(file_path, sheet_name=0)
        
        else:
            raise ValueError(f"Formato de archivo no soportado: {suffix}")
    
    def _map_columns(self, df_columns: List[str], mapping_overrides: Optional[Dict] = None) -> Dict[str, str]:
        """Mapea las columnas del archivo a las columnas esperadas"""
        mapping = {}
        used_columns = set()
        
        # Aplicar mapeos personalizados primero
        if mapping_overrides:
            for standard_col, file_col in mapping_overrides.items():
                if file_col in df_columns and file_col not in used_columns:
                    mapping[file_col] = standard_col
                    used_columns.add(file_col)
        
        # Buscar coincidencias con los mapeos estándar
        for standard_col, possible_names in self.column_mappings.items():
            if standard_col in mapping.values():
                continue  # Ya mapeado
            
            for possible_name in possible_names:
                # Buscar coincidencia exacta (case-insensitive)
                for df_col in df_columns:
                    if df_col.lower() == possible_name.lower() and df_col not in used_columns:
                        mapping[df_col] = standard_col
                        used_columns.add(df_col)
                        break
                
                if standard_col in mapping.values():
                    break
                
                # Buscar coincidencia parcial
                for df_col in df_columns:
                    if possible_name.lower() in df_col.lower() and df_col not in used_columns:
                        # Verificar que no sea una coincidencia ambigua
                        if len(df_col) < len(possible_name) * 2:  # No demasiado largo
                            mapping[df_col] = standard_col
                            used_columns.add(df_col)
                            break
                
                if standard_col in mapping.values():
                    break
        
        # Verificar que tenemos las columnas requeridas
        mapped_columns = set(mapping.values())
        missing_required = [col for col in self.required_columns if col not in mapped_columns]
        
        if missing_required:
            logger.warning(f"Columnas requeridas faltantes: {missing_required}")
            logger.info(f"Columnas disponibles: {df_columns}")
            logger.info(f"Mapeo actual: {mapping}")
        
        return mapping
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza los datos"""
        # Hacer una copia para no modificar el original
        df_clean = df.copy()
        
        # Limpiar espacios en nombres de columnas
        df_clean.columns = df_clean.columns.str.strip()
        
        # Limpiar espacios en datos de texto
        for col in df_clean.select_dtypes(include=['object']).columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
            # Reemplazar valores vacíos o 'nan' con None
            df_clean[col] = df_clean[col].replace(['', 'nan', 'NaN', 'None'], None)
        
        # Convertir precios a formato numérico
        if 'unit_price' in df_clean.columns:
            df_clean['unit_price'] = pd.to_numeric(df_clean['unit_price'], errors='coerce')
        
        # Convertir porcentajes a formato numérico
        percentage_columns = ['labor_percentage', 'material_percentage', 'equipment_percentage']
        for col in percentage_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Convertir rendimiento a formato numérico
        if 'performance_rate' in df_clean.columns:
            df_clean['performance_rate'] = pd.to_numeric(df_clean['performance_rate'], errors='coerce')
        
        # Eliminar filas donde código y descripción sean nulos
        if 'code' in df_clean.columns and 'description' in df_clean.columns:
            df_clean = df_clean.dropna(subset=['code', 'description'], how='all')
        
        # Rellenar valores por defecto
        defaults = {
            'labor_percentage': 40.0,
            'material_percentage': 50.0,
            'equipment_percentage': 10.0,
            'performance_rate': 1.0,
            'unit': 'un',
            'category': 'General'
        }
        
        for col, default_value in defaults.items():
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna(default_value)
        
        return df_clean
    
    def _validate_data(self, df: pd.DataFrame, validation_rules: Optional[Dict] = None) -> Dict[str, Any]:
        """Valida los datos según las reglas establecidas"""
        errors = []
        warnings = []
        
        # Reglas de validación por defecto
        default_rules = {
            'min_price': 0.01,
            'max_price': 1000000,
            'required_fields': ['code', 'description', 'unit', 'unit_price'],
            'unique_codes': True,
            'valid_units': ['m2', 'm3', 'kg', 'ml', 'l', 'un', 'm', 'hm', 'km', 'pieza', 'juego', 'global']
        }
        
        rules = {**default_rules, **(validation_rules or {})}
        
        # Validar campos requeridos
        for field in rules['required_fields']:
            if field not in df.columns:
                errors.append(f"Campo requerido faltante: {field}")
                continue
            
            missing_count = df[field].isnull().sum()
            if missing_count > 0:
                warnings.append(f"{missing_count} filas con {field} faltante")
        
        # Validar códigos únicos
        if rules.get('unique_codes') and 'code' in df.columns:
            duplicate_codes = df[df.duplicated(subset=['code'], keep=False)]['code'].tolist()
            if duplicate_codes:
                warnings.append(f"Códigos duplicados encontrados: {set(duplicate_codes)}")
        
        # Validar rangos de precios
        if 'unit_price' in df.columns:
            invalid_prices = df[
                (df['unit_price'] < rules['min_price']) | 
                (df['unit_price'] > rules['max_price'])
            ]
            if len(invalid_prices) > 0:
                warnings.append(f"{len(invalid_prices)} precios fuera del rango esperado")
        
        # Validar unidades
        if 'unit' in df.columns and rules.get('valid_units'):
            invalid_units = df[~df['unit'].isin(rules['valid_units'])]['unit'].unique()
            if len(invalid_units) > 0:
                warnings.append(f"Unidades no reconocidas: {invalid_units}")
        
        # Validar porcentajes
        percentage_columns = ['labor_percentage', 'material_percentage', 'equipment_percentage']
        for col in percentage_columns:
            if col in df.columns:
                invalid_percentages = df[(df[col] < 0) | (df[col] > 100)][col].tolist()
                if invalid_percentages:
                    warnings.append(f"{col} con valores fuera del rango 0-100%")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _convert_to_entries(self, df: pd.DataFrame, price_book_id: int) -> List[Dict[str, Any]]:
        """Convierte el DataFrame a entradas de libro de precios"""
        entries = []
        
        for _, row in df.iterrows():
            entry = {
                'price_book_id': price_book_id,
                'code': str(row.get('code', '')).strip(),
                'description': str(row.get('description', '')).strip(),
                'unit': str(row.get('unit', 'un')).strip(),
                'unit_price': float(row.get('unit_price', 0)),
                'labor_percentage': float(row.get('labor_percentage', 40.0)),
                'material_percentage': float(row.get('material_percentage', 50.0)),
                'equipment_percentage': float(row.get('equipment_percentage', 10.0)),
                'performance_rate': float(row.get('performance_rate', 1.0)),
                'category': str(row.get('category', 'General')).strip(),
                'notes': str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else '',
                'is_active': True
            }
            
            # Validar entrada mínima
            if entry['code'] and entry['description'] and entry['unit_price'] > 0:
                entries.append(entry)
        
        return entries
    
    def _calculate_price_range(self, entries: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcula el rango de precios en las entradas"""
        if not entries:
            return {'min': 0, 'max': 0, 'average': 0}
        
        prices = [entry['unit_price'] for entry in entries]
        
        return {
            'min': float(min(prices)),
            'max': float(max(prices)),
            'average': float(sum(prices) / len(prices))
        }
    
    def _extract_categories(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Extrae las categorías únicas de las entradas"""
        categories = set(entry.get('category', 'General') for entry in entries)
        return sorted(list(categories))
    
    def _extract_units(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Extrae las unidades únicas de las entradas"""
        units = set(entry.get('unit', 'un') for entry in entries)
        return sorted(list(units))
    
    def export_template(self, output_path: str, format_type: str = 'xlsx') -> bool:
        """
        Exporta una plantilla de libro de precios
        
        Args:
            output_path: Ruta donde guardar la plantilla
            format_type: Formato de salida ('xlsx' o 'csv')
            
        Returns:
            True si se exportó exitosamente
        """
        try:
            # Crear DataFrame de ejemplo
            template_data = {
                'code': ['01.01.01', '01.01.02', '01.02.01', '02.01.01'],
                'description': [
                    'Demolición de concreto simple',
                    'Demolición de concreto reforzado', 
                    'Excavación manual',
                    'Concreto f\'c=200 kg/cm2'
                ],
                'unit': ['m3', 'm3', 'm3', 'm3'],
                'unit_price': [150.00, 250.00, 80.00, 1200.00],
                'category': ['Demolición', 'Demolición', 'Excavación', 'Concreto'],
                'labor_percentage': [60, 65, 70, 25],
                'material_percentage': [30, 25, 20, 70],
                'equipment_percentage': [10, 10, 10, 5],
                'performance_rate': [1.0, 0.8, 1.2, 1.0],
                'notes': [
                    'Incluye acarreo 30m',
                    'Incluye acarreo 30m',
                    'Incluye carga',
                    'Incluye vibrado'
                ]
            }
            
            df_template = pd.DataFrame(template_data)
            
            # Agregar fila de encabezados descriptivos
            header_row = {
                'code': 'Código de partida (formato: XX.XX.XX)',
                'description': 'Descripción detallada del trabajo',
                'unit': 'Unidad de medida (m2, m3, kg, un, etc.)',
                'unit_price': 'Precio unitario en moneda local',
                'category': 'Categoría o capítulo del trabajo',
                'labor_percentage': 'Porcentaje de mano de obra (0-100)',
                'material_percentage': 'Porcentaje de materiales (0-100)',
                'equipment_percentage': 'Porcentaje de equipo (0-100)',
                'performance_rate': 'Factor de rendimiento (ej: 1.0 = normal)',
                'notes': 'Notas adicionales o especificaciones'
            }
            
            df_header = pd.DataFrame([header_row])
            df_final = pd.concat([df_header, df_template], ignore_index=True)
            
            # Exportar según formato
            if format_type.lower() == 'xlsx':
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    df_final.to_excel(writer, sheet_name='Libro_Precios', index=False)
                    
                    # Obtener la hoja de trabajo para formateo
                    worksheet = writer.sheets['Libro_Precios']
                    
                    # Formatear encabezados
                    from openpyxl.styles import Font, PatternFill
                    
                    header_font = Font(bold=True, color='FFFFFF')
                    header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
                    
                    for cell in worksheet[1]:
                        cell.font = header_font
                        cell.fill = header_fill
                    
                    # Ajustar anchos de columna
                    column_widths = {
                        'A': 15,  # code
                        'B': 50,  # description
                        'C': 12,  # unit
                        'D': 15,  # unit_price
                        'E': 20,  # category
                        'F': 18,  # labor_percentage
                        'G': 20,  # material_percentage
                        'H': 20,  # equipment_percentage
                        'I': 18,  # performance_rate
                        'J': 40   # notes
                    }
                    
                    for col, width in column_widths.items():
                        worksheet.column_dimensions[col].width = width
            
            elif format_type.lower() == 'csv':
                df_final.to_csv(output_path, index=False, encoding='utf-8')
            
            else:
                raise ValueError(f"Formato de exportación no soportado: {format_type}")
            
            logger.info(f"Plantilla exportada exitosamente: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando plantilla: {str(e)}")
            return False