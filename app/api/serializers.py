"""
Сериализаторы для API
"""
from flask import url_for
from app.models.category import ProductCategory
from app.models.supplier import Supplier
from app.models.subcategory import Subcategory
from app.models.product import Product, ProductStatus
from app.models.attribute import Attribute, AttributeType
from app.models.verification import ProductVerification
from app.models.workflow import ProductStatusHistory
from app.models.version import ProductVersion

class CategorySerializer:
    """Сериализатор для категорий"""
    
    @staticmethod
    def serialize(category, include_suppliers=False):
        """Сериализовать категорию"""
        data = category.to_dict()
        if include_suppliers:
            data['suppliers'] = [SupplierSerializer.serialize(s) for s in category.suppliers.all()]
        return data

class SupplierSerializer:
    """Сериализатор для поставщиков"""
    
    @staticmethod
    def serialize(supplier, include_subcategories=False):
        """Сериализовать поставщика"""
        data = supplier.to_dict()
        if include_subcategories:
            data['subcategories'] = [SubcategorySerializer.serialize(s) for s in supplier.subcategories.all()]
        return data

class SubcategorySerializer:
    """Сериализатор для подкатегорий"""
    
    @staticmethod
    def serialize(subcategory, include_attributes=False, include_products=False):
        """Сериализовать подкатегорию"""
        data = subcategory.to_dict()
        if include_attributes:
            data['attributes'] = [attr.to_dict() for attr in subcategory.get_all_attributes()]
        if include_products:
            data['products'] = [ProductSerializer.serialize(p) for p in subcategory.products.all()]
        return data

class ProductSerializer:
    """Сериализатор для товаров"""
    
    @staticmethod
    def serialize(product, include_attributes=False, include_verification=False, include_history=False):
        """Сериализовать товар"""
        data = product.to_dict(include_attributes=include_attributes, include_verification=include_verification)
        if include_history:
            data['status_history'] = [h.to_dict() for h in product.status_history.all()]
        return data

class AttributeSerializer:
    """Сериализатор для атрибутов"""
    
    @staticmethod
    def serialize(attribute, include_values=False):
        """Сериализовать атрибут"""
        data = attribute.to_dict()
        if include_values and attribute.type == AttributeType.SELECT:
            data['values'] = [av.to_dict() for av in attribute.values.all()]
        return data

class VerificationSerializer:
    """Сериализатор для верификации"""
    
    @staticmethod
    def serialize(verification, include_issues=True):
        """Сериализовать верификацию"""
        return verification.to_dict(include_issues=include_issues)

