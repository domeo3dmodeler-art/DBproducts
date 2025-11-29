"""
Модель подкатегории
"""
from app import db
from datetime import datetime

# Таблица связи many-to-many для поставщиков и подкатегорий
supplier_subcategories = db.Table('supplier_subcategories',
    db.Column('supplier_id', db.Integer, db.ForeignKey('suppliers.id'), primary_key=True),
    db.Column('subcategory_id', db.Integer, db.ForeignKey('subcategories.id'), primary_key=True)
)

class Subcategory(db.Model):
    """Подкатегория товаров (определяет набор эталонных атрибутов)"""
    __tablename__ = 'subcategories'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Уникальность: код должен быть уникальным в рамках категории
    __table_args__ = (db.UniqueConstraint('code', 'category_id', name='uq_subcategory_code_category'),)
    
    # Связи
    category = db.relationship('ProductCategory', backref='subcategories')
    products = db.relationship('Product', backref='subcategory', lazy='dynamic', cascade='all, delete-orphan')
    attributes = db.relationship('SubcategoryAttribute', backref='subcategory', lazy='dynamic', cascade='all, delete-orphan')
    suppliers = db.relationship('Supplier', secondary=supplier_subcategories, backref='subcategories', lazy='dynamic')
    
    def __repr__(self):
        return f'<Subcategory {self.code}: {self.name}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'description': self.description,
            'is_active': self.is_active,
            'products_count': self.products.count(),
            'attributes_count': self.attributes.count(),
            'suppliers_count': self.suppliers.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_required_attributes(self):
        """Получить список обязательных атрибутов для этой подкатегории"""
        return self.attributes.filter_by(is_required=True).all()
    
    def get_all_attributes(self):
        """Получить все атрибуты подкатегории, отсортированные по sort_order"""
        from app.models.subcategory_attribute import SubcategoryAttribute
        return self.attributes.order_by(SubcategoryAttribute.sort_order).all()
