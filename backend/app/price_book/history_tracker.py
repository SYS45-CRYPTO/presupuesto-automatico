from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from ..models.models import PriceEntry, PriceHistory

logger = logging.getLogger(__name__)

class HistoryTracker:
    """Gestiona el historial de cambios de precios y alertas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_price_history(self, entry_id: int, limit: int = 50) -> List[PriceHistory]:
        """Obtiene el historial de precios de una entrada"""
        return self.db.query(PriceHistory).filter(
            PriceHistory.price_entry_id == entry_id
        ).order_by(PriceHistory.changed_at.desc()).limit(limit).all()
    
    def get_price_trends(self, price_book_id: int, days: int = 30) -> Dict[str, Any]:
        """Analiza tendencias de precios en un período"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Obtener todos los cambios en el período
        changes = self.db.query(PriceHistory).join(PriceEntry).filter(
            and_(
                PriceEntry.price_book_id == price_book_id,
                PriceHistory.changed_at >= cutoff_date
            )
        ).all()
        
        if not changes:
            return {
                'total_changes': 0,
                'average_change': 0,
                'trend': 'stable',
                'volatility': 0,
                'significant_changes': []
            }
        
        # Calcular estadísticas
        price_changes = []
        for change in changes:
            if change.previous_price > 0:
                percent_change = ((change.new_price - change.previous_price) / change.previous_price) * 100
                price_changes.append({
                    'entry_code': change.price_entry.code,
                    'entry_description': change.price_entry.description,
                    'old_price': change.previous_price,
                    'new_price': change.new_price,
                    'percent_change': percent_change,
                    'change_date': change.changed_at,
                    'change_reason': change.change_reason
                })
        
        # Calcular métricas
        average_change = sum(pc['percent_change'] for pc in price_changes) / len(price_changes)
        volatility = (sum(pc['percent_change']**2 for pc in price_changes) / len(price_changes))**0.5
        
        # Determinar tendencia
        if average_change > 2:
            trend = 'increasing'
        elif average_change < -2:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Filtrar cambios significativos (>10%)
        significant_changes = [pc for pc in price_changes if abs(pc['percent_change']) > 10]
        
        return {
            'total_changes': len(changes),
            'average_change': average_change,
            'trend': trend,
            'volatility': volatility,
            'significant_changes': sorted(significant_changes, key=lambda x: abs(x['percent_change']), reverse=True)
        }
    
    def get_price_anomalies(self, price_book_id: int, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detecta anomalías en precios basándose en histórico"""
        # Obtener todas las entradas activas del libro de precios
        entries = self.db.query(PriceEntry).filter(
            and_(
                PriceEntry.price_book_id == price_book_id,
                PriceEntry.is_active == True
            )
        ).all()
        
        anomalies = []
        
        for entry in entries:
            # Obtener historial de precios de esta entrada
            history = self.get_price_history(entry.id, limit=20)
            
            if len(history) >= 3:  # Necesitamos al menos 3 precios para detectar anomalías
                prices = [h.previous_price for h in history] + [entry.unit_price]
                prices = [float(p) for p in prices if p > 0]
                
                if len(prices) >= 3:
                    mean_price = sum(prices) / len(prices)
                    std_price = (sum((p - mean_price)**2 for p in prices) / len(prices))**0.5
                    
                    # Calcular z-score del precio actual
                    if std_price > 0:
                        z_score = abs(entry.unit_price - mean_price) / std_price
                        
                        if z_score > threshold:
                            anomalies.append({
                                'entry_id': entry.id,
                                'code': entry.code,
                                'description': entry.description,
                                'current_price': entry.unit_price,
                                'historical_mean': mean_price,
                                'historical_std': std_price,
                                'z_score': z_score,
                                'price_history': prices[-10:],  # Últimos 10 precios
                                'anomaly_type': 'high' if entry.unit_price > mean_price else 'low'
                            })
        
        return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)
    
    def generate_price_alerts(self, price_book_id: int, alert_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera alertas basadas en configuración"""
        alerts = []
        
        # Configuración de alertas
        max_change_percent = alert_config.get('max_change_percent', 20)
        max_price_increase = alert_config.get('max_price_increase', 50)
        min_price_threshold = alert_config.get('min_price_threshold', 0.01)
        check_volatility = alert_config.get('check_volatility', True)
        
        # Obtener cambios recientes
        recent_changes = self.get_price_trends(price_book_id, days=7)
        
        # Alerta por cambios significativos
        for change in recent_changes.get('significant_changes', []):
            if abs(change['percent_change']) > max_change_percent:
                alerts.append({
                    'type': 'significant_change',
                    'severity': 'high' if abs(change['percent_change']) > max_price_increase else 'medium',
                    'message': f"Cambio significativo en {change['code']}: {change['percent_change']:.1f}%",
                    'details': change,
                    'timestamp': change['change_date']
                })
        
        # Alerta por alta volatilidad
        if check_volatility and recent_changes.get('volatility', 0) > 15:
            alerts.append({
                'type': 'high_volatility',
                'severity': 'medium',
                'message': f"Alta volatilidad detectada: {recent_changes['volatility']:.1f}%",
                'details': {'volatility': recent_changes['volatility']},
                'timestamp': datetime.utcnow()
            })
        
        # Alerta por precios anómalos
        anomalies = self.get_price_anomalies(price_book_id)
        for anomaly in anomalies[:5]:  # Solo los top 5
            alerts.append({
                'type': 'price_anomaly',
                'severity': 'high' if anomaly['z_score'] > 3 else 'medium',
                'message': f"Precio anómalo en {anomaly['code']}: {anomaly['current_price']:.2f} (z-score: {anomaly['z_score']:.2f})",
                'details': anomaly,
                'timestamp': datetime.utcnow()
            })
        
        # Alerta por precios muy bajos
        entries = self.db.query(PriceEntry).filter(
            PriceEntry.price_book_id == price_book_id,
            PriceEntry.is_active == True,
            PriceEntry.unit_price < min_price_threshold
        ).all()
        
        for entry in entries:
            alerts.append({
                'type': 'low_price',
                'severity': 'medium',
                'message': f"Precio muy bajo en {entry.code}: {entry.unit_price}",
                'details': {
                    'code': entry.code,
                    'description': entry.description,
                    'price': entry.unit_price
                },
                'timestamp': datetime.utcnow()
            })
        
        return sorted(alerts, key=lambda x: (x['severity'] == 'high', x['timestamp']), reverse=True)
    
    def get_price_forecast(self, entry_id: int, periods: int = 3) -> Dict[str, Any]:
        """Genera una proyección de precios basada en tendencias"""
        history = self.get_price_history(entry_id, limit=20)
        
        if len(history) < 3:
            return {
                'forecast': [],
                'confidence': 0,
                'trend': 'insufficient_data',
                'message': 'Datos insuficientes para generar proyección'
            }
        
        # Obtener precios en orden cronológico
        prices = [float(h.previous_price) for h in reversed(history)] + [float(history[0].price_entry.unit_price)]
        dates = [h.changed_at for h in reversed(history)] + [datetime.utcnow()]
        
        # Calcular tendencia simple (media móvil)
        if len(prices) >= 3:
            recent_trend = (prices[-1] - prices[-3]) / prices[-3] * 100
            
            # Generar proyección simple
            forecast = []
            last_price = prices[-1]
            
            for i in range(periods):
                # Proyección basada en tendencia reciente, pero atenuada
                projected_change = (recent_trend / 100) * last_price * (0.7 ** (i + 1))
                projected_price = last_price + projected_change
                
                forecast.append({
                    'period': i + 1,
                    'projected_price': round(projected_price, 2),
                    'confidence': max(0.3, 0.9 - i * 0.2)  # Confianza decreciente
                })
                
                last_price = projected_price
            
            # Determinar tendencia
            if recent_trend > 5:
                trend = 'increasing'
            elif recent_trend < -5:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            return {
                'forecast': forecast,
                'confidence': min(0.9, len(history) / 20),  # Confianza basada en cantidad de datos
                'trend': trend,
                'recent_trend_percent': recent_trend,
                'message': f'Tendencia {trend} detectada en los últimos períodos'
            }
        
        else:
            return {
                'forecast': [],
                'confidence': 0,
                'trend': 'insufficient_data',
                'message': 'Datos insuficientes para generar proyección'
            }
    
    def export_price_history(self, price_book_id: int, start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None, format_type: str = 'csv') -> str:
        """Exporta historial de precios"""
        # Construir query
        query = self.db.query(PriceHistory).join(PriceEntry).filter(
            PriceEntry.price_book_id == price_book_id
        )
        
        if start_date:
            query = query.filter(PriceHistory.changed_at >= start_date)
        
        if end_date:
            query = query.filter(PriceHistory.changed_at <= end_date)
        
        history_entries = query.order_by(PriceHistory.changed_at.desc()).all()
        
        # Convertir a formato de exportación
        export_data = []
        for history in history_entries:
            export_data.append({
                'code': history.price_entry.code,
                'description': history.price_entry.description,
                'category': history.price_entry.category,
                'previous_price': history.previous_price,
                'new_price': history.new_price,
                'price_change': history.new_price - history.previous_price,
                'change_percent': ((history.new_price - history.previous_price) / history.previous_price * 100) if history.previous_price > 0 else 0,
                'change_date': history.changed_at.strftime('%Y-%m-%d %H:%M:%S'),
                'change_reason': history.change_reason,
                'changed_by': history.changed_by
            })
        
        # Crear DataFrame y exportar
        import pandas as pd
        df = pd.DataFrame(export_data)
        
        if format_type.lower() == 'csv':
            output_path = f'price_history_export_{price_book_id}.csv'
            df.to_csv(output_path, index=False, encoding='utf-8')
        elif format_type.lower() == 'xlsx':
            output_path = f'price_history_export_{price_book_id}.xlsx'
            df.to_excel(output_path, index=False, engine='openpyxl')
        else:
            raise ValueError(f"Formato de exportación no soportado: {format_type}")
        
        return output_path
    
    def cleanup_old_history(self, price_book_id: int, keep_months: int = 24) -> int:
        """Limpia historial antiguo, manteniendo solo los últimos N meses"""
        cutoff_date = datetime.utcnow() - timedelta(days=keep_months * 30)
        
        # Obtener IDs de entradas del libro de precios
        entry_ids = self.db.query(PriceEntry.id).filter(
            PriceEntry.price_book_id == price_book_id
        ).subquery()
        
        # Eliminar historial antiguo, manteniendo al menos 5 registros por entrada
        deleted_count = 0
        
        entries_to_clean = self.db.query(PriceEntry).filter(
            PriceEntry.price_book_id == price_book_id
        ).all()
        
        for entry in entries_to_clean:
            # Obtener historial ordenado por fecha
            history_entries = self.db.query(PriceHistory).filter(
                PriceHistory.price_entry_id == entry.id
            ).order_by(PriceHistory.changed_at.desc()).all()
            
            # Mantener solo los últimos 5 registros más antiguos que la fecha de corte
            if len(history_entries) > 5:
                old_entries = [
                    h for h in history_entries[5:]  # Saltar los 5 más recientes
                    if h.changed_at < cutoff_date
                ]
                
                for old_entry in old_entries:
                    self.db.delete(old_entry)
                    deleted_count += 1
        
        self.db.commit()
        logger.info(f"Historial antiguo limpiado: {deleted_count} registros eliminados")
        
        return deleted_count