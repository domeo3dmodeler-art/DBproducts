"""
Модель версионирования товаров
"""
from app import db
from datetime import datetime
import json

class ProductVersion(db.Model):
    """Версия товара"""
    __tablename__ = 'product_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    data = db.Column(db.JSON, nullable=False)  # Снимок данных товара
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment = db.Column(db.Text)
    
    # Связи
    created_by = db.relationship('User', backref='product_versions', foreign_keys=[created_by_id])
    
    # Уникальность: версия товара должна быть уникальной
    __table_args__ = (db.UniqueConstraint('product_id', 'version_number', name='uq_product_version'),)
    
    def __repr__(self):
        return f'<ProductVersion product={self.product_id} version={self.version_number}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'version_number': self.version_number,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by.username if self.created_by else None,
            'comment': self.comment,
        }
    
    @staticmethod
    def create_version(product, user=None, comment=None):
        """Создать версию товара"""
        # Получить последний номер версии
        last_version = ProductVersion.query.filter_by(product_id=product.id).order_by(
            ProductVersion.version_number.desc()
        ).first()
        
        version_number = (last_version.version_number + 1) if last_version else 1
        
        # Создать снимок данных
        data = product.to_dict(include_attributes=True)
        
        # Добавить значения атрибутов
        data['attribute_values'] = {
            pav.attribute.code: pav.value 
            for pav in product.attribute_values.all()
        }
        
        version = ProductVersion(
            product_id=product.id,
            version_number=version_number,
            data=data,
            created_by_id=user.id if user else None,
            comment=comment
        )
        
        db.session.add(version)
        return version

