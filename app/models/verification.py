"""
Модели верификации данных
"""
from app import db
from datetime import datetime
import enum

class IssueType(enum.Enum):
    """Типы проблем при верификации"""
    MISSING_REQUIRED = 'missing_required'  # Отсутствует обязательное поле
    INVALID_TYPE = 'invalid_type'  # Неверный тип данных
    INVALID_VALUE = 'invalid_value'  # Неверное значение
    INVALID_FORMAT = 'invalid_format'  # Неверный формат
    DUPLICATE = 'duplicate'  # Дубликат
    IMAGE_NOT_ACCESSIBLE = 'image_not_accessible'  # Изображение недоступно
    IMAGE_LOW_RESOLUTION = 'image_low_resolution'  # Низкое разрешение изображения
    IMAGE_INVALID_FORMAT = 'image_invalid_format'  # Неверный формат изображения
    MEDIA_COUNT_LOW = 'media_count_low'  # Мало медиа-файлов

class ProductVerification(db.Model):
    """Результаты верификации товара"""
    __tablename__ = 'product_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    completeness_score = db.Column(db.Integer, default=0, nullable=False)  # 0-100
    quality_score = db.Column(db.Integer, default=0, nullable=False)  # 0-100
    media_score = db.Column(db.Integer, default=0, nullable=False)  # 0-100
    overall_score = db.Column(db.Integer, default=0, nullable=False)  # 0-100
    verified_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Связи
    issues = db.relationship('VerificationIssue', backref='verification', lazy='dynamic', cascade='all, delete-orphan')
    verified_by = db.relationship('User', backref='verifications', foreign_keys=[verified_by_id])
    
    def __repr__(self):
        return f'<ProductVerification product={self.product_id} score={self.overall_score}%>'
    
    def to_dict(self, include_issues=False):
        """Сериализация в словарь"""
        data = {
            'id': self.id,
            'product_id': self.product_id,
            'completeness_score': self.completeness_score,
            'quality_score': self.quality_score,
            'media_score': self.media_score,
            'overall_score': self.overall_score,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'issues_count': self.issues.count(),
        }
        
        if include_issues:
            data['issues'] = [issue.to_dict() for issue in self.issues.all()]
        
        return data

class VerificationIssue(db.Model):
    """Проблема, обнаруженная при верификации"""
    __tablename__ = 'verification_issues'
    
    id = db.Column(db.Integer, primary_key=True)
    verification_id = db.Column(db.Integer, db.ForeignKey('product_verifications.id'), nullable=False)
    issue_type = db.Column(db.Enum(IssueType), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey('attributes.id'))
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='warning')  # error, warning, info
    
    # Связи
    attribute = db.relationship('Attribute', backref='verification_issues')
    
    def __repr__(self):
        return f'<VerificationIssue {self.issue_type.value}: {self.message[:50]}>'
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'verification_id': self.verification_id,
            'issue_type': self.issue_type.value,
            'attribute_id': self.attribute_id,
            'attribute_code': self.attribute.code if self.attribute else None,
            'message': self.message,
            'severity': self.severity,
        }

