"""
Модель категории товаров
"""
from app import db
from datetime import datetime

class ProductCategory(db.Model):
    """Категория товаров (верхний уровень иерархии)"""
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductCategory {self.code}: {self.name}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'subcategories_count': self.subcategories.count() if hasattr(self, 'subcategories') else 0,
            'suppliers_count': self.suppliers.count() if hasattr(self, 'suppliers') else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
