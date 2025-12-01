"""
Модель запроса данных от поставщика
"""
from app import db
from datetime import datetime
import enum
import json

class DataRequestStatus(enum.Enum):
    """Статусы запросов данных"""
    NEW = 'new'                    # Новый поставщик, запрос еще не отправлен
    REQUEST_SENT = 'request_sent'   # Запрос отправлен поставщику
    DATA_RECEIVED = 'data_received' # Данные получены от поставщика
    NO_RESPONSE = 'no_response'     # Нет ответа от поставщика
    CANCELLED = 'cancelled'         # Запрос отменен

class DataRequest(db.Model):
    """Запрос данных от поставщика"""
    __tablename__ = 'data_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    
    # Список ID подкатегорий (JSON)
    subcategory_ids = db.Column(db.Text)  # JSON строка с массивом ID
    
    # Статус запроса
    status = db.Column(db.Enum(DataRequestStatus), default=DataRequestStatus.NEW, nullable=False)
    
    # Даты
    request_sent_at = db.Column(db.DateTime)  # Когда отправлен запрос
    data_received_at = db.Column(db.DateTime)  # Когда получены данные
    deadline = db.Column(db.DateTime)  # Срок получения данных
    
    # Информация о запросе
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_message = db.Column(db.Text)  # Текст запроса (опционально)
    response_message = db.Column(db.Text)  # Ответ поставщика (опционально)
    
    # Связь с файлом (когда данные получены)
    import_history_id = db.Column(db.Integer, db.ForeignKey('import_history.id'), nullable=True)
    
    # Метаданные
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    supplier = db.relationship('Supplier', backref='data_requests')
    category = db.relationship('ProductCategory', backref='data_requests')
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref='data_requests')
    import_file = db.relationship('ImportHistory', foreign_keys=[import_history_id], backref=db.backref('data_request_from_import', uselist=False))
    
    def get_subcategory_ids(self):
        """Получить список ID подкатегорий"""
        if not self.subcategory_ids:
            return []
        try:
            return json.loads(self.subcategory_ids)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_subcategory_ids(self, ids):
        """Установить список ID подкатегорий"""
        if ids is None:
            self.subcategory_ids = None
        else:
            self.subcategory_ids = json.dumps(ids)
    
    def is_overdue(self):
        """Проверить, просрочен ли запрос"""
        if not self.deadline:
            return False
        return datetime.utcnow() > self.deadline and self.status == DataRequestStatus.REQUEST_SENT
    
    def __repr__(self):
        return f'<DataRequest {self.id}: {self.supplier.name if self.supplier else "Unknown"} - {self.status.value}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'supplier_code': self.supplier.code if self.supplier else None,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'category_code': self.category.code if self.category else None,
            'subcategory_ids': self.get_subcategory_ids(),
            'status': self.status.value if isinstance(self.status, enum.Enum) else self.status,
            'request_sent_at': self.request_sent_at.isoformat() if self.request_sent_at else None,
            'data_received_at': self.data_received_at.isoformat() if self.data_received_at else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'is_overdue': self.is_overdue(),
            'requested_by_id': self.requested_by_id,
            'requested_by': self.requested_by.username if self.requested_by else None,
            'request_message': self.request_message,
            'response_message': self.response_message,
            'import_history_id': self.import_history_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

