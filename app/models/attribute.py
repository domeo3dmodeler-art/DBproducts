"""
Модели атрибутов (глобальный справочник)
"""
from app import db
from datetime import datetime
import enum

class AttributeType(enum.Enum):
    """Типы атрибутов"""
    TEXT = 'text'
    NUMBER = 'number'
    DATE = 'date'
    BOOLEAN = 'boolean'
    URL = 'url'
    IMAGE = 'image'
    SELECT = 'select'

class Attribute(db.Model):
    """Глобальный справочник атрибутов"""
    __tablename__ = 'attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)  # Уникальное название
    type = db.Column(db.Enum(AttributeType), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(50))  # Единица измерения (кг, м, шт и т.д.)
    is_unique = db.Column(db.Boolean, default=False, nullable=False)
    validation_rules = db.Column(db.JSON)  # Правила валидации (min, max, pattern и т.д.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    values = db.relationship('AttributeValue', backref='attribute', lazy='dynamic', cascade='all, delete-orphan')
    subcategory_attributes = db.relationship('SubcategoryAttribute', backref='attribute', lazy='dynamic')
    
    def __repr__(self):
        return f'<Attribute {self.code}: {self.name} ({self.type.value})>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'unit': self.unit,
            'is_unique': self.is_unique,
            'validation_rules': self.validation_rules,
            'has_select_values': self.type == AttributeType.SELECT and self.values.count() > 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class AttributeValue(db.Model):
    """Варианты значений для атрибутов типа SELECT"""
    __tablename__ = 'attribute_values'
    
    id = db.Column(db.Integer, primary_key=True)
    attribute_id = db.Column(db.Integer, db.ForeignKey('attributes.id'), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Уникальность значения в рамках атрибута
    __table_args__ = (db.UniqueConstraint('attribute_id', 'value', name='uq_attribute_value'),)
    
    def __repr__(self):
        return f'<AttributeValue {self.value} for {self.attribute.code}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'attribute_id': self.attribute_id,
            'value': self.value,
            'display_name': self.display_name or self.value,
            'sort_order': self.sort_order,
        }

