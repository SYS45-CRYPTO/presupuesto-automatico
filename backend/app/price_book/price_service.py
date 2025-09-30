from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any, Tuple
import logging
from datetime import datetime, date
from decimal import Decimal

from ..models.models import PriceBook, PriceEntry, PriceHistory
from ..models.schemas import PriceEntryCreate, PriceEntryUpdate

logger = logging.getLogger(__name__)

class PriceService:
    """Servicio para gestionar operaciones de libros de precios"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Operaciones de PriceBook
    def create_price_book(self, price_book_data: Dict[str, Any]) -> PriceBook:
        """Crea un nuevo libro de precios"""
        try:
            price_book = PriceBook(**price_book_data)
            self.db.add(price_book)
            self.db.commit()
            self.db.refresh(price_book)
            logger.info(f"Libro de precios creado: {price_book.name} (ID: {price_book.id})")
            return price_book
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando libro de precios: {str(e)}")
            raise
    
    def get_price_book(self, price_book_id: int) -> Optional[PriceBook]:
        """Obtiene un libro de precios por ID"""
        return self.db.query(PriceBook).filter(PriceBook.id == price_book_id).first()
    
    def get_price_books_by_company(self, company_id: int, active_only: bool = True) -> List[PriceBook]:
        """Obtiene todos los libros de precios de una empresa"""
        query = self.db.query(PriceBook).filter(PriceBook.company_id == company_id)
        
        if active_only:
            query = query.filter(PriceBook.is_active == True)
        
        return query.order_by(PriceBook.name).all()
    
    def update_price_book(self, price_book_id: int, updates: Dict[str, Any]) -> Optional[PriceBook]:
        """Actualiza un libro de precios"""
        try:
            price_book = self.get_price_book(price_book_id)
            if not price_book:
                return None
            
            for key, value in updates.items():
                if hasattr(price_book, key):
                    setattr(price_book, key, value)
            
            price_book.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(price_book)
            
            logger.info(f"Libro de precios actualizado: {price_book.name} (ID: {price_book.id})")
            return price_book
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando libro de precios: {str(e)}")
            raise
    
    # Operaciones de PriceEntry
    def create_price_entry(self, entry_data: PriceEntryCreate) -> PriceEntry:
        """Crea una nueva entrada de precio"""
        try:
            entry = PriceEntry(**entry_data.dict())
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)
            logger.info(f"Entrada de precio creada: {entry.code} - {entry.description}")
            return entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando entrada de precio: {str(e)}")
            raise
    
    def batch_create_price_entries(self, entries_data: List[Dict[str, Any]]) -> List[PriceEntry]:
        """Crea múltiples entradas de precio"""
        try:
            entries = []
            for entry_data in entries_data:
                entry = PriceEntry(**entry_data)
                entries.append(entry)
            
            self.db.bulk_save_objects(entries)
            self.db.commit()
            
            logger.info(f"{len(entries)} entradas de precio creadas en lote")
            return entries
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando entradas de precio en lote: {str(e)}")
            raise
    
    def get_price_entry(self, entry_id: int) -> Optional[PriceEntry]:
        """Obtiene una entrada de precio por ID"""
        return self.db.query(PriceEntry).filter(PriceEntry.id == entry_id).first()
    
    def get_price_entries(self, price_book_id: int, active_only: bool = True) -> List[PriceEntry]:
        """Obtiene todas las entradas de un libro de precios"""
        query = self.db.query(PriceEntry).filter(PriceEntry.price_book_id == price_book_id)
        
        if active_only:
            query = query.filter(PriceEntry.is_active == True)
        
        return query.order_by(PriceEntry.code, PriceEntry.description).all()
    
    def search_price_entries(self, price_book_id: int, search_term: str, 
                           category: Optional[str] = None, limit: int = 50) -> List[PriceEntry]:
        """Busca entradas de precio por término de búsqueda"""
        query = self.db.query(PriceEntry).filter(
            and_(
                PriceEntry.price_book_id == price_book_id,
                PriceEntry.is_active == True,
                or_(
                    PriceEntry.code.ilike(f"%{search_term}%"),
                    PriceEntry.description.ilike(f"%{search_term}%"),
                    PriceEntry.category.ilike(f"%{search_term}%")
                )
            )
        )
        
        if category:
            query = query.filter(PriceEntry.category == category)
        
        return query.limit(limit).all()
    
    def update_price_entry(self, entry_id: int, updates: PriceEntryUpdate, 
                          user_id: Optional[str] = None) -> Optional[PriceEntry]:
        """Actualiza una entrada de precio y registra en historial"""
        try:
            entry = self.get_price_entry(entry_id)
            if not entry:
                return None
            
            # Guardar precio anterior para historial
            old_price = entry.unit_price
            
            # Actualizar campos
            update_data = updates.dict(exclude_unset=True)
            
            for key, value in update_data.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            
            entry.updated_at = datetime.utcnow()
            
            # Si cambió el precio, registrar en historial
            if 'unit_price' in update_data and old_price != update_data['unit_price']:
                self._create_price_history_entry(
                    entry_id, old_price, update_data['unit_price'], user_id
                )
            
            self.db.commit()
            self.db.refresh(entry)
            
            logger.info(f"Entrada de precio actualizada: {entry.code} (ID: {entry.id})")
            return entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando entrada de precio: {str(e)}")
            raise
    
    def update_price_entry_price(self, entry_id: int, new_price: float, 
                                reason: str = "Actualización manual",
                                user_id: Optional[str] = None) -> Optional[PriceEntry]:
        """Actualiza solo el precio de una entrada"""
        try:
            entry = self.get_price_entry(entry_id)
            if not entry:
                return None
            
            old_price = entry.unit_price
            
            entry.unit_price = new_price
            entry.updated_at = datetime.utcnow()
            
            # Registrar en historial
            self._create_price_history_entry(entry_id, old_price, new_price, user_id, reason)
            
            self.db.commit()
            self.db.refresh(entry)
            
            logger.info(f"Precio actualizado: {entry.code} de ${old_price} a ${new_price}")
            return entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando precio: {str(e)}")
            raise
    
    def bulk_update_prices(self, price_updates: List[Dict[str, Any]], 
                          user_id: Optional[str] = None) -> Dict[str, Any]:
        """Actualiza múltiples precios"""
        try:
            updated_count = 0
            errors = []
            
            for update in price_updates:
                entry_id = update.get('entry_id')
                new_price = update.get('new_price')
                reason = update.get('reason', 'Actualización masiva')
                
                try:
                    entry = self.update_price_entry_price(entry_id, new_price, reason, user_id)
                    if entry:
                        updated_count += 1
                except Exception as e:
                    errors.append(f"Error actualizando entrada {entry_id}: {str(e)}")
            
            self.db.commit()
            
            result = {
                'updated_count': updated_count,
                'total_count': len(price_updates),
                'errors': errors
            }
            
            logger.info(f"Actualización masiva completada: {updated_count}/{len(price_updates)} precios actualizados")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error en actualización masiva: {str(e)}")
            raise
    
    def delete_price_entry(self, entry_id: int) -> bool:
        """Elimina (desactiva) una entrada de precio"""
        try:
            entry = self.get_price_entry(entry_id)
            if not entry:
                return False
            
            entry.is_active = False
            entry.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Entrada de precio desactivada: {entry.code} (ID: {entry_id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error desactivando entrada de precio: {str(e)}")
            raise
    
    # Búsqueda y análisis de precios
    def find_price_by_code(self, price_book_id: int, code: str) -> Optional[PriceEntry]:
        """Busca una entrada por código exacto"""
        return self.db.query(PriceEntry).filter(
            and_(
                PriceEntry.price_book_id == price_book_id,
                PriceEntry.code == code,
                PriceEntry.is_active == True
            )
        ).first()
    
    def find_prices_by_description(self, price_book_id: int, description: str, 
                                 similarity_threshold: float = 0.6) -> List[PriceEntry]:
        """Busca entradas por descripción con similitud"""
        from sqlalchemy import func
        
        # Primero buscar coincidencia exacta
        exact_matches = self.db.query(PriceEntry).filter(
            and_(
                PriceEntry.price_book_id == price_book_id,
                PriceEntry.description.ilike(f"%{description}%"),
                PriceEntry.is_active == True
            )
        ).all()
        
        if exact_matches:
            return exact_matches
        
        # Si no hay coincidencias exactas, buscar con similitud (si la base de datos lo soporta)
        try:
            similar_matches = self.db.query(PriceEntry).filter(
                and_(
                    PriceEntry.price_book_id == price_book_id,
                    PriceEntry.is_active == True
                )
            ).all()
            
            # Filtrar por similitud manualmente
            filtered_matches = []
            for entry in similar_matches:
                similarity = self._calculate_similarity(description.lower(), entry.description.lower())
                if similarity >= similarity_threshold:
                    filtered_matches.append(entry)
            
            return sorted(filtered_matches, key=lambda x: self._calculate_similarity(description.lower(), x.description.lower()), reverse=True)
            
        except Exception as e:
            logger.warning(f"Error en búsqueda por similitud: {str(e)}")
            return []
    
    def get_price_statistics(self, price_book_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de un libro de precios"""
        entries = self.get_price_entries(price_book_id)
        
        if not entries:
            return {
                'total_entries': 0,
                'price_range': {'min': 0, 'max': 0, 'average': 0},
                'categories': [],
                'units': []
            }
        
        prices = [entry.unit_price for entry in entries]
        categories = list(set(entry.category for entry in entries if entry.category))
        units = list(set(entry.unit for entry in entries if entry.unit))
        
        return {
            'total_entries': len(entries),
            'price_range': {
                'min': float(min(prices)),
                'max': float(max(prices)),
                'average': round(float(sum(prices) / len(prices)), 2)
            },
            'categories': sorted(categories),
            'units': sorted(units)
        }
    
    def compare_price_books(self, price_book_id_1: int, price_book_id_2: int) -> Dict[str, Any]:
        """Compara dos libros de precios"""
        entries_1 = {entry.code: entry for entry in self.get_price_entries(price_book_id_1)}
        entries_2 = {entry.code: entry for entry in self.get_price_entries(price_book_id_2)}
        
        comparison = {
            'common_items': [],
            'only_in_book_1': [],
            'only_in_book_2': [],
            'price_differences': [],
            'summary': {
                'total_book_1': len(entries_1),
                'total_book_2': len(entries_2),
                'common_count': 0,
                'average_difference': 0.0
            }
        }
        
        # Encontrar items comunes y diferencias
        common_codes = set(entries_1.keys()) & set(entries_2.keys())
        only_in_1 = set(entries_1.keys()) - set(entries_2.keys())
        only_in_2 = set(entries_2.keys()) - set(entries_1.keys())
        
        comparison['summary']['common_count'] = len(common_codes)
        comparison['only_in_book_1'] = [entries_1[code] for code in only_in_1]
        comparison['only_in_book_2'] = [entries_2[code] for code in only_in_2]
        
        # Calcular diferencias de precio
        price_differences = []
        for code in common_codes:
            entry_1 = entries_1[code]
            entry_2 = entries_2[code]
            
            if entry_1.unit_price != entry_2.unit_price:
                difference = abs(entry_2.unit_price - entry_1.unit_price)
                percentage_change = ((entry_2.unit_price - entry_1.unit_price) / entry_1.unit_price * 100) if entry_1.unit_price > 0 else 0
                
                price_differences.append({
                    'code': code,
                    'description': entry_1.description,
                    'price_book_1': entry_1.unit_price,
                    'price_book_2': entry_2.unit_price,
                    'difference': difference,
                    'percentage_change': percentage_change
                })
        
        comparison['price_differences'] = sorted(price_differences, key=lambda x: abs(x['percentage_change']), reverse=True)
        
        # Calcular promedio de diferencias
        if price_differences:
            comparison['summary']['average_difference'] = sum(abs(pd['percentage_change']) for pd in price_differences) / len(price_differences)
        
        return comparison
    
    # Métodos auxiliares
    def _create_price_history_entry(self, entry_id: int, old_price: float, new_price: float, 
                                   user_id: Optional[str] = None, reason: str = "Actualización manual"):
        """Crea una entrada en el historial de precios"""
        try:
            history_entry = PriceHistory(
                price_entry_id=entry_id,
                previous_price=old_price,
                new_price=new_price,
                change_reason=reason,
                changed_by=user_id
            )
            
            self.db.add(history_entry)
            
        except Exception as e:
            logger.error(f"Error creando entrada de historial: {str(e)}")
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calcula la similitud entre dos strings"""
        import difflib
        return difflib.SequenceMatcher(None, str1, str2).ratio()
    
    def get_price_history(self, entry_id: int, limit: int = 10) -> List[PriceHistory]:
        """Obtiene el historial de precios de una entrada"""
        return self.db.query(PriceHistory).filter(
            PriceHistory.price_entry_id == entry_id
        ).order_by(PriceHistory.changed_at.desc()).limit(limit).all()
    
    def get_price_trends(self, price_book_id: int, days: int = 30) -> Dict[str, Any]:
        """Obtiene tendencias de precios recientes"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Obtener cambios recientes
        recent_changes = self.db.query(PriceHistory).join(PriceEntry).filter(
            and_(
                PriceEntry.price_book_id == price_book_id,
                PriceHistory.changed_at >= cutoff_date
            )
        ).all()
        
        if not recent_changes:
            return {'changes': [], 'trend': 'stable', 'average_change': 0}
        
        # Analizar tendencias
        changes = []
        for change in recent_changes:
            percentage_change = ((change.new_price - change.previous_price) / change.previous_price * 100) if change.previous_price > 0 else 0
            changes.append({
                'code': change.price_entry.code,
                'description': change.price_entry.description,
                'old_price': change.previous_price,
                'new_price': change.new_price,
                'percentage_change': percentage_change,
                'change_date': change.changed_at
            })
        
        # Calcular tendencia general
        average_change = sum(c['percentage_change'] for c in changes) / len(changes)
        
        if average_change > 5:
            trend = 'increasing'
        elif average_change < -5:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'changes': sorted(changes, key=lambda x: x['change_date'], reverse=True),
            'trend': trend,
            'average_change': average_change
        }