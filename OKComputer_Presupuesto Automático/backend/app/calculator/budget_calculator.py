from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import logging
from datetime import datetime

from ..models.schemas import CalculationRequest, CalculationResult
from .cost_calculator import CostCalculator
from .profit_service import ProfitService

logger = logging.getLogger(__name__)

class BudgetCalculator:
    """Calculadora principal de presupuestos con rendimientos y beneficios"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.cost_calculator = CostCalculator(db_session)
        self.profit_service = ProfitService(db_session)
    
    def calculate_budget(self, request: CalculationRequest) -> CalculationResult:
        """
        Calcula el presupuesto completo con rendimientos y beneficios
        
        Args:
            request: Objeto con parámetros de cálculo
            
        Returns:
            Resultado del cálculo con desglose completo
        """
        try:
            logger.info(f"Iniciando cálculo de presupuesto ID: {request.budget_id}")
            
            # Obtener datos del presupuesto
            budget = self._get_budget(request.budget_id)
            if not budget:
                raise ValueError(f"Presupuesto no encontrado: {request.budget_id}")
            
            items = self._get_budget_items(request.budget_id)
            if not items:
                logger.warning(f"No se encontraron items para el presupuesto {request.budget_id}")
            
            # Calcular cada item
            calculated_items = []
            subtotal = Decimal('0.00')
            total_labor_cost = Decimal('0.00')
            total_material_cost = Decimal('0.00')
            total_equipment_cost = Decimal('0.00')
            total_indirect_cost = Decimal('0.00')
            
            for item in items:
                calculated_item = self._calculate_item(
                    item, 
                    request.performance_adjustments or {},
                    budget.project.profit_margin if not request.profit_margin else request.profit_margin
                )
                calculated_items.append(calculated_item)
                
                # Acumular totales
                subtotal += calculated_item['total_price']
                total_labor_cost += calculated_item['labor_cost']
                total_material_cost += calculated_item['material_cost']
                total_equipment_cost += calculated_item['equipment_cost']
                total_indirect_cost += calculated_item['indirect_cost']
            
            # Calcular beneficios y costos indirectos adicionales
            profit_margin = request.profit_margin or budget.project.profit_margin
            profit_amount = subtotal * (profit_margin / 100)
            
            # Calcular costos indirectos adicionales
            additional_indirect_costs = self._calculate_additional_indirect_costs(
                subtotal, budget.project.company_id
            )
            
            # Calcular total final
            final_amount = subtotal + profit_amount + additional_indirect_costs
            
            # Construir resultado
            result = CalculationResult(
                budget_id=request.budget_id,
                subtotal=subtotal,
                profit_amount=profit_amount,
                total_amount=final_amount,
                cost_breakdown={
                    'labor_cost': total_labor_cost,
                    'material_cost': total_material_cost,
                    'equipment_cost': total_equipment_cost,
                    'indirect_cost': total_indirect_cost + additional_indirect_costs,
                    'profit_amount': profit_amount,
                    'profit_margin': profit_margin
                },
                items_calculated=len(calculated_items)
            )
            
            # Actualizar presupuesto con los nuevos valores
            self._update_budget_totals(budget, final_amount, profit_amount)
            
            logger.info(f"Cálculo completado: {len(calculated_items)} items, total: ${final_amount}")
            return result
            
        except Exception as e:
            logger.error(f"Error en cálculo de presupuesto: {str(e)}")
            raise
    
    def calculate_simulation(self, budget_id: int, profit_margin: Optional[Decimal] = None,
                           performance_adjustments: Optional[Dict[int, Decimal]] = None) -> CalculationResult:
        """
        Realiza una simulación de cálculo sin guardar cambios
        """
        request = CalculationRequest(
            budget_id=budget_id,
            profit_margin=profit_margin,
            performance_adjustments=performance_adjustments
        )
        
        # Realizar cálculo sin actualizar la base de datos
        return self._calculate_simulation_only(request)
    
    def _calculate_item(self, item, performance_adjustments: Dict[int, Decimal], 
                       profit_margin: Decimal) -> Dict[str, Any]:
        """Calcula los costos de un item individual"""
        
        # Aplicar ajustes de rendimiento si existen
        performance_rate = item.performance_rate
        if item.id in performance_adjustments:
            performance_rate = performance_adjustments[item.id]
        
        # Calcular cantidad ajustada por rendimiento
        adjusted_quantity = item.quantity * performance_rate
        
        # Calcular costos base
        base_cost = item.unit_price * adjusted_quantity
        
        # Desglosar costos por categoría
        labor_cost = base_cost * (item.labor_percentage / 100)
        material_cost = base_cost * (item.material_percentage / 100)
        equipment_cost = base_cost * (item.equipment_percentage / 100)
        
        # Calcular costos indirectos (transporte, herramientas, etc.)
        indirect_cost = self._calculate_indirect_costs(base_cost)
        
        # Calcular precio total con costos indirectos
        total_cost = labor_cost + material_cost + equipment_cost + indirect_cost
        
        # Aplicar margen de beneficio
        profit_amount = total_cost * (profit_margin / 100)
        total_price = total_cost + profit_amount
        
        return {
            'id': item.id,
            'code': item.code,
            'description': item.description,
            'unit': item.unit,
            'quantity': item.quantity,
            'adjusted_quantity': adjusted_quantity,
            'unit_price': item.unit_price,
            'performance_rate': performance_rate,
            'labor_cost': labor_cost,
            'material_cost': material_cost,
            'equipment_cost': equipment_cost,
            'indirect_cost': indirect_cost,
            'profit_margin': profit_margin,
            'profit_amount': profit_amount,
            'total_price': total_price
        }
    
    def _calculate_indirect_costs(self, base_cost: Decimal) -> Decimal:
        """Calcula los costos indirectos para un costo base"""
        
        # Costos indirectos típicos en construcción
        indirect_costs = {
            'transport': Decimal('0.02'),  # 2% de transporte
            'tools': Decimal('0.015'),     # 1.5% de herramientas
            'equipment': Decimal('0.025'), # 2.5% de maquinaria
            'overhead': Decimal('0.05')    # 5% de gastos generales
        }
        
        total_indirect = Decimal('0.00')
        for cost_type, percentage in indirect_costs.items():
            total_indirect += base_cost * percentage
        
        return total_indirect
    
    def _calculate_additional_indirect_costs(self, subtotal: Decimal, company_id: int) -> Decimal:
        """Calcula costos indirectos adicionales configurados por la empresa"""
        
        # Obtener configuración de costos indirectos de la empresa
        cost_settings = self._get_company_cost_settings(company_id)
        
        additional_costs = Decimal('0.00')
        for setting in cost_settings:
            if setting.calculation_method == 'percentage':
                additional_costs += subtotal * (Decimal(str(setting.percentage)) / 100)
            elif setting.calculation_method == 'fixed':
                additional_costs += Decimal(str(setting.fixed_amount))
        
        return additional_costs
    
    def calculate_chapter_totals(self, budget_id: int) -> Dict[str, Decimal]:
        """Calcula los totales por capítulo del presupuesto"""
        
        items = self._get_budget_items(budget_id)
        
        # Agrupar por capítulo
        chapters = {}
        for item in items:
            chapter = item.chapter or 'Sin Capítulo'
            if chapter not in chapters:
                chapters[chapter] = {
                    'items': [],
                    'subtotal': Decimal('0.00')
                }
            
            chapters[chapter]['items'].append(item)
            chapters[chapter]['subtotal'] += item.total_price
        
        return chapters
    
    def calculate_material_list(self, budget_id: int) -> Dict[str, Any]:
        """Calcula la lista de materiales necesarios para el presupuesto"""
        
        items = self._get_budget_items(budget_id)
        material_list = {}
        
        for item in items:
            # Calcular cantidad de materiales basada en el porcentaje de material
            material_cost = item.total_price * (item.material_percentage / 100)
            
            # Agrupar por tipo de material (usando la descripción como proxy)
            material_key = f"{item.description} ({item.unit})"
            
            if material_key not in material_list:
                material_list[material_key] = {
                    'quantity': Decimal('0.00'),
                    'unit': item.unit,
                    'estimated_cost': Decimal('0.00'),
                    'items': []
                }
            
            material_list[material_key]['quantity'] += item.quantity
            material_list[material_key]['estimated_cost'] += material_cost
            material_list[material_key]['items'].append({
                'code': item.code,
                'description': item.description,
                'quantity': item.quantity,
                'unit_cost': material_cost / item.quantity if item.quantity > 0 else 0
            })
        
        # Calcular totales
        total_material_cost = sum(material['estimated_cost'] for material in material_list.values())
        
        return {
            'materials': material_list,
            'total_cost': total_material_cost,
            'total_items': len(material_list)
        }
    
    def calculate_labor_hours(self, budget_id: int) -> Dict[str, Any]:
        """Calcula las horas de trabajo necesarias"""
        
        items = self._get_budget_items(budget_id)
        
        total_labor_cost = Decimal('0.00')
        labor_by_category = {}
        
        for item in items:
            # Calcular costo de mano de obra
            labor_cost = item.total_price * (item.labor_percentage / 100)
            total_labor_cost += labor_cost
            
            # Agrupar por categoría
            category = item.chapter or 'General'
            if category not in labor_by_category:
                labor_by_category[category] = {
                    'labor_cost': Decimal('0.00'),
                    'estimated_hours': Decimal('0.00')
                }
            
            labor_by_category[category]['labor_cost'] += labor_cost
            
            # Estimar horas basado en un costo por hora promedio
            # Asumimos $20/hora como promedio (ajustable según región)
            avg_hourly_rate = Decimal('20.00')
            estimated_hours = labor_cost / avg_hourly_rate
            labor_by_category[category]['estimated_hours'] += estimated_hours
        
        # Calcular horas totales
        avg_hourly_rate = Decimal('20.00')
        total_hours = total_labor_cost / avg_hourly_rate
        
        return {
            'total_labor_cost': total_labor_cost,
            'total_estimated_hours': total_hours,
            'categories': labor_by_category,
            'average_hourly_rate': avg_hourly_rate
        }
    
    def _get_budget(self, budget_id: int):
        """Obtiene un presupuesto por ID"""
        from ..models.models import Budget
        return self.db.query(Budget).filter(Budget.id == budget_id).first()
    
    def _get_budget_items(self, budget_id: int):
        """Obtiene los items de un presupuesto"""
        from ..models.models import BudgetItem
        return self.db.query(BudgetItem).filter(BudgetItem.budget_id == budget_id).all()
    
    def _get_company_cost_settings(self, company_id: int):
        """Obtiene la configuración de costos de una empresa"""
        from ..models.models import CostSetting
        return self.db.query(CostSetting).filter(
            CostSetting.company_id == company_id,
            CostSetting.is_active == True
        ).all()
    
    def _update_budget_totals(self, budget, final_amount: Decimal, profit_amount: Decimal):
        """Actualiza los totales del presupuesto"""
        budget.total_amount = final_amount - profit_amount  # Subtotal sin beneficio
        budget.profit_amount = profit_amount
        budget.final_amount = final_amount
        budget.updated_at = datetime.utcnow()
        
        self.db.commit()
    
    def _calculate_simulation_only(self, request: CalculationRequest) -> CalculationResult:
        """Realiza cálculo de simulación sin guardar cambios"""
        # Versión simplificada para simulaciones rápidas
        from ..models.models import Budget, BudgetItem
        
        budget = self.db.query(Budget).filter(Budget.id == request.budget_id).first()
        if not budget:
            raise ValueError(f"Presupuesto no encontrado: {request.budget_id}")
        
        items = self.db.query(BudgetItem).filter(BudgetItem.budget_id == request.budget_id).all()
        
        subtotal = Decimal('0.00')
        for item in items:
            performance_rate = item.performance_rate
            if item.id in (request.performance_adjustments or {}):
                performance_rate = request.performance_adjustments[item.id]
            
            adjusted_quantity = item.quantity * performance_rate
            item_total = item.unit_price * adjusted_quantity
            subtotal += item_total
        
        profit_margin = request.profit_margin or budget.project.profit_margin
        profit_amount = subtotal * (profit_margin / 100)
        final_amount = subtotal + profit_amount
        
        return CalculationResult(
            budget_id=request.budget_id,
            subtotal=subtotal,
            profit_amount=profit_amount,
            total_amount=final_amount,
            cost_breakdown={
                'subtotal': subtotal,
                'profit_amount': profit_amount,
                'profit_margin': profit_margin
            },
            items_calculated=len(items)
        )
    
    def validate_budget(self, budget_id: int) -> Dict[str, Any]:
        """Valida la integridad de un presupuesto"""
        
        items = self._get_budget_items(budget_id)
        
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'stats': {
                'total_items': len(items),
                'items_with_zero_price': 0,
                'items_with_zero_quantity': 0,
                'total_estimated_value': Decimal('0.00')
            }
        }
        
        for item in items:
            # Validar precio unitario
            if item.unit_price <= 0:
                validation_results['errors'].append(f"Item {item.code}: precio unitario inválido")
                validation_results['stats']['items_with_zero_price'] += 1
                validation_results['is_valid'] = False
            
            # Validar cantidad
            if item.quantity <= 0:
                validation_results['warnings'].append(f"Item {item.code}: cantidad cero o negativa")
                validation_results['stats']['items_with_zero_quantity'] += 1
            
            # Validar rendimiento
            if item.performance_rate <= 0 or item.performance_rate > 10:
                validation_results['warnings'].append(f"Item {item.code}: rendimiento fuera de rango normal")
            
            # Acumular valor estimado
            validation_results['stats']['total_estimated_value'] += (item.unit_price * item.quantity)
        
        # Validaciones globales
        if len(items) == 0:
            validation_results['errors'].append("El presupuesto no contiene items")
            validation_results['is_valid'] = False
        
        if validation_results['stats']['total_estimated_value'] <= 0:
            validation_results['errors'].append("El valor total del presupuesto es cero")
            validation_results['is_valid'] = False
        
        return validation_results