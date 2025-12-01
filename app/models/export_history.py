"""
Модель истории экспорта данных в основную БД
"""
from app import db
from datetime import datetime
import json

class ExportHistory(db.Model):
    """История экспорта данных в основную БД"""
    __tablename__ = 'export_history'
    
    id = db.Column(db.Integer, primary_key=True)
    import_history_id = db.Column(db.Integer, db.ForeignKey('import_history.id'), nullable=True)
    data_request_id = db.Column(db.Integer, db.ForeignKey('data_requests.id'), nullable=True)
    
    # Какие товары экспортированы
    products_count = db.Column(db.Integer, default=0)
    products_ids = db.Column(db.Text)  # JSON строка с массивом ID товаров
    
    # Когда и кем экспортировано
    exported_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    exported_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Результаты экспорта
    status = db.Column(db.String(20), default='success')  # success, failed, partial
    error_message = db.Column(db.Text)  # Сообщение об ошибке, если статус failed
    
    # Метаданные экспорта
    export_config = db.Column(db.Text)  # JSON строка с конфигурацией экспорта
    export_format = db.Column(db.String(20), default='json')  # json, xml, direct_db
    
    # Откат
    is_rolled_back = db.Column(db.Boolean, default=False, nullable=False)
    rolled_back_at = db.Column(db.DateTime, nullable=True)
    rolled_back_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Связи
    import_file = db.relationship('ImportHistory', foreign_keys=[import_history_id], backref='export_history')
    data_request = db.relationship('DataRequest', foreign_keys=[data_request_id], backref='export_history')
    exported_by = db.relationship('User', foreign_keys=[exported_by_id], backref='exports')
    rolled_back_by = db.relationship('User', foreign_keys=[rolled_back_by_id], backref='rolled_back_exports')
    
    def get_products_ids(self):
        """Получить список ID товаров"""
        if not self.products_ids:
            return []
        try:
            return json.loads(self.products_ids)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_products_ids(self, ids):
        """Установить список ID товаров"""
        if ids is None:
            self.products_ids = None
        else:
            self.products_ids = json.dumps(ids)
    
    def get_export_config(self):
        """Получить конфигурацию экспорта"""
        if not self.export_config:
            return {}
        try:
            return json.loads(self.export_config)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_export_config(self, config):
        """Установить конфигурацию экспорта"""
        if config is None:
            self.export_config = None
        else:
            self.export_config = json.dumps(config)
    
    def __repr__(self):
        return f'<ExportHistory {self.id}: {self.products_count} товаров - {self.status}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'import_history_id': self.import_history_id,
            'data_request_id': self.data_request_id,
            'products_count': self.products_count,
            'products_ids': self.get_products_ids(),
            'exported_at': self.exported_at.isoformat() if self.exported_at else None,
            'exported_by_id': self.exported_by_id,
            'exported_by': self.exported_by.username if self.exported_by else None,
            'status': self.status,
            'error_message': self.error_message,
            'export_config': self.get_export_config(),
            'export_format': self.export_format,
            'is_rolled_back': self.is_rolled_back,
            'rolled_back_at': self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            'rolled_back_by_id': self.rolled_back_by_id,
            'rolled_back_by': self.rolled_back_by.username if self.rolled_back_by else None,
        }

