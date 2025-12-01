"""
Модель товара
"""
from app import db
from datetime import datetime
import enum

class ProductStatus(enum.Enum):
    """Статусы товара в workflow"""
    DRAFT = 'draft'  # Черновик
    IN_PROGRESS = 'in_progress'  # В работе
    TO_REVIEW = 'to_review'  # На проверке
    APPROVED = 'approved'  # Утвержден
    REJECTED = 'rejected'  # Отклонен
    EXPORTED = 'exported'  # Экспортирован

class Product(db.Model):
    """Товар"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, nullable=False, index=True)  # Артикул
    name = db.Column(db.String(255), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategories.id'), nullable=False)
    status = db.Column(db.Enum(ProductStatus), default=ProductStatus.DRAFT, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Связь с файлом импорта
    import_history_id = db.Column(db.Integer, db.ForeignKey('import_history.id'), nullable=True)
    
    # Экспорт в основную БД
    is_exported = db.Column(db.Boolean, default=False, nullable=False)
    exported_at = db.Column(db.DateTime, nullable=True)
    
    # Связи
    attribute_values = db.relationship('ProductAttributeValue', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    verifications = db.relationship('ProductVerification', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    status_history = db.relationship('ProductStatusHistory', backref='product', lazy='dynamic', cascade='all, delete-orphan', order_by='ProductStatusHistory.changed_at.desc()')
    versions = db.relationship('ProductVersion', backref='product', lazy='dynamic', cascade='all, delete-orphan', order_by='ProductVersion.version_number.desc()')
    import_file = db.relationship('ImportHistory', foreign_keys=[import_history_id], backref='products')
    
    def __repr__(self):
        return f'<Product {self.sku}: {self.name}>'
    
    def to_dict(self, include_attributes=False, include_verification=False):
        """Сериализация в словарь"""
        data = {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'subcategory_id': self.subcategory_id,
            'subcategory_name': self.subcategory.name if self.subcategory else None,
            'supplier_name': self.subcategory.suppliers.first().name if self.subcategory and self.subcategory.suppliers.first() else None,
            'category_name': self.subcategory.category.name if self.subcategory and self.subcategory.category else None,
            'status': self.status.value,
            'description': self.description,
            'import_history_id': self.import_history_id,
            'is_exported': self.is_exported,
            'exported_at': self.exported_at.isoformat() if self.exported_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_attributes:
            data['attributes'] = {av.attribute.code: av.value for av in self.attribute_values.all()}
        
        if include_verification:
            from app.models.verification import ProductVerification
            latest_verification = self.verifications.order_by(ProductVerification.verified_at.desc()).first()
            if latest_verification:
                data['verification'] = latest_verification.to_dict()
        
        return data
    
    def get_attribute_value(self, attribute_code):
        """Получить значение атрибута по коду"""
        pav = self.attribute_values.join('attribute').filter_by(code=attribute_code).first()
        return pav.value if pav else None
    
    def set_attribute_value(self, attribute_code, value):
        """Установить значение атрибута"""
        from app.models.attribute import Attribute
        from app.models.subcategory_attribute import SubcategoryAttribute
        
        # Найти атрибут
        attribute = Attribute.query.filter_by(code=attribute_code).first()
        if not attribute:
            raise ValueError(f"Attribute {attribute_code} not found")
        
        # Проверить, что атрибут есть в подкатегории
        subcat_attr = SubcategoryAttribute.query.filter_by(
            subcategory_id=self.subcategory_id,
            attribute_id=attribute.id
        ).first()
        if not subcat_attr:
            raise ValueError(f"Attribute {attribute_code} is not in subcategory {self.subcategory_id}")
        
        # Найти или создать ProductAttributeValue
        pav = ProductAttributeValue.query.filter_by(
            product_id=self.id,
            attribute_id=attribute.id
        ).first()
        
        if pav:
            pav.value = value
        else:
            pav = ProductAttributeValue(
                product_id=self.id,
                attribute_id=attribute.id,
                value=value
            )
            db.session.add(pav)
        
        return pav

class ProductAttributeValue(db.Model):
    """Значение атрибута для товара"""
    __tablename__ = 'product_attribute_values'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey('attributes.id'), nullable=False)
    value = db.Column(db.Text, nullable=False)  # JSON для сложных типов
    
    # Уникальность: один атрибут - одно значение для товара
    __table_args__ = (db.UniqueConstraint('product_id', 'attribute_id', name='uq_product_attribute'),)
    
    def __repr__(self):
        return f'<ProductAttributeValue product={self.product_id} attribute={self.attribute_id} value={self.value[:50]}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'attribute_id': self.attribute_id,
            'attribute_code': self.attribute.code if self.attribute else None,
            'attribute_name': self.attribute.name if self.attribute else None,
            'value': self.value,
        }

