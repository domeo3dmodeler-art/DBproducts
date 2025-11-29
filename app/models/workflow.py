"""
Модель workflow (жизненный цикл товара)
"""
from app import db
from datetime import datetime

class ProductStatusHistory(db.Model):
    """История изменений статуса товара"""
    __tablename__ = 'product_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    comment = db.Column(db.Text)
    
    # Связи
    changed_by = db.relationship('User', backref='status_changes', foreign_keys=[changed_by_id])
    
    def __repr__(self):
        return f'<ProductStatusHistory product={self.product_id} {self.old_status} -> {self.new_status}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'changed_by': self.changed_by.username if self.changed_by else None,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'comment': self.comment,
        }

