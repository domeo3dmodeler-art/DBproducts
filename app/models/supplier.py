"""
Модель поставщика
"""
from app import db
from datetime import datetime

# Таблица связи many-to-many для поставщиков и категорий
supplier_categories = db.Table('supplier_categories',
    db.Column('supplier_id', db.Integer, db.ForeignKey('suppliers.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('product_categories.id'), primary_key=True)
)

class Supplier(db.Model):
    """Поставщик товаров"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи many-to-many
    categories = db.relationship('ProductCategory', secondary=supplier_categories, backref='suppliers', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.code}: {self.name}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'categories': [c.name for c in self.categories.all()],
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'is_active': self.is_active,
            'categories_count': self.categories.count(),
            'subcategories_count': self.subcategories.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
