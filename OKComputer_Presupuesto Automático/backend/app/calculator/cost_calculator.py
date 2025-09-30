from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class CostCalculator:
    """Calcula costos indirectos y desgloses de costos"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def calculate_detailed_costs(self, base_cost: Decimal, unit_data: Dict[str, Any], 
                               quantity: Decimal) -> Dict[str, Any]:
        """
        Calcula el desglose detallado de costos para una partida
        
        Args:
            base_cost: Costo base unitario
            unit_data: Datos de la unidad de trabajo
            quantity: Cantidad de trabajo
            
        Returns:
            Dict con desglose completo de costos
        """
        try:
            # Costos directos principales
            labor_cost = base_cost * (Decimal(str(unit_data.get('labor_percentage', 40))) / 100)
            material_cost = base_cost * (Decimal(str(unit_data.get('material_percentage', 50))) / 100)
            equipment_cost = base_cost * (Decimal(str(unit_data.get('equipment_percentage', 10))) / 100)
            
            # Calcular costos indirectos
            indirect_costs = self._calculate_indirect_breakdown(
                labor_cost + material_cost + equipment_cost,
                unit_data
            )
            
            # Costo total directo
            direct_cost = labor_cost + material_cost + equipment_cost
            
            # Costos indirectos totales
            total_indirect = sum(indirect_costs.values())
            
            # Costo total
            total_cost = direct_cost + total_indirect
            
            return {
                'base_cost': base_cost,
                'quantity': quantity,
                'direct_costs': {
                    'labor': {
                        'amount': labor_cost,
                        'percentage': unit_data.get('labor_percentage', 40),
                        'description': 'Mano de obra directa'
                    },
                    'materials': {
                        'amount': material_cost,
                        'percentage': unit_data.get('material_percentage', 50),
                        'description': 'Materiales y suministros'
                    },
                    'equipment': {
                        'amount': equipment_cost,
                        'percentage': unit_data.get('equipment_percentage', 10),
                        'description': 'Equipo y maquinaria'
                    },
                    'total': direct_cost
                },
                'indirect_costs': indirect_costs,
                'total_indirect': total_indirect,
                'total_cost': total_cost,
                'cost_per_unit': total_cost / quantity if quantity > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculando costos detallados: {str(e)}")
            raise
    
    def _calculate_indirect_breakdown(self, direct_cost: Decimal, unit_data: Dict[str, Any]) -> Dict[str, Decimal]:
        """Calcula el desglose de costos indirectos"""
        
        # Factores estándar de costos indirectos en construcción
        indirect_factors = {
            'transportation': Decimal('0.025'),    # 2.5% - Transporte y acarreo
            'tools_small_equipment': Decimal('0.015'),  # 1.5% - Herramientas menores
            'machinery_rental': Decimal('0.030'),  # 3.0% - Alquiler de maquinaria
            'safety_equipment': Decimal('0.010'),  # 1.0% - Equipos de seguridad
            'temporary_facilities': Decimal('0.020'),  # 2.0% - Instalaciones temporales
            'quality_control': Decimal('0.015'),   # 1.5% - Control de calidad
            'administration': Decimal('0.040'),    # 4.0% - Administración y supervisión
            'contingency': Decimal('0.025'),       # 2.5% - Contingencias imprevistos
            'profit_margin': Decimal('0.150')      # 15.0% - Beneficio (se ajusta según proyecto)
        }
        
        # Ajustar factores según tipo de trabajo
        adjusted_factors = self._adjust_factors_by_work_type(indirect_factors, unit_data)
        
        # Calcular costos indirectos
        indirect_costs = {}
        for cost_type, factor in adjusted_factors.items():
            if cost_type != 'profit_margin':  # El beneficio se calcula aparte
                indirect_costs[cost_type] = direct_cost * factor
        
        return indirect_costs
    
    def _adjust_factors_by_work_type(self, base_factors: Dict[str, Decimal], 
                                   unit_data: Dict[str, Any]) -> Dict[str, Decimal]:
        """Ajusta los factores de costos indirectos según el tipo de trabajo"""
        
        # Identificar tipo de trabajo basado en descripción o categoría
        description = unit_data.get('description', '').lower()
        category = unit_data.get('category', '').lower()
        
        adjusted_factors = base_factors.copy()
        
        # Ajustes específicos por tipo de trabajo
        if any(keyword in description for keyword in ['demolición', 'demolicion', 'demolition']):
            # Los trabajos de demolición requieren más maquinaria y seguridad
            adjusted_factors['machinery_rental'] *= Decimal('1.5')
            adjusted_factors['safety_equipment'] *= Decimal('1.8')
            adjusted_factors['transportation'] *= Decimal('1.3')  # Más acarreo de escombros
            
        elif any(keyword in description for keyword in ['excavación', 'excavacion', 'excavation']):
            # Excavación requiere maquinaria pesada
            adjusted_factors['machinery_rental'] *= Decimal('2.0')
            adjusted_factors['fuel_maintenance'] = Decimal('0.040')  # 4% combustible y mantenimiento
            
        elif any(keyword in description for keyword in ['concreto', 'concrete', 'hormigón']):
            # Concreto requiere control de calidad estricto y transporte
            adjusted_factors['quality_control'] *= Decimal('1.5')
            adjusted_factors['transportation'] *= Decimal('1.4')
            
        elif any(keyword in description for keyword in ['acero', 'steel', 'armadura', 'reinforcement']):
            # Acero de refuerzo requiere herramientas especializadas
            adjusted_factors['tools_small_equipment'] *= Decimal('1.3')
            adjusted_factors['transportation'] *= Decimal('1.2')
            
        elif any(keyword in description for keyword in ['pintura', 'paint', 'acabado', 'finishing']):
            # Acabados requieren menos maquinaria pero más herramientas
            adjusted_factors['machinery_rental'] *= Decimal('0.7')
            adjusted_factors['tools_small_equipment'] *= Decimal('1.4')
            
        elif any(keyword in description for keyword in ['instalación', 'installation', 'electrica', 'sanitaria']):
            # Instalaciones requieren herramientas especializadas y seguridad
            adjusted_factors['tools_small_equipment'] *= Decimal('1.5')
            adjusted_factors['safety_equipment'] *= Decimal('1.3')
            
        # Ajustes por ubicación o condiciones especiales
        if any(keyword in description for keyword in ['altura', 'height', 'elevado']):
            # Trabajo en altura requiere más seguridad y equipos especiales
            adjusted_factors['safety_equipment'] *= Decimal('1.8')
            adjusted_factors['temporary_facilities'] *= Decimal('1.4')
            
        elif any(keyword in description for keyword in ['subterráneo', 'underground', 'subterraneo']):
            # Trabajo subterráneo requiere ventilación y seguridad extra
            adjusted_factors['safety_equipment'] *= Decimal('1.6')
            adjusted_factors['temporary_facilities'] *= Decimal('1.5')
        
        return adjusted_factors
    
    def calculate_equipment_needs(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula las necesidades de equipo y maquinaria"""
        
        equipment_catalog = {
            'excavator': {
                'description': 'Excavadora',
                'hourly_cost': Decimal('150.00'),
                'productivity': Decimal('8.0'),  # m3/hora
                'applicable_to': ['excavación', 'excavation', 'demolición', 'demolition']
            },
            'concrete_mixer': {
                'description': 'Mezcladora de concreto',
                'hourly_cost': Decimal('25.00'),
                'productivity': Decimal('2.0'),  # m3/hora
                'applicable_to': ['concreto', 'concrete', 'mortero', 'mortar']
            },
            'compactor': {
                'description': 'Compactador',
                'hourly_cost': Decimal('80.00'),
                'productivity': Decimal('50.0'),  # m2/hora
                'applicable_to': ['relleno', 'fill', 'compactación', 'compaction']
            },
            'crane': {
                'description': 'Grúa',
                'hourly_cost': Decimal('200.00'),
                'productivity': Decimal('1.0'),  # viajes/hora
                'applicable_to': ['acero', 'steel', 'prefabricado', 'precast']
            },
            'concrete_pump': {
                'description': 'Bomba de concreto',
                'hourly_cost': Decimal('120.00'),
                'productivity': Decimal('15.0'),  # m3/hora
                'applicable_to': ['concreto', 'concrete']
            }
        }
        
        equipment_needs = {}
        total_equipment_cost = Decimal('0.00')
        
        for item in items:
            description = item.get('description', '').lower()
            quantity = Decimal(str(item.get('quantity', 0)))
            
            # Determinar equipos necesarios para este item
            for equipment_key, equipment in equipment_catalog.items():
                if any(keyword in description for keyword in equipment['applicable_to']):
                    
                    if equipment_key not in equipment_needs:
                        equipment_needs[equipment_key] = {
                            'description': equipment['description'],
                            'total_hours': Decimal('0.00'),
                            'total_cost': Decimal('0.00'),
                            'items': []
                        }
                    
                    # Calcular horas necesarias
                    required_hours = quantity / equipment['productivity']
                    equipment_cost = required_hours * equipment['hourly_cost']
                    
                    equipment_needs[equipment_key]['total_hours'] += required_hours
                    equipment_needs[equipment_key]['total_cost'] += equipment_cost
                    equipment_needs[equipment_key]['items'].append({
                        'item_code': item.get('code', ''),
                        'description': item.get('description', ''),
                        'quantity': quantity,
                        'required_hours': required_hours,
                        'cost': equipment_cost
                    })
                    
                    total_equipment_cost += equipment_cost
        
        return {
            'equipment_needs': equipment_needs,
            'total_cost': total_equipment_cost,
            'recommendations': self._generate_equipment_recommendations(equipment_needs)
        }
    
    def _generate_equipment_recommendations(self, equipment_needs: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones para el uso de equipo"""
        recommendations = []
        
        for equipment_key, data in equipment_needs.items():
            if data['total_hours'] > 40:  # Más de una semana de trabajo
                recommendations.append(
                    f"Considerar contrato mensual para {data['description']} "
                    f"({data['total_hours']:.1f} horas totales)"
                )
            
            elif data['total_hours'] > 8:  # Más de un día
                recommendations.append(
                    f"Planificar renta diaria para {data['description']} "
                    f"({data['total_hours']:.1f} horas totales)"
                )
            
            if len(data['items']) > 3:
                recommendations.append(
                    f"Optimizar uso de {data['description']} en múltiples actividades "
                    f"({len(data['items'])} items)"
                )
        
        return recommendations
    
    def calculate_labor_productivity(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula la productividad laboral esperada"""
        
        # Tasas de productividad estándar (unidades por jornada de 8 horas)
        productivity_rates = {
            'concreto_fundacion': {'unit': 'm3', 'rate': 4.0, 'crew_size': 6},
            'concreto_columnas': {'unit': 'm3', 'rate': 2.5, 'crew_size': 8},
            'acero_refuerzo': {'unit': 'kg', 'rate': 150.0, 'crew_size': 4},
            'encofrado': {'unit': 'm2', 'rate': 25.0, 'crew_size': 6},
            'mamposteria': {'unit': 'm2', 'rate': 8.0, 'crew_size': 4},
            'pintura': {'unit': 'm2', 'rate': 80.0, 'crew_size': 3},
            'excavacion_manual': {'unit': 'm3', 'rate': 6.0, 'crew_size': 4},
            'demolicion_concreto': {'unit': 'm3', 'rate': 3.0, 'crew_size': 6}
        }
        
        productivity_analysis = {}
        total_estimated_days = Decimal('0.00')
        
        for item in items:
            description = item.get('description', '').lower()
            quantity = Decimal(str(item.get('quantity', 0)))
            
            # Encontrar la tasa de productividad más apropiada
            matched_rate = None
            for key, rate_data in productivity_rates.items():
                keywords = key.split('_')
                if all(keyword in description for keyword in keywords):
                    matched_rate = rate_data
                    break
            
            if matched_rate:
                # Calcular días necesarios
                daily_output = Decimal(str(matched_rate['rate']))
                required_days = quantity / daily_output
                
                productivity_analysis[description[:50]] = {
                    'quantity': quantity,
                    'unit': matched_rate['unit'],
                    'daily_rate': daily_output,
                    'crew_size': matched_rate['crew_size'],
                    'estimated_days': required_days,
                    'total_worker_days': required_days * matched_rate['crew_size']
                }
                
                total_estimated_days += required_days
        
        # Estadísticas generales
        total_worker_days = sum(analysis['total_worker_days'] for analysis in productivity_analysis.values())
        
        return {
            'productivity_analysis': productivity_analysis,
            'total_estimated_days': total_estimated_days,
            'total_worker_days': total_worker_days,
            'recommendations': self._generate_productivity_recommendations(productivity_analysis)
        }
    
    def _generate_productivity_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones de productividad"""
        recommendations = []
        
        for description, data in analysis.items():
            if data['estimated_days'] > 30:  # Más de un mes
                recommendations.append(
                    f"Considerar división en fases para {description[:30]}... "
                    f"({data['estimated_days']:.1f} días)"
                )
            
            if data['crew_size'] > 8:
                recommendations.append(
                    f"Optimizar tamaño de cuadrilla para {description[:30]}... "
                    f"({data['crew_size']} trabajadores)"
                )
        
        return recommendations