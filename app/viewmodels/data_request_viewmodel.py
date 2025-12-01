"""
ViewModel для запроса данных
"""
from datetime import datetime


class DataRequestViewModel:
    """ViewModel для представления запроса данных"""
    
    def __init__(self, data_request):
        """
        Инициализация ViewModel
        
        Args:
            data_request: объект DataRequest
        """
        self.id = data_request.id
        self.supplier_id = data_request.supplier_id
        self.supplier_name = data_request.supplier.name if data_request.supplier else None
        self.supplier_code = data_request.supplier.code if data_request.supplier else None
        self.category_id = data_request.category_id
        self.category_name = data_request.category.name if data_request.category else None
        self.subcategory_ids = data_request.subcategory_ids or []
        self.status = data_request.status.value if hasattr(data_request.status, 'value') else str(data_request.status)
        self.request_sent_at = data_request.request_sent_at
        self.data_received_at = data_request.data_received_at
        self.deadline = data_request.deadline
        self.request_message = data_request.request_message
        self.response_message = data_request.response_message
        self.requested_by = data_request.requested_by.username if data_request.requested_by else None
        self.import_history_id = data_request.import_history_id
        self.created_at = data_request.created_at
        self.updated_at = data_request.updated_at
        
        # Подкатегории (если нужно)
        self.subcategories = []
        if data_request.category and self.subcategory_ids:
            for subcat in data_request.category.subcategories:
                if subcat.id in self.subcategory_ids:
                    self.subcategories.append({
                        'id': subcat.id,
                        'name': subcat.name,
                        'code': subcat.code,
                    })
    
    def is_overdue(self):
        """Проверить, просрочен ли запрос"""
        if not self.deadline:
            return False
        return self.deadline < datetime.utcnow() and self.status not in ['data_received', 'cancelled']
    
    def get_status_badge_class(self):
        """Получить CSS класс для badge статуса"""
        classes = {
            'new': 'bg-secondary',
            'request_sent': 'bg-primary',
            'data_received': 'bg-success',
            'no_response': 'bg-danger',
            'cancelled': 'bg-secondary',
        }
        return classes.get(self.status, 'bg-secondary')
    
    def get_status_label(self):
        """Получить текстовую метку статуса"""
        labels = {
            'new': 'Новый',
            'request_sent': 'Отправлен',
            'data_received': 'Получено',
            'no_response': 'Нет ответа',
            'cancelled': 'Отменен',
        }
        return labels.get(self.status, 'Неизвестно')
    
    def to_dict(self):
        """Сериализация в словарь для JSON"""
        return {
            'id': self.id,
            'supplier': {
                'id': self.supplier_id,
                'name': self.supplier_name,
                'code': self.supplier_code,
            },
            'category': {
                'id': self.category_id,
                'name': self.category_name,
            },
            'subcategories': self.subcategories,
            'status': self.status,
            'status_label': self.get_status_label(),
            'status_badge_class': self.get_status_badge_class(),
            'request_sent_at': self.request_sent_at.isoformat() if self.request_sent_at else None,
            'data_received_at': self.data_received_at.isoformat() if self.data_received_at else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'is_overdue': self.is_overdue(),
            'request_message': self.request_message,
            'response_message': self.response_message,
            'requested_by': self.requested_by,
            'import_history_id': self.import_history_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

