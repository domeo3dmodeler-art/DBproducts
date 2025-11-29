"""
Модель связи подкатегории с атрибутами (эталонные свойства)
"""
from app import db

class SubcategoryAttribute(db.Model):
    """Связь подкатегории с атрибутом (эталонное свойство)"""
    __tablename__ = 'subcategory_attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategories.id'), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey('attributes.id'), nullable=False)
    is_required = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    # Уникальность: атрибут может быть добавлен в подкатегорию только один раз
    __table_args__ = (db.UniqueConstraint('subcategory_id', 'attribute_id', name='uq_subcategory_attribute'),)
    
    def __repr__(self):
        return f'<SubcategoryAttribute subcategory={self.subcategory_id} attribute={self.attribute_id} required={self.is_required}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'subcategory_id': self.subcategory_id,
            'attribute_id': self.attribute_id,
            'attribute_code': self.attribute.code if self.attribute else None,
            'attribute_name': self.attribute.name if self.attribute else None,
            'attribute_type': self.attribute.type.value if self.attribute else None,
            'is_required': self.is_required,
            'sort_order': self.sort_order,
        }

