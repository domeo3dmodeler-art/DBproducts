"""
Модель истории импорта файлов
"""
from app import db
from datetime import datetime
import enum

class ImportFileStatus(enum.Enum):
    """Статусы файлов импорта"""
    PROCESSING = 'processing'  # Файл импортируется
    IN_CATALOG = 'in_catalog'  # Данные в каталоге (товары созданы)
    EXPORTED = 'exported'  # Экспортировано в основную БД
    FAILED = 'failed'  # Ошибка обработки

class ImportHistory(db.Model):
    """История импорта файлов"""
    __tablename__ = 'import_history'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500))  # Путь к файлу (если сохранен)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategories.id'), nullable=False)
    imported_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Результаты импорта
    total_rows = db.Column(db.Integer, default=0)  # Всего строк в файле
    imported_count = db.Column(db.Integer, default=0)  # Успешно импортировано
    errors_count = db.Column(db.Integer, default=0)  # Ошибок
    warnings_count = db.Column(db.Integer, default=0)  # Предупреждений
    
    # Статус обработки (старый, для обратной совместимости)
    status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    
    # Новый статус файла (workflow)
    file_status = db.Column(db.Enum(ImportFileStatus), default=ImportFileStatus.PROCESSING, nullable=False)
    
    # Связь с запросом данных
    data_request_id = db.Column(db.Integer, db.ForeignKey('data_requests.id'), nullable=True)
    
    # Экспорт
    exported_at = db.Column(db.DateTime, nullable=True)
    exported_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    error_message = db.Column(db.Text)  # Сообщение об ошибке, если статус failed
    
    # Связи
    subcategory = db.relationship('Subcategory', backref='import_history')
    imported_by = db.relationship('User', foreign_keys=[imported_by_id], backref='imports')
    data_request = db.relationship('DataRequest', foreign_keys=[data_request_id], backref='imports')
    exported_by = db.relationship('User', foreign_keys=[exported_by_id], backref='exported_imports')
    
    def __repr__(self):
        return f'<ImportHistory {self.filename} ({self.imported_count}/{self.total_rows})>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_path': self.file_path,
            'subcategory_id': self.subcategory_id,
            'subcategory_name': self.subcategory.name if self.subcategory else None,
            'category_name': self.subcategory.category.name if self.subcategory and self.subcategory.category else None,
            'imported_by_id': self.imported_by_id,
            'imported_by': self.imported_by.username if self.imported_by else None,
            'imported_at': self.imported_at.isoformat() if self.imported_at else None,
            'total_rows': self.total_rows,
            'imported_count': self.imported_count,
            'errors_count': self.errors_count,
            'warnings_count': self.warnings_count,
            'status': self.status,  # Старый статус для обратной совместимости
            'file_status': self.file_status.value if isinstance(self.file_status, enum.Enum) else self.file_status,
            'data_request_id': self.data_request_id,
            'data_request': self.data_request.to_dict() if self.data_request else None,
            'exported_at': self.exported_at.isoformat() if self.exported_at else None,
            'exported_by_id': self.exported_by_id,
            'exported_by': self.exported_by.username if self.exported_by else None,
            'error_message': self.error_message,
        }

