"""
Тесты для моделей данных
"""
import pytest
from datetime import datetime
from app.models.category import ProductCategory
from app.models.subcategory import Subcategory
from app.models.supplier import Supplier
from app.models.product import Product, ProductStatus
from app.models.attribute import Attribute, AttributeType
from app.models.user import User
from app.models.verification import ProductVerification
from app.models.product_media import ProductMedia


class TestUserModel:
    """Тесты для модели User"""
    
    def test_create_user(self, db_session):
        """Тест создания пользователя"""
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('password123')
        db_session.session.add(user)
        db_session.session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')
    
    def test_user_password_hashing(self, db_session):
        """Тест хеширования пароля"""
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('password123')
        
        assert user.password_hash != 'password123'
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')


class TestCategoryModel:
    """Тесты для модели ProductCategory"""
    
    def test_create_category(self, db_session):
        """Тест создания категории"""
        category = ProductCategory(
            code='01',
            name='Сантехника',
            description='Категория сантехнических товаров'
        )
        db_session.session.add(category)
        db_session.session.commit()
        
        assert category.id is not None
        assert category.code == '01'
        assert category.name == 'Сантехника'
        assert category.is_active is True
    
    def test_category_soft_delete(self, db_session):
        """Тест мягкого удаления категории"""
        category = ProductCategory(
            code='01',
            name='Сантехника'
        )
        db_session.session.add(category)
        db_session.session.commit()
        
        category.is_active = False
        db_session.session.commit()
        
        assert category.is_active is False


class TestSubcategoryModel:
    """Тесты для модели Subcategory"""
    
    def test_create_subcategory(self, db_session):
        """Тест создания подкатегории"""
        category = ProductCategory(code='01', name='Сантехника')
        db_session.session.add(category)
        db_session.session.commit()
        
        subcategory = Subcategory(
            code='01_1',
            name='Смесители',
            category_id=category.id
        )
        db_session.session.add(subcategory)
        db_session.session.commit()
        
        assert subcategory.id is not None
        assert subcategory.code == '01_1'
        assert subcategory.category_id == category.id
        assert subcategory.category == category


class TestSupplierModel:
    """Тесты для модели Supplier"""
    
    def test_create_supplier(self, db_session):
        """Тест создания поставщика"""
        supplier = Supplier(
            code='SUP001',
            name='ООО Поставщик',
            email='supplier@example.com',
            phone='+7 999 123 45 67'
        )
        db_session.session.add(supplier)
        db_session.session.commit()
        
        assert supplier.id is not None
        assert supplier.name == 'ООО Поставщик'
        assert supplier.email == 'supplier@example.com'


class TestAttributeModel:
    """Тесты для модели Attribute"""
    
    def test_create_attribute(self, db_session):
        """Тест создания атрибута"""
        attribute = Attribute(
            code='name',
            name='Название',
            type=AttributeType.TEXT,
            unit=None
        )
        db_session.session.add(attribute)
        db_session.session.commit()
        
        assert attribute.id is not None
        assert attribute.code == 'name'
        assert attribute.name == 'Название'
        assert attribute.type == AttributeType.TEXT
    
    def test_attribute_with_unit(self, db_session):
        """Тест создания атрибута с единицей измерения"""
        attribute = Attribute(
            code='weight',
            name='Вес',
            type=AttributeType.NUMBER,
            unit='кг'
        )
        db_session.session.add(attribute)
        db_session.session.commit()
        
        assert attribute.unit == 'кг'
    
    def test_attribute_unique_name(self, db_session):
        """Тест уникальности названия атрибута"""
        attribute1 = Attribute(
            code='name1',
            name='Название',
            type=AttributeType.TEXT
        )
        db_session.session.add(attribute1)
        db_session.session.commit()
        
        # Попытка создать атрибут с таким же названием должна вызвать ошибку
        attribute2 = Attribute(
            code='name2',
            name='Название',
            type=AttributeType.TEXT
        )
        db_session.session.add(attribute2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.session.commit()


class TestProductModel:
    """Тесты для модели Product"""
    
    def test_create_product(self, db_session):
        """Тест создания товара"""
        category = ProductCategory(code='01', name='Сантехника')
        subcategory = Subcategory(code='01_1', name='Смесители', category_id=1)
        supplier = Supplier(code='SUP001', name='Поставщик', email='supplier@example.com')
        
        db_session.session.add_all([category, subcategory, supplier])
        db_session.session.commit()
        
        product = Product(
            name='Смеситель для раковины',
            sku='SKU123',
            subcategory_id=subcategory.id,
            status=ProductStatus.DRAFT
        )
        db_session.session.add(product)
        db_session.session.commit()
        
        assert product.id is not None
        assert product.name == 'Смеситель для раковины'
        assert product.status == ProductStatus.DRAFT
    
    def test_product_status_transitions(self, db_session):
        """Тест переходов статусов товара"""
        category = ProductCategory(code='01', name='Сантехника')
        subcategory = Subcategory(code='01_1', name='Смесители', category_id=1)
        supplier = Supplier(code='SUP001', name='Поставщик', email='supplier@example.com')
        
        db_session.session.add_all([category, subcategory, supplier])
        db_session.session.commit()
        
        product = Product(
            name='Товар',
            sku='SKU123',
            subcategory_id=subcategory.id,
            status=ProductStatus.DRAFT
        )
        db_session.session.add(product)
        db_session.session.commit()
        
        # Переход статусов
        product.status = ProductStatus.IN_PROGRESS
        db_session.session.commit()
        assert product.status == ProductStatus.IN_PROGRESS
        
        product.status = ProductStatus.TO_REVIEW
        db_session.session.commit()
        assert product.status == ProductStatus.TO_REVIEW
        
        product.status = ProductStatus.APPROVED
        db_session.session.commit()
        assert product.status == ProductStatus.APPROVED


class TestProductVerificationModel:
    """Тесты для модели ProductVerification"""
    
    def test_create_verification(self, db_session):
        """Тест создания верификации"""
        category = ProductCategory(code='01', name='Сантехника')
        subcategory = Subcategory(code='01_1', name='Смесители', category_id=1)
        supplier = Supplier(code='SUP001', name='Поставщик', email='supplier@example.com')
        
        db_session.session.add_all([category, subcategory, supplier])
        db_session.session.commit()
        
        product = Product(
            name='Товар',
            sku='SKU123',
            subcategory_id=subcategory.id
        )
        db_session.session.add(product)
        db_session.session.commit()
        
        verification = ProductVerification(
            product_id=product.id,
            completeness_score=85.0,
            quality_score=90.0,
            media_score=75.0,
            overall_score=85.0
        )
        db_session.session.add(verification)
        db_session.session.commit()
        
        assert verification.id is not None
        assert verification.completeness_score == 85.0
        assert verification.overall_score == 85.0
        assert verification.product_id == product.id

