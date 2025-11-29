"""
Модель истории импорта файлов
"""
from app import db
from datetime import datetime

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
    
    # Статус обработки
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text)  # Сообщение об ошибке, если статус failed
    
    # Связи
    subcategory = db.relationship('Subcategory', backref='import_history')
    imported_by = db.relationship('User', backref='imports')
    
    def __repr__(self):
        return f'<ImportHistory {self.filename} ({self.imported_count}/{self.total_rows})>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'filename': self.filename,
            'subcategory_id': self.subcategory_id,
            'subcategory_name': self.subcategory.name if self.subcategory else None,
            'category_name': self.subcategory.category.name if self.subcategory and self.subcategory.category else None,
            'imported_by': self.imported_by.username if self.imported_by else None,
            'imported_at': self.imported_at.isoformat() if self.imported_at else None,
            'total_rows': self.total_rows,
            'imported_count': self.imported_count,
            'errors_count': self.errors_count,
            'warnings_count': self.warnings_count,
            'status': self.status,
            'error_message': self.error_message,
        }

