from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
import logging
from decimal import Decimal

from ..models.models import PerformanceRate, BudgetItem

logger = logging.getLogger(__name__)

class PerformanceService:
    """Gestiona rendimientos de operarios y productividad"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_performance_rate(self, rate_data: Dict[str, Any]) -> PerformanceRate:
        """Crea una nueva tasa de rendimiento"""
        try:
            rate = PerformanceRate(**rate_data)
            self.db.add(rate)
            self.db.commit()
            self.db.refresh(rate)
            logger.info(f"Tasa de rendimiento creada: {rate.code}")
            return rate
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando tasa de rendimiento: {str(e)}")
            raise
    
    def get_performance_rate(self, rate_id: int) -> Optional[PerformanceRate]:
        """Obtiene una tasa de rendimiento por ID"""
        return self.db.query(PerformanceRate).filter(PerformanceRate.id == rate_id).first()
    
    def find_performance_rate(self, code: str) -> Optional[PerformanceRate]:
        """Busca una tasa de rendimiento por código"""
        return self.db.query(PerformanceRate).filter(
            and_(
                PerformanceRate.code == code,
                PerformanceRate.is_active == True
            )
        ).first()
    
    def search_performance_rates(self, search_term: str, limit: int = 20) -> List[PerformanceRate]:
        """Busca tasas de rendimiento por término de búsqueda"""
        return self.db.query(PerformanceRate).filter(
            and_(
                PerformanceRate.is_active == True,
                or_(
                    PerformanceRate.code.ilike(f"%{search_term}%"),
                    PerformanceRate.description.ilike(f"%{search_term}%")
                )
            )
        ).limit(limit).all()
    
    def get_performance_rates_by_category(self, category: str) -> List[PerformanceRate]:
        """Obtiene todas las tasas de rendimiento de una categoría"""
        return self.db.query(PerformanceRate).filter(
            and_(
                PerformanceRate.is_active == True,
                or_(
                    PerformanceRate.description.ilike(f"%{category}%"),
                    PerformanceRate.code.ilike(f"%{category}%")
                )
            )
        ).all()
    
    def update_performance_rate(self, rate_id: int, updates: Dict[str, Any]) -> Optional[PerformanceRate]:
        """Actualiza una tasa de rendimiento"""
        try:
            rate = self.get_performance_rate(rate_id)
            if not rate:
                return None
            
            for key, value in updates.items():
                if hasattr(rate, key):
                    setattr(rate, key, value)
            
            self.db.commit()
            self.db.refresh(rate)
            logger.info(f"Tasa de rendimiento actualizada: {rate.code}")
            return rate
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando tasa de rendimiento: {str(e)}")
            raise
    
    def calculate_performance_adjustment(self, base_rate: Decimal, conditions: Dict[str, Any]) -> Decimal:
        """
        Calcula el ajuste de rendimiento basado en condiciones del trabajo
        
        Args:
            base_rate: Tasa base de rendimiento
            conditions: Condiciones del trabajo (clima, acceso, altura, etc.)
            
        Returns:
            Factor de ajuste de rendimiento
        """
        adjustment_factor = Decimal('1.00')
        
        # Factores de ajuste por condiciones
        condition_factors = {
            'weather_bad': Decimal('0.85'),      # Clima adverso
            'weather_extreme': Decimal('0.70'),  # Clima extremo
            'access_difficult': Decimal('0.90'), # Acceso difícil
            'height_high': Decimal('0.85'),      # Trabajo en altura
            'underground': Decimal('0.80'),      # Trabajo subterráneo
            'congested_area': Decimal('0.90'),   # Área congestionada
            'night_work': Decimal('0.85'),       # Trabajo nocturno
            'overtime': Decimal('0.90'),         # Horas extra
            'complex_work': Decimal('0.85'),     # Trabajo complejo
            'new_crew': Decimal('0.80'),         # Cuadrilla nueva
            'experienced_crew': Decimal('1.10'), # Cuadrilla experimentada
            'optimal_conditions': Decimal('1.15') # Condiciones óptimas
        }
        
        # Aplicar factores de condición
        for condition, factor in condition_factors.items():
            if conditions.get(condition, False):
                adjustment_factor *= factor
        
        # Limitar el ajuste máximo
        adjustment_factor = max(Decimal('0.50'), min(Decimal('1.50'), adjustment_factor))
        
        return base_rate * adjustment_factor
    
    def estimate_project_duration(self, items: List[Dict[str, Any]], 
                                crew_size: int = 8) -> Dict[str, Any]:
        """
        Estima la duración del proyecto basada en rendimientos
        
        Args:
            items: Lista de items del presupuesto
            crew_size: Tamaño promedio de cuadrilla
            
        Returns:
            Estimación de duración y recursos necesarios
        """
        
        # Tasas de rendimiento estándar por tipo de trabajo
        productivity_rates = {
            'demolition_concrete': {'rate': 3.0, 'unit': 'm3/day', 'crew': 6},      # m3 por día
            'demolition_reinforced': {'rate': 2.0, 'unit': 'm3/day', 'crew': 8},
            'excavation_manual': {'rate': 6.0, 'unit': 'm3/day', 'crew': 4},
            'excavation_mechanical': {'rate': 50.0, 'unit': 'm3/day', 'crew': 2},
            'concrete_foundation': {'rate': 15.0, 'unit': 'm3/day', 'crew': 8},
            'concrete_columns': {'rate': 8.0, 'unit': 'm3/day', 'crew': 10},
            'concrete_slabs': {'rate': 20.0, 'unit': 'm3/day', 'crew': 12},
            'reinforcement_steel': {'rate': 800.0, 'unit': 'kg/day', 'crew': 6},
            'formwork': {'rate': 60.0, 'unit': 'm2/day', 'crew': 8},
            'masonry': {'rate': 15.0, 'unit': 'm2/day', 'crew': 4},
            'plastering': {'rate': 80.0, 'unit': 'm2/day', 'crew': 3},
            'painting': {'rate': 200.0, 'unit': 'm2/day', 'crew': 4},
            'flooring': {'rate': 40.0, 'unit': 'm2/day', 'crew': 6},
            'roofing': {'rate': 100.0, 'unit': 'm2/day', 'crew': 8},
            'electrical_installation': {'rate': 200.0, 'unit': 'm2/day', 'crew': 3},
            'plumbing_installation': {'rate': 150.0, 'unit': 'm2/day', 'crew': 4},
            'finishing_works': {'rate': 100.0, 'unit': 'm2/day', 'crew': 5}
        }
        
        total_duration = Decimal('0.00')
        work_breakdown = {}
        
        for item in items:
            description = item.get('description', '').lower()
            quantity = Decimal(str(item.get('quantity', 0)))
            unit = item.get('unit', '').lower()
            
            # Identificar tipo de trabajo
            work_type = self._identify_work_type(description, unit)
            
            if work_type and work_type in productivity_rates:
                rate_data = productivity_rates[work_type]
                
                # Calcular duración en días
                if unit in ['m2', 'm3', 'kg']:
                    duration_days = quantity / Decimal(str(rate_data['rate']))
                    
                    # Ajustar por tamaño de cuadrilla
                    crew_adjustment = Decimal(str(crew_size)) / Decimal(str(rate_data['crew']))
                    duration_days = duration_days / crew_adjustment
                    
                    if work_type not in work_breakdown:
                        work_breakdown[work_type] = {
                            'description': self._get_work_description(work_type),
                            'total_quantity': Decimal('0.00'),
                            'unit': rate_data['unit'],
                            'duration_days': Decimal('0.00'),
                            'crew_size': rate_data['crew']
                        }
                    
                    work_breakdown[work_type]['total_quantity'] += quantity
                    work_breakdown[work_type]['duration_days'] += duration_days
                    total_duration = max(total_duration, duration_days)
        
        # Calcular duración total considerando trabajos en paralelo
        # Asumimos que trabajos diferentes pueden realizarse en paralelo
        # pero trabajos similares se suman
        
        parallel_factor = Decimal('0.70')  # 70% de eficiencia por trabajos en paralelo
        adjusted_duration = total_duration / parallel_factor
        
        # Agregar tiempo de imprevistos (10%)
        contingency_time = adjusted_duration * Decimal('0.10')
        final_duration = adjusted_duration + contingency_time
        
        return {
            'estimated_duration_days': final_duration,
            'work_breakdown': work_breakdown,
            'parallel_duration': adjusted_duration,
            'contingency_time': contingency_time,
            'recommendations': self._generate_duration_recommendations(work_breakdown, final_duration)
        }
    
    def _identify_work_type(self, description: str, unit: str) -> Optional[str]:
        """Identifica el tipo de trabajo basado en descripción y unidad"""
        
        # Palabras clave para identificación
        work_keywords = {
            'demolition_concrete': ['demolición', 'demolition', 'concreto', 'concrete'],
            'demolition_reinforced': ['demolición', 'demolition', 'reforzado', 'reinforced'],
            'excavation_manual': ['excavación', 'excavation', 'manual'],
            'excavation_mechanical': ['excavación', 'excavation', 'mecánica', 'mechanical'],
            'concrete_foundation': ['concreto', 'concrete', 'cimiento', 'foundation'],
            'concrete_columns': ['concreto', 'concrete', 'columna', 'column'],
            'concrete_slabs': ['concreto', 'concrete', 'losa', 'slab'],
            'reinforcement_steel': ['acero', 'steel', 'armadura', 'reinforcement'],
            'formwork': ['encofrado', 'formwork', 'cimbra'],
            'masonry': ['mampostería', 'masonry', 'muro', 'wall'],
            'plastering': ['plaster', 'plaste', 'repello', 'stucco'],
            'painting': ['pintura', 'painting', 'paint'],
            'flooring': ['piso', 'floor', 'flooring'],
            'roofing': ['techo', 'roof', 'cubierta'],
            'electrical_installation': ['eléctrica', 'electrical', 'electric'],
            'plumbing_installation': ['sanitaria', 'plumbing', 'plumber'],
            'finishing_works': ['acabado', 'finishing', 'acabados']
        }
        
        for work_type, keywords in work_keywords.items():
            if any(keyword in description for keyword in keywords):
                return work_type
        
        return None
    
    def _get_work_description(self, work_type: str) -> str:
        """Obtiene la descripción en español del tipo de trabajo"""
        descriptions = {
            'demolition_concrete': 'Demolición de concreto simple',
            'demolition_reinforced': 'Demolición de concreto reforzado',
            'excavation_manual': 'Excavación manual',
            'excavation_mechanical': 'Excavación mecánica',
            'concrete_foundation': 'Concreto en cimientos',
            'concrete_columns': 'Concreto en columnas',
            'concrete_slabs': 'Concreto en losas',
            'reinforcement_steel': 'Acero de refuerzo',
            'formwork': 'Encofrados y cimbras',
            'masonry': 'Mampostería',
            'plastering': 'Plastería y repello',
            'painting': 'Pintura',
            'flooring': 'Pisos y acabados de piso',
            'roofing': 'Techos y cubiertas',
            'electrical_installation': 'Instalación eléctrica',
            'plumbing_installation': 'Instalación sanitaria',
            'finishing_works': 'Acabados generales'
        }
        
        return descriptions.get(work_type, work_type.replace('_', ' ').title())
    
    def _generate_duration_recommendations(self, work_breakdown: Dict[str, Any], 
                                         total_duration: Decimal) -> List[str]:
        """Genera recomendaciones para la duración del proyecto"""
        recommendations = []
        
        if total_duration > 180:  # Más de 6 meses
            recommendations.append("Considerar división del proyecto en fases")
            recommendations.append("Planificar hitos intermedios de entrega")
        
        if total_duration > 365:  # Más de un año
            recommendations.append("Evaluar impacto de condiciones climáticas estacionales")
            recommendations.append("Considerar ajustes por inflación en costos")
        
        # Identificar trabajos críticos
        critical_works = [
            work for work, data in work_breakdown.items()
            if data['duration_days'] > total_duration * Decimal('0.3')
        ]
        
        if critical_works:
            recommendations.append(f"Trabajos críticos identificados: {', '.join(critical_works)}")
            recommendations.append("Considerar aceleración de trabajos críticos")
        
        # Recomendaciones por tipo de trabajo
        if any('concreto' in work.lower() for work in work_breakdown.keys()):
            recommendations.append("Planificar curado de concreto en programa")
        
        if any('pintura' in work.lower() for work in work_breakdown.keys()):
            recommendations.append("Considerar condiciones climáticas para pintura")
        
        return recommendations
    
    def get_performance_benchmarks(self) -> Dict[str, Any]:
        """Obtiene benchmarks de rendimiento para comparación"""
        
        # Benchmarks de la industria de construcción
        benchmarks = {
            'concrete_placement': {
                'excellent': 25,    # m3/día
                'good': 20,
                'average': 15,
                'poor': 10,
                'unit': 'm3/day'
            },
            'rebar_installation': {
                'excellent': 1000,  # kg/día
                'good': 800,
                'average': 600,
                'poor': 400,
                'unit': 'kg/day'
            },
            'formwork': {
                'excellent': 100,   # m2/día
                'good': 80,
                'average': 60,
                'poor': 40,
                'unit': 'm2/day'
            },
            'masonry': {
                'excellent': 20,    # m2/día
                'good': 15,
                'average': 12,
                'poor': 8,
                'unit': 'm2/day'
            },
            'excavation': {
                'excellent': 80,    # m3/día
                'good': 60,
                'average': 40,
                'poor': 20,
                'unit': 'm3/day'
            }
        }
        
        return {
            'benchmarks': benchmarks,
            'comparison_notes': [
                "Los benchmarks son aproximados y pueden variar según condiciones locales",
                "Considerar ajustes por tipo de proyecto y complejidad",
                "Los valores son para cuadrillas estándar de 6-8 trabajadores",
                "Clima y condiciones de acceso pueden afectar significativamente"
            ]
        }
    
    def analyze_performance_gaps(self, planned_items: List[Dict[str, Any]], 
                               actual_progress: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza brechas entre rendimiento planeado y real"""
        
        gaps_analysis = {}
        total_planned_days = Decimal('0.00')
        total_actual_days = Decimal('0.00')
        
        for item in planned_items:
            description = item.get('description', '')
            planned_days = item.get('estimated_days', 0)
            
            # Buscar progreso real correspondiente
            actual_days = actual_progress.get(description, planned_days)
            
            gap_percentage = ((actual_days - planned_days) / planned_days * 100) if planned_days > 0 else 0
            
            gaps_analysis[description] = {
                'planned_days': planned_days,
                'actual_days': actual_days,
                'gap_days': actual_days - planned_days,
                'gap_percentage': gap_percentage,
                'performance': 'excellent' if gap_percentage <= -10 else \
                             'good' if gap_percentage <= 0 else \
                             'fair' if gap_percentage <= 20 else 'poor'
            }
            
            total_planned_days += planned_days
            total_actual_days += actual_days
        
        # Análisis general
        overall_gap = total_actual_days - total_planned_days
        overall_gap_percentage = (overall_gap / total_planned_days * 100) if total_planned_days > 0 else 0
        
        return {
            'gaps_analysis': gaps_analysis,
            'overall_metrics': {
                'total_planned_days': total_planned_days,
                'total_actual_days': total_actual_days,
                'overall_gap_days': overall_gap,
                'overall_gap_percentage': overall_gap_percentage
            },
            'recommendations': self._generate_performance_recommendations(gaps_analysis)
        }
    
    def _generate_performance_recommendations(self, gaps_analysis: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en análisis de brechas"""
        recommendations = []
        
        poor_performances = [
            desc for desc, data in gaps_analysis.items()
            if data['performance'] == 'poor'
        ]
        
        excellent_performances = [
            desc for desc, data in gaps_analysis.items()
            if data['performance'] == 'excellent'
        ]
        
        if len(poor_performances) > len(gaps_analysis) * 0.3:
            recommendations.append("Revisar planificación general del proyecto")
            recommendations.append("Considerar capacitación adicional del personal")
        
        if len(excellent_performances) > 0:
            recommendations.append("Identificar y replicar prácticas exitosas")
            recommendations.append(f"Actividades con excelente rendimiento: {len(excellent_performances)}")
        
        for description, data in gaps_analysis.items():
            if data['gap_percentage'] > 50:
                recommendations.append(f"Investigar causas de retraso en: {description[:50]}...")
        
        return recommendations