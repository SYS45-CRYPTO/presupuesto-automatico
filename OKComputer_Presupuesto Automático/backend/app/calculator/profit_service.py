from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

from ..models.models import Project, Company, CostSetting

logger = logging.getLogger(__name__)

class ProfitService:
    """Gestiona cálculos de beneficios y márgenes de ganancia"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def calculate_project_profit(self, project_id: int, cost_breakdown: Dict[str, Decimal]) -> Dict[str, Any]:
        """
        Calcula el beneficio del proyecto basado en costos y configuración
        
        Args:
            project_id: ID del proyecto
            cost_breakdown: Desglose de costos del proyecto
            
        Returns:
            Dict con cálculo de beneficios y análisis
        """
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Proyecto no encontrado: {project_id}")
            
            company = project.company
            
            # Calcular costo directo total
            direct_cost = (
                cost_breakdown.get('labor_cost', Decimal('0.00')) +
                cost_breakdown.get('material_cost', Decimal('0.00')) +
                cost_breakdown.get('equipment_cost', Decimal('0.00'))
            )
            
            # Calcular costos indirectos
            indirect_costs = self._calculate_indirect_costs(direct_cost, project.company_id)
            
            # Calcular costo total antes de beneficio
            total_cost = direct_cost + sum(indirect_costs.values())
            
            # Obtener margen de beneficio configurado
            profit_margin = project.profit_margin or company.default_profit_margin
            
            # Calcular beneficio
            profit_amount = total_cost * (profit_margin / 100)
            
            # Precio final de venta
            final_price = total_cost + profit_amount
            
            # Análisis de rentabilidad
            profitability_analysis = self._analyze_profitability(
                total_cost, profit_amount, profit_margin, project
            )
            
            return {
                'project_id': project_id,
                'cost_components': {
                    'direct_cost': direct_cost,
                    'indirect_costs': indirect_costs,
                    'total_cost': total_cost,
                    'profit_amount': profit_amount,
                    'final_price': final_price
                },
                'profitability': profitability_analysis,
                'recommendations': self._generate_profit_recommendations(
                    profit_margin, profitability_analysis, project
                )
            }
            
        except Exception as e:
            logger.error(f"Error calculando beneficio del proyecto: {str(e)}")
            raise
    
    def calculate_scenario_analysis(self, base_cost: Decimal, project_id: int) -> Dict[str, Any]:
        """
        Analiza diferentes escenarios de márgenes de beneficio
        
        Args:
            base_cost: Costo base del proyecto
            project_id: ID del proyecto
            
        Returns:
            Análisis de escenarios con diferentes márgenes
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Proyecto no encontrado: {project_id}")
        
        # Escenarios de margen de beneficio
        scenarios = [
            {'name': 'Conservador', 'margin': Decimal('10.00')},
            {'name': 'Estándar', 'margin': project.profit_margin or Decimal('15.00')},
            {'name': 'Agresivo', 'margin': Decimal('20.00')},
            {'name': 'Premium', 'margin': Decimal('25.00')}
        ]
        
        scenario_results = []
        
        for scenario in scenarios:
            margin = scenario['margin']
            profit_amount = base_cost * (margin / 100)
            final_price = base_cost + profit_amount
            
            # Análisis de riesgo para cada escenario
            risk_analysis = self._analyze_profit_risk(base_cost, margin, profit_amount)
            
            scenario_results.append({
                'scenario': scenario['name'],
                'margin_percent': margin,
                'profit_amount': profit_amount,
                'final_price': final_price,
                'risk_level': risk_analysis['risk_level'],
                'break_even_point': risk_analysis['break_even_point'],
                'recommendation': risk_analysis['recommendation']
            })
        
        return {
            'base_cost': base_cost,
            'scenarios': scenario_results,
            'optimal_scenario': self._find_optimal_scenario(scenario_results),
            'market_comparison': self._compare_with_market_rates(base_cost)
        }
    
    def optimize_profit_margin(self, project_id: int, target_profit: Decimal, 
                             constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimiza el margen de beneficio considerando restricciones
        
        Args:
            project_id: ID del proyecto
            target_profit: Beneficio objetivo
            constraints: Restricciones del proyecto (competencia, mercado, etc.)
            
        Returns:
            Optimización de margen y recomendaciones
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Proyecto no encontrado: {project_id}")
        
        # Obtener costos base del proyecto
        # Nota: En una implementación real, esto vendría del cálculo de presupuesto
        estimated_cost = constraints.get('estimated_cost', Decimal('100000.00'))
        
        # Factores de optimización
        optimization_factors = {
            'market_competition': constraints.get('market_competition', 'medium'),  # low, medium, high
            'project_complexity': constraints.get('project_complexity', 'medium'),
            'client_relationship': constraints.get('client_relationship', 'new'),  # new, established, strategic
            'project_duration': constraints.get('project_duration', 180),  # días
            'risk_level': constraints.get('risk_level', 'medium')  # low, medium, high
        }
        
        # Calcular margen óptimo
        optimal_margin = self._calculate_optimal_margin(
            estimated_cost, target_profit, optimization_factors
        )
        
        # Análisis de sensibilidad
        sensitivity_analysis = self._perform_sensitivity_analysis(
            estimated_cost, optimal_margin
        )
        
        return {
            'project_id': project_id,
            'target_profit': target_profit,
            'optimal_margin': optimal_margin,
            'optimal_profit': estimated_cost * (optimal_margin / 100),
            'final_price': estimated_cost * (1 + optimal_margin / 100),
            'optimization_factors': optimization_factors,
            'sensitivity_analysis': sensitivity_analysis,
            'risk_assessment': self._assess_profit_risk(optimal_margin, optimization_factors),
            'recommendations': self._generate_optimization_recommendations(
                optimal_margin, optimization_factors
            )
        }
    
    def _calculate_indirect_costs(self, direct_cost: Decimal, company_id: int) -> Dict[str, Decimal]:
        """Calcula costos indirectos del proyecto"""
        
        # Obtener configuración de costos indirectos
        cost_settings = self.db.query(CostSetting).filter(
            and_(
                CostSetting.company_id == company_id,
                CostSetting.is_active == True
            )
        ).all()
        
        indirect_costs = {}
        
        for setting in cost_settings:
            if setting.calculation_method == 'percentage':
                cost_amount = direct_cost * (Decimal(str(setting.percentage)) / 100)
            elif setting.calculation_method == 'fixed':
                cost_amount = Decimal(str(setting.fixed_amount))
            else:
                cost_amount = Decimal('0.00')
            
            indirect_costs[setting.setting_type] = cost_amount
        
        # Costos indirectos estándar si no hay configuración
        if not indirect_costs:
            indirect_costs = {
                'transport': direct_cost * Decimal('0.02'),
                'tools': direct_cost * Decimal('0.015'),
                'machinery': direct_cost * Decimal('0.025'),
                'overhead': direct_cost * Decimal('0.05')
            }
        
        return indirect_costs
    
    def _analyze_profitability(self, total_cost: Decimal, profit_amount: Decimal, 
                             profit_margin: Decimal, project: Project) -> Dict[str, Any]:
        """Analiza la rentabilidad del proyecto"""
        
        # Ratios de rentabilidad
        profit_ratio = profit_amount / total_cost if total_cost > 0 else 0
        
        # Análisis de punto de equilibrio
        break_even_point = total_cost / (1 - profit_margin / 100) if profit_margin > 0 else total_cost
        
        # Comparación con benchmarks de industria
        industry_benchmarks = {
            'residential': {'min_margin': 15, 'target_margin': 20, 'max_margin': 25},
            'commercial': {'min_margin': 12, 'target_margin': 18, 'max_margin': 22},
            'industrial': {'min_margin': 10, 'target_margin': 15, 'max_margin': 20},
            'infrastructure': {'min_margin': 8, 'target_margin': 12, 'max_margin': 18}
        }
        
        # Determinar tipo de proyecto (simplificado)
 project_type = 'residential'  # Por defecto
        
        benchmark = industry_benchmarks.get(project_type, industry_benchmarks['residential'])
        
        # Evaluar rentabilidad
        if profit_margin >= benchmark['target_margin']:
            profitability_rating = 'excellent'
        elif profit_margin >= benchmark['min_margin']:
            profitability_rating = 'good'
        elif profit_margin >= benchmark['min_margin'] - 5:
            profitability_rating = 'fair'
        else:
            profitability_rating = 'poor'
        
        # Análisis de riesgo
        risk_factors = {
            'low_profit_margin': profit_margin < benchmark['min_margin'],
            'high_cost_project': total_cost > 1000000,  # Proyectos grandes
            'long_duration': False,  # Se determinaría con más información
            'complex_project': False  # Se determinaría con más información
        }
        
        risk_score = sum(1 for risk in risk_factors.values() if risk)
        
        return {
            'profit_ratio': profit_ratio,
            'break_even_point': break_even_point,
            'profitability_rating': profitability_rating,
            'industry_benchmark': benchmark,
            'risk_factors': risk_factors,
            'risk_score': risk_score,
            'risk_level': 'low' if risk_score == 0 else 'medium' if risk_score <= 2 else 'high'
        }
    
    def _analyze_profit_risk(self, base_cost: Decimal, margin: Decimal, profit_amount: Decimal) -> Dict[str, Any]:
        """Analiza el riesgo asociado con un margen de beneficio"""
        
        # Calcular punto de equilibrio
        break_even_point = base_cost / (1 - margin / 100) if margin > 0 else base_cost
        
        # Evaluar riesgo basado en margen
        if margin >= 20:
            risk_level = 'low'
            recommendation = "Margen saludable con buen buffer para imprevistos"
        elif margin >= 15:
            risk_level = 'medium'
            recommendation = "Margen aceptable, monitorear costos cuidadosamente"
        elif margin >= 10:
            risk_level = 'medium-high'
            recommendation = "Margen ajustado, requiere control estricto de costos"
        else:
            risk_level = 'high'
            recommendation = "Margen muy bajo, alto riesgo de pérdidas"
        
        return {
            'risk_level': risk_level,
            'break_even_point': break_even_point,
            'recommendation': recommendation
        }
    
    def _calculate_optimal_margin(self, estimated_cost: Decimal, target_profit: Decimal, 
                                factors: Dict[str, Any]) -> Decimal:
        """Calcula el margen de beneficio óptimo"""
        
        # Margen base para alcanzar el beneficio objetivo
        base_margin = (target_profit / estimated_cost) * 100
        
        # Factores de ajuste
        adjustment_factors = {
            'market_competition': {
                'low': 1.10,    # Puede aumentar margen
                'medium': 1.00, # Margen estándar
                'high': 0.85    # Debe reducir margen por competencia
            },
            'project_complexity': {
                'low': 0.90,    # Menor complejidad, menor margen
                'medium': 1.00, # Complejidad estándar
                'high': 1.15    # Mayor complejidad, mayor margen justificado
            },
            'client_relationship': {
                'new': 1.00,        # Cliente nuevo, margen estándar
                'established': 0.95, # Cliente fiel, ligero descuento
                'strategic': 0.90    # Cliente estratégico, margen reducido
            },
            'risk_level': {
                'low': 0.95,    # Bajo riesgo, margen reducido
                'medium': 1.00, # Riesgo estándar
                'high': 1.10    # Alto riesgo, margen aumentado
            }
        }
        
        # Aplicar ajustes
        adjusted_margin = base_margin
        
        for factor_name, factor_value in factors.items():
            if factor_name in adjustment_factors and factor_value in adjustment_factors[factor_name]:
                adjusted_margin *= adjustment_factors[factor_name][factor_value]
        
        # Limitar margen mínimo y máximo
        min_margin = Decimal('5.00')   # 5% mínimo
        max_margin = Decimal('35.00')  # 35% máximo
        
        optimal_margin = max(min_margin, min(max_margin, Decimal(str(adjusted_margin))))
        
        return optimal_margin
    
    def _perform_sensitivity_analysis(self, base_cost: Decimal, optimal_margin: Decimal) -> Dict[str, Any]:
        """Realiza análisis de sensibilidad del margen de beneficio"""
        
        # Escenarios de variación de costos
        cost_variations = [-20, -10, -5, 0, 5, 10, 20]  # Porcentajes
        
        sensitivity_results = []
        
        for variation in cost_variations:
            varied_cost = base_cost * (1 + variation / 100)
            profit_at_margin = varied_cost * (optimal_margin / 100)
            final_price = varied_cost + profit_at_margin
            
            # Calcular margen real si se mantiene el precio final
            actual_margin = (profit_at_margin / varied_cost) * 100 if varied_cost > 0 else 0
            
            sensitivity_results.append({
                'cost_variation': variation,
                'varied_cost': varied_cost,
                'profit_amount': profit_at_margin,
                'final_price': final_price,
                'actual_margin': actual_margin,
                'margin_impact': actual_margin - optimal_margin
            })
        
        return {
            'base_cost': base_cost,
            'optimal_margin': optimal_margin,
            'sensitivity_results': sensitivity_results,
            'break_even_variation': self._calculate_break_even_point(sensitivity_results)
        }
    
    def _calculate_break_even_point(self, sensitivity_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula el punto de equilibrio basado en análisis de sensibilidad"""
        
        # Encontrar el punto donde el margen se vuelve crítico (< 5%)
        critical_points = [result for result in sensitivity_results if result['actual_margin'] < 5]
        
        if critical_points:
            worst_case = min(critical_points, key=lambda x: x['actual_margin'])
            return {
                'break_even_reached': True,
                'critical_variation': worst_case['cost_variation'],
                'critical_margin': worst_case['actual_margin'],
                'safety_buffer': abs(worst_case['cost_variation'])
            }
        else:
            return {
                'break_even_reached': False,
                'safety_buffer': 20  # Asumir buffer de seguridad de 20%
            }
    
    def _assess_profit_risk(self, margin: Decimal, factors: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa el riesgo del margen de beneficio"""
        
        # Calcular score de riesgo
        risk_score = 0
        
        # Riesgo por margen bajo
        if margin < 10:
            risk_score += 3
        elif margin < 15:
            risk_score += 2
        elif margin < 20:
            risk_score += 1
        
        # Riesgo por competencia
        if factors.get('market_competition') == 'high':
            risk_score += 2
        elif factors.get('market_competition') == 'medium':
            risk_score += 1
        
        # Riesgo por alta complejidad
        if factors.get('project_complexity') == 'high':
            risk_score += 2
        elif factors.get('project_complexity') == 'medium':
            risk_score += 1
        
        # Riesgo por alto nivel de riesgo
        if factors.get('risk_level') == 'high':
            risk_score += 2
        elif factors.get('risk_level') == 'medium':
            risk_score += 1
        
        # Determinar nivel de riesgo
        if risk_score >= 7:
            risk_level = 'very_high'
        elif risk_score >= 5:
            risk_level = 'high'
        elif risk_score >= 3:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': [
                f"Margen: {margin:.1f}%",
                f"Competencia: {factors.get('market_competition', 'unknown')}",
                f"Complejidad: {factors.get('project_complexity', 'unknown')}",
                f"Nivel de riesgo: {factors.get('risk_level', 'unknown')}"
            ]
        }
    
    def _compare_with_market_rates(self, base_cost: Decimal) -> Dict[str, Any]:
        """Compara con tasas de mercado"""
        
        # Tasas típicas de mercado por tipo de proyecto (valores de ejemplo)
        market_rates = {
            'residential_construction': {
                'cost_range': (800, 1200),  # $/m2
                'typical_margin': (15, 25)
            },
            'commercial_construction': {
                'cost_range': (1000, 1500),  # $/m2
                'typical_margin': (12, 20)
            },
            'industrial_construction': {
                'cost_range': (600, 1000),   # $/m2
                'typical_margin': (10, 18)
            },
            'infrastructure': {
                'cost_range': (500, 800),    # $/m2
                'typical_margin': (8, 15)
            }
        }
        
        # Análisis simplificado - usar rango promedio
        avg_low = sum(rate['cost_range'][0] for rate in market_rates.values()) / len(market_rates)
        avg_high = sum(rate['cost_range'][1] for rate in market_rates.values()) / len(market_rates)
        
        avg_margin_low = sum(rate['typical_margin'][0] for rate in market_rates.values()) / len(market_rates)
        avg_margin_high = sum(rate['typical_margin'][1] for rate in market_rates.values()) / len(market_rates)
        
        return {
            'market_cost_range': (avg_low, avg_high),
            'market_margin_range': (avg_margin_low, avg_margin_high),
            'comparison_note': 'Valores promedio del mercado, pueden variar según ubicación y condiciones'
        }
    
    def _find_optimal_scenario(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Encuentra el escenario óptimo basado en balance riesgo-beneficio"""
        
        # Puntuar cada escenario
        scored_scenarios = []
        
        for scenario in scenarios:
            # Puntuación por margen (beneficio)
            margin_score = min(10, scenario['margin'] / 2)  # Máximo 10 puntos
            
            # Puntuación por nivel de riesgo
            risk_scores = {'low': 10, 'medium': 7, 'medium-high': 4, 'high': 2}
            risk_score = risk_scores.get(scenario['risk_level'], 5)
            
            # Puntuación total (balance entre beneficio y riesgo)
            total_score = (margin_score * 0.6) + (risk_score * 0.4)
            
            scored_scenarios.append({
                **scenario,
                'score': total_score
            })
        
        # Encontrar el escenario con mejor puntuación
        optimal = max(scored_scenarios, key=lambda x: x['score'])
        
        return {
            'scenario': optimal['scenario'],
            'margin': optimal['margin'],
            'score': optimal['score'],
            'reasoning': f"Mejor balance entre margen ({optimal['margin']:.1f}%) y riesgo ({optimal['risk_level']})"
        }
    
    def _generate_profit_recommendations(self, margin: Decimal, analysis: Dict[str, Any], 
                                       project: Project) -> List[str]:
        """Genera recomendaciones para el margen de beneficio"""
        
        recommendations = []
        
        if analysis['profitability_rating'] == 'poor':
            recommendations.append("Revisar estrategia de precios - margen muy bajo")
            recommendations.append("Identificar oportunidades de reducción de costos")
            recommendations.append("Considerar si el proyecto es viable con este margen")
        
        elif analysis['profitability_rating'] == 'fair':
            recommendations.append("Margen aceptable pero con riesgo")
            recommendations.append("Implementar control estricto de costos")
            recommendations.append("Monitorear imprevistos de cerca")
        
        elif analysis['profitability_rating'] == 'excellent':
            recommendations.append("Margen saludable identificado")
            recommendations.append("Considerar reinversión de beneficios en calidad")
        
        if analysis['risk_level'] == 'high':
            recommendations.append("Alto riesgo detectado - considerar seguros adicionales")
            recommendations.append("Preparar plan de contingencia")
        
        # Recomendaciones específicas por tipo de proyecto
        if hasattr(project, 'client_name') and project.client_name:
            recommendations.append(f"Considerar relación a largo plazo con {project.client_name}")
        
        return recommendations
    
    def _generate_optimization_recommendations(self, optimal_margin: Decimal, 
                                             factors: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones para la optimización"""
        
        recommendations = []
        
        recommendations.append(f"Margen óptimo sugerido: {optimal_margin:.1f}%")
        
        if factors.get('market_competition') == 'high':
            recommendations.append("Mercado competitivo - enfocarse en eficiencia operativa")
        
        if factors.get('project_complexity') == 'high':
            recommendations.append("Alta complejidad justifica margen superior")
        
        if factors.get('client_relationship') == 'strategic':
            recommendations.append("Cliente estratégico - margen reducido por valor a largo plazo")
        
        if factors.get('risk_level') == 'high':
            recommendations.append("Alto riesgo - considerar seguros y contingencias")
        
        return recommendations