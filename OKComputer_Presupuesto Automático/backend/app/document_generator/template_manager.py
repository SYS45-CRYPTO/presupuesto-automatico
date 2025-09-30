import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TemplateManager:
    """Gestiona plantillas de documentos y configuraciones de exportación"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Carga las plantillas disponibles"""
        try:
            # Plantillas predefinidas
            self.templates = {
                'standard_budget': {
                    'name': 'Presupuesto Estándar',
                    'description': 'Formato estándar de presupuesto con todos los detalles',
                    'type': 'budget',
                    'format': 'pdf',
                    'sections': [
                        'cover_page',
                        'executive_summary',
                        'chapter_breakdown',
                        'detailed_items',
                        'cost_analysis',
                        'terms_conditions'
                    ],
                    'styles': {
                        'primary_color': '#2E4057',
                        'secondary_color': '#5D6D7E',
                        'accent_color': '#34495E',
                        'font_family': 'Helvetica',
                        'include_logo': True,
                        'show_chapter_totals': True,
                        'show_item_details': True
                    },
                    'settings': {
                        'page_size': 'A4',
                        'margins': {'top': 0.75, 'bottom': 0.75, 'left': 0.75, 'right': 0.75},
                        'include_page_numbers': True,
                        'include_date': True,
                        'validity_days': 30
                    }
                },
                'summary_budget': {
                    'name': 'Presupuesto Resumido',
                    'description': 'Formato resumido con información esencial',
                    'type': 'budget',
                    'format': 'pdf',
                    'sections': [
                        'cover_page',
                        'executive_summary',
                        'chapter_breakdown',
                        'cost_analysis'
                    ],
                    'styles': {
                        'primary_color': '#2E4057',
                        'secondary_color': '#5D6D7E',
                        'accent_color': '#34495E',
                        'font_family': 'Helvetica',
                        'include_logo': True,
                        'show_chapter_totals': True,
                        'show_item_details': False
                    },
                    'settings': {
                        'page_size': 'A4',
                        'margins': {'top': 0.75, 'bottom': 0.75, 'left': 0.75, 'right': 0.75},
                        'include_page_numbers': True,
                        'include_date': True,
                        'validity_days': 30
                    }
                },
                'detailed_budget': {
                    'name': 'Presupuesto Detallado',
                    'description': 'Formato con máximo detalle incluyendo análisis',
                    'type': 'budget',
                    'format': 'pdf',
                    'sections': [
                        'cover_page',
                        'executive_summary',
                        'chapter_breakdown',
                        'detailed_items',
                        'cost_analysis',
                        'materials_analysis',
                        'labor_analysis',
                        'terms_conditions'
                    ],
                    'styles': {
                        'primary_color': '#2E4057',
                        'secondary_color': '#5D6D7E',
                        'accent_color': '#34495E',
                        'font_family': 'Helvetica',
                        'include_logo': True,
                        'show_chapter_totals': True,
                        'show_item_details': True,
                        'show_breakdown_charts': True
                    },
                    'settings': {
                        'page_size': 'A4',
                        'margins': {'top': 0.75, 'bottom': 0.75, 'left': 0.75, 'right': 0.75},
                        'include_page_numbers': True,
                        'include_date': True,
                        'validity_days': 30
                    }
                },
                'excel_standard': {
                    'name': 'Excel Estándar',
                    'description': 'Exportación estándar a Excel con múltiples hojas',
                    'type': 'excel',
                    'format': 'xlsx',
                    'sheets': [
                        'summary',
                        'detailed_items',
                        'cost_analysis',
                        'charts'
                    ],
                    'settings': {
                        'include_charts': True,
                        'include_formulas': True,
                        'auto_adjust_columns': True,
                        'add_borders': True
                    }
                },
                'csv_simple': {
                    'name': 'CSV Simple',
                    'description': 'Exportación simple a CSV con datos básicos',
                    'type': 'csv',
                    'format': 'csv',
                    'sections': [
                        'header_info',
                        'summary',
                        'detailed_items'
                    ],
                    'settings': {
                        'delimiter': ',',
                        'encoding': 'utf-8',
                        'include_headers': True
                    }
                }
            }
            
            logger.info(f"Plantillas cargadas: {list(self.templates.keys())}")
            
        except Exception as e:
            logger.error(f"Error cargando plantillas: {str(e)}")
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una plantilla por ID"""
        return self.templates.get(template_id)
    
    def get_templates_by_type(self, template_type: str) -> Dict[str, Any]:
        """Obtiene plantillas por tipo"""
        return {
            template_id: template 
            for template_id, template in self.templates.items() 
            if template.get('type') == template_type
        }
    
    def get_all_templates(self) -> Dict[str, Any]:
        """Obtiene todas las plantillas"""
        return self.templates.copy()
    
    def create_custom_template(self, template_data: Dict[str, Any]) -> str:
        """
        Crea una plantilla personalizada
        
        Args:
            template_data: Datos de la plantilla
            
        Returns:
            ID de la plantilla creada
        """
        try:
            template_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Validar datos de plantilla
            required_fields = ['name', 'type', 'format']
            for field in required_fields:
                if field not in template_data:
                    raise ValueError(f"Campo requerido faltante: {field}")
            
            # Agregar metadatos
            template_data['created_at'] = datetime.now().isoformat()
            template_data['is_custom'] = True
            
            self.templates[template_id] = template_data
            
            # Guardar plantilla en archivo
            self._save_template_to_file(template_id, template_data)
            
            logger.info(f"Plantilla personalizada creada: {template_id}")
            return template_id
            
        except Exception as e:
            logger.error(f"Error creando plantilla personalizada: {str(e)}")
            raise
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """
        Actualiza una plantilla existente
        
        Args:
            template_id: ID de la plantilla
            updates: Actualizaciones a aplicar
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            if template_id not in self.templates:
                return False
            
            # No permitir actualizar plantillas del sistema
            if not self.templates[template_id].get('is_custom', False):
                raise ValueError("No se pueden modificar plantillas del sistema")
            
            # Actualizar plantilla
            self.templates[template_id].update(updates)
            self.templates[template_id]['updated_at'] = datetime.now().isoformat()
            
            # Guardar cambios
            self._save_template_to_file(template_id, self.templates[template_id])
            
            logger.info(f"Plantilla actualizada: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando plantilla: {str(e)}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """
        Elimina una plantilla personalizada
        
        Args:
            template_id: ID de la plantilla
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            if template_id not in self.templates:
                return False
            
            # No permitir eliminar plantillas del sistema
            if not self.templates[template_id].get('is_custom', False):
                raise ValueError("No se pueden eliminar plantillas del sistema")
            
            # Eliminar plantilla
            del self.templates[template_id]
            
            # Eliminar archivo
            template_file = self.templates_dir / f"{template_id}.json"
            if template_file.exists():
                template_file.unlink()
            
            logger.info(f"Plantilla eliminada: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando plantilla: {str(e)}")
            return False
    
    def validate_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida los datos de una plantilla
        
        Args:
            template_data: Datos de la plantilla a validar
            
        Returns:
            Dict con resultado de validación
        """
        errors = []
        warnings = []
        
        # Validar campos requeridos
        required_fields = ['name', 'type', 'format']
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                errors.append(f"Campo requerido faltante o vacío: {field}")
        
        # Validar tipos permitidos
        valid_types = ['budget', 'excel', 'csv']
        if template_data.get('type') not in valid_types:
            errors.append(f"Tipo de plantilla inválido: {template_data.get('type')}")
        
        # Validar formatos permitidos
        valid_formats = ['pdf', 'xlsx', 'csv']
        if template_data.get('format') not in valid_formats:
            errors.append(f"Formato de plantilla inválido: {template_data.get('format')}")
        
        # Validar secciones para plantillas de presupuesto
        if template_data.get('type') == 'budget':
            valid_sections = [
                'cover_page', 'executive_summary', 'chapter_breakdown',
                'detailed_items', 'cost_analysis', 'materials_analysis',
                'labor_analysis', 'terms_conditions'
            ]
            
            sections = template_data.get('sections', [])
            for section in sections:
                if section not in valid_sections:
                    warnings.append(f"Sección desconocida: {section}")
        
        # Validar estilos
        styles = template_data.get('styles', {})
        if styles:
            # Validar colores hex
            color_fields = ['primary_color', 'secondary_color', 'accent_color']
            for field in color_fields:
                if field in styles:
                    color = styles[field]
                    if not self._is_valid_hex_color(color):
                        warnings.append(f"Color hex inválido en {field}: {color}")
        
        # Validar configuraciones
        settings = template_data.get('settings', {})
        if settings:
            # Validar márgenes
            margins = settings.get('margins', {})
            if margins:
                for margin_type, value in margins.items():
                    if not isinstance(value, (int, float)) or value < 0:
                        warnings.append(f"Valor de margen inválido en {margin_type}: {value}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_template_config(self, template_id: str, config_key: str) -> Any:
        """Obtiene una configuración específica de una plantilla"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        # Buscar en configuraciones específicas
        if 'settings' in template and config_key in template['settings']:
            return template['settings'][config_key]
        
        # Buscar en estilos
        if 'styles' in template and config_key in template['styles']:
            return template['styles'][config_key]
        
        return None
    
    def apply_template_overrides(self, base_template: Dict[str, Any], 
                               overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica sobreescrituras a una plantilla base
        
        Args:
            base_template: Plantilla base
            overrides: Sobreescrituras a aplicar
            
        Returns:
            Plantilla con sobreescrituras aplicadas
        """
        try:
            # Crear copia de la plantilla base
            result = base_template.copy()
            
            # Aplicar sobreescrituras de estilos
            if 'styles' in overrides and 'styles' in result:
                result['styles'].update(overrides['styles'])
            
            # Aplicar sobreescrituras de configuraciones
            if 'settings' in overrides and 'settings' in result:
                result['settings'].update(overrides['settings'])
            
            # Aplicar otras sobreescrituras
            for key, value in overrides.items():
                if key not in ['styles', 'settings']:
                    result[key] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Error aplicando sobreescrituras: {str(e)}")
            return base_template
    
    def get_export_config(self, template_id: str, export_format: str) -> Dict[str, Any]:
        """Obtiene configuración de exportación para un formato específico"""
        
        template = self.get_template(template_id)
        if not template:
            return {}
        
        # Configuraciones por formato
        format_configs = {
            'pdf': {
                'page_size': template.get('settings', {}).get('page_size', 'A4'),
                'margins': template.get('settings', {}).get('margins', {}),
                'include_logo': template.get('styles', {}).get('include_logo', True),
                'include_page_numbers': template.get('settings', {}).get('include_page_numbers', True),
                'styles': template.get('styles', {})
            },
            'excel': {
                'include_charts': template.get('settings', {}).get('include_charts', True),
                'include_formulas': template.get('settings', {}).get('include_formulas', True),
                'auto_adjust_columns': template.get('settings', {}).get('auto_adjust_columns', True),
                'add_borders': template.get('settings', {}).get('add_borders', True),
                'sheets': template.get('sheets', ['summary', 'detailed_items'])
            },
            'csv': {
                'delimiter': template.get('settings', {}).get('delimiter', ','),
                'encoding': template.get('settings', {}).get('encoding', 'utf-8'),
                'include_headers': template.get('settings', {}).get('include_headers', True)
            }
        }
        
        return format_configs.get(export_format, {})
    
    def _save_template_to_file(self, template_id: str, template_data: Dict[str, Any]):
        """Guarda una plantilla en archivo"""
        try:
            template_file = self.templates_dir / f"{template_id}.json"
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error guardando plantilla en archivo: {str(e)}")
    
    def _load_templates_from_files(self):
        """Carga plantillas desde archivos"""
        try:
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        template_id = template_file.stem
                        self.templates[template_id] = template_data
                        
                except Exception as e:
                    logger.warning(f"Error cargando plantilla {template_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error cargando plantillas desde archivos: {str(e)}")
    
    def _is_valid_hex_color(self, color: str) -> bool:
        """Valida si un string es un color hex válido"""
        if not color.startswith('#'):
            return False
        
        hex_part = color[1:]
        if len(hex_part) not in [3, 6]:
            return False
        
        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False
    
    def create_template_from_budget(self, budget_data: Dict[str, Any], 
                                  template_name: str, description: str = "") -> str:
        """
        Crea una plantilla basada en un presupuesto existente
        
        Args:
            budget_data: Datos del presupuesto
            template_name: Nombre de la plantilla
            description: Descripción opcional
            
        Returns:
            ID de la plantilla creada
        """
        try:
            # Analizar estructura del presupuesto
            has_chapters = any(item.get('chapter') for item in budget_data.get('items', []))
            has_detailed_costs = bool(budget_data.get('cost_breakdown', {}))
            
            # Crear plantilla base
            template_data = {
                'name': template_name,
                'description': description or f"Plantilla basada en presupuesto {budget_data.get('project', {}).get('name', '')}",
                'type': 'budget',
                'format': 'pdf',
                'based_on_budget': budget_data.get('id'),
                'sections': [
                    'cover_page',
                    'executive_summary',
                    'chapter_breakdown' if has_chapters else 'detailed_items',
                    'detailed_items',
                    'cost_analysis' if has_detailed_costs else '',
                    'terms_conditions'
                ],
                'styles': {
                    'primary_color': '#2E4057',
                    'secondary_color': '#5D6D7E',
                    'accent_color': '#34495E',
                    'font_family': 'Helvetica',
                    'include_logo': True,
                    'show_chapter_totals': has_chapters,
                    'show_item_details': True
                },
                'settings': {
                    'page_size': 'A4',
                    'margins': {'top': 0.75, 'bottom': 0.75, 'left': 0.75, 'right': 0.75},
                    'include_page_numbers': True,
                    'include_date': True,
                    'validity_days': 30
                }
            }
            
            # Limpiar secciones vacías
            template_data['sections'] = [s for s in template_data['sections'] if s]
            
            return self.create_custom_template(template_data)
            
        except Exception as e:
            logger.error(f"Error creando plantilla desde presupuesto: {str(e)}")
            raise
    
    def export_template(self, template_id: str, output_path: str) -> bool:
        """
        Exporta una plantilla a archivo JSON
        
        Args:
            template_id: ID de la plantilla
            output_path: Ruta de salida
            
        Returns:
            True si se exportó exitosamente
        """
        try:
            template = self.get_template(template_id)
            if not template:
                return False
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Plantilla exportada: {template_id} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando plantilla: {str(e)}")
            return False
    
    def import_template(self, template_path: str) -> str:
        """
        Importa una plantilla desde archivo JSON
        
        Args:
            template_path: Ruta del archivo de plantilla
            
        Returns:
            ID de la plantilla importada
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # Validar plantilla
            validation = self.validate_template(template_data)
            if not validation['is_valid']:
                raise ValueError(f"Plantilla inválida: {validation['errors']}")
            
            # Generar nuevo ID
            template_data['is_custom'] = True
            template_data['imported_from'] = template_path
            
            return self.create_custom_template(template_data)
            
        except Exception as e:
            logger.error(f"Error importando plantilla: {str(e)}")
            raise