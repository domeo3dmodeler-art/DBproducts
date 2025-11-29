"""
Модель медиа-файлов товара (фото и 3D модели)
"""
from app import db
from datetime import datetime
import enum

class MediaType(enum.Enum):
    """Типы медиа-файлов"""
    IMAGE = 'image'  # Изображение
    THREE_D_MODEL = '3d_model'  # 3D модель

class ProductMedia(db.Model):
    """Медиа-файл товара (фото или 3D модель)"""
    __tablename__ = 'product_media'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey('attributes.id'))  # Связь с атрибутом
    media_type = db.Column(db.Enum(MediaType), nullable=False)
    
    # Информация о файле
    original_url = db.Column(db.String(500))  # Оригинальный URL
    file_path = db.Column(db.String(500), nullable=False)  # Путь к файлу в файловой системе
    file_name = db.Column(db.String(255), nullable=False)  # Имя файла
    file_size = db.Column(db.Integer)  # Размер файла в байтах
    mime_type = db.Column(db.String(100))  # MIME тип файла
    
    # Метаданные для изображений
    width = db.Column(db.Integer)  # Ширина изображения
    height = db.Column(db.Integer)  # Высота изображения
    
    # Метаданные для 3D моделей
    model_format = db.Column(db.String(50))  # Формат 3D модели (glb, gltf, obj и т.д.)
    
    # Порядок сортировки
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Связи
    product = db.relationship('Product', backref='media_files')
    attribute = db.relationship('Attribute', backref='media_files')
    
    def __repr__(self):
        return f'<ProductMedia {self.media_type.value} for product {self.product_id}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'attribute_id': self.attribute_id,
            'media_type': self.media_type.value,
            'original_url': self.original_url,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'width': self.width,
            'height': self.height,
            'model_format': self.model_format,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'downloaded_at': self.downloaded_at.isoformat() if self.downloaded_at else None,
        }

