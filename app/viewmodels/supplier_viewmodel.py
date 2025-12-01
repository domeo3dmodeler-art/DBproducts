"""
ViewModel для поставщика
"""
from datetime import datetime


class SupplierViewModel:
    """ViewModel для представления поставщика"""
    
    def __init__(self, supplier, stats=None):
        """
        Инициализация ViewModel
        
        Args:
            supplier: объект Supplier
            stats: статистика по запросам (опционально)
        """
        self.id = supplier.id
        self.code = supplier.code
        self.name = supplier.name
        self.email = supplier.email
        self.phone = supplier.phone
        self.is_active = supplier.is_active
        self.created_at = supplier.created_at
        
        # Категории
        self.categories = [{'id': c.id, 'name': c.name, 'code': c.code} 
                          for c in supplier.categories if c.is_active]
        
        # Статистика и статус
        if stats:
            self.stats = stats
            self.overall_status = self._determine_status(stats)
        else:
            self.stats = {}
            self.overall_status = 'new'
    
    def _determine_status(self, stats):
        """
        Определить общий статус поставщика на основе статистики
        
        Args:
            stats: словарь со статистикой
        
        Returns:
            str: статус (has_data, waiting, no_response, new)
        """
        if stats.get('data_received', 0) > 0:
            return 'has_data'
        elif stats.get('request_sent', 0) > 0 or stats.get('overdue', 0) > 0:
            return 'waiting'
        elif stats.get('no_response', 0) > 0:
            return 'no_response'
        else:
            return 'new'
    
    def get_status_icon(self):
        """Получить иконку статуса"""
        icons = {
            'has_data': '🟢',
            'waiting': '🟡',
            'no_response': '🔴',
            'new': '⚪',
        }
        return icons.get(self.overall_status, '⚪')
    
    def get_status_label(self):
        """Получить текстовую метку статуса"""
        labels = {
            'has_data': 'Есть данные',
            'waiting': 'Ожидают ответа',
            'no_response': 'Нет ответа',
            'new': 'Новый',
        }
        return labels.get(self.overall_status, 'Новый')
    
    def to_dict(self):
        """Сериализация в словарь для JSON"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'categories': self.categories,
            'stats': self.stats,
            'overall_status': self.overall_status,
            'status_icon': self.get_status_icon(),
            'status_label': self.get_status_label(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

