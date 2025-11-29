"""
Модели данных
"""
from app.models.category import ProductCategory
from app.models.supplier import Supplier
from app.models.subcategory import Subcategory
from app.models.attribute import Attribute, AttributeValue
from app.models.subcategory_attribute import SubcategoryAttribute
from app.models.product import Product, ProductAttributeValue
from app.models.verification import ProductVerification, VerificationIssue
from app.models.workflow import ProductStatusHistory
from app.models.version import ProductVersion
from app.models.user import User
from app.models.import_history import ImportHistory
from app.models.product_media import ProductMedia, MediaType

__all__ = [
    'ProductCategory',
    'Supplier',
    'Subcategory',
    'Attribute',
    'AttributeValue',
    'SubcategoryAttribute',
    'Product',
    'ProductAttributeValue',
    'ProductVerification',
    'VerificationIssue',
    'ProductStatusHistory',
    'ProductVersion',
    'User',
    'ImportHistory',
    'ProductMedia',
    'MediaType',
]

