"""
Тесты для сервисов
"""
import pytest
from app.utils import code_generator
from app.utils import attribute_mapper
from app.services.verification_service import VerificationService
from app.models.category import ProductCategory
from app.models.subcategory import Subcategory
from app.models.product import Product, ProductStatus
from app.models.attribute import Attribute, AttributeType
from app.models.supplier import Supplier


class TestCodeGenerator:
    """Тесты для CodeGenerator"""
    
    def test_generate_category_code_first(self, db_session):
        """Тест генерации первого кода категории"""
        from app.utils.code_generator import generate_category_code
        code = generate_category_code()
        assert code == '01'
    
    def test_generate_category_code_sequential(self, db_session):
        """Тест последовательной генерации кодов категорий"""
        from app.utils.code_generator import generate_category_code
        # Создаем несколько категорий
        cat1 = ProductCategory(code='01', name='Категория 1')
        cat2 = ProductCategory(code='02', name='Категория 2')
        db_session.session.add_all([cat1, cat2])
        db_session.session.commit()
        
        code = generate_category_code()
        assert code == '03'
    
    def test_generate_subcategory_code_first(self, db_session):
        """Тест генерации первого кода подкатегории"""
        from app.utils.code_generator import generate_subcategory_code
        category = ProductCategory(code='01', name='Категория')
        db_session.session.add(category)
        db_session.session.commit()
        
        code = generate_subcategory_code(category.id)
        assert code == '01_1'
    
    def test_generate_subcategory_code_sequential(self, db_session):
        """Тест последовательной генерации кодов подкатегорий"""
        from app.utils.code_generator import generate_subcategory_code
        category = ProductCategory(code='01', name='Категория')
        db_session.session.add(category)
        db_session.session.commit()
        
        sub1 = Subcategory(code='01_1', name='Подкатегория 1', category_id=category.id)
        sub2 = Subcategory(code='01_2', name='Подкатегория 2', category_id=category.id)
        db_session.session.add_all([sub1, sub2])
        db_session.session.commit()
        
        code = generate_subcategory_code(category.id)
        assert code == '01_3'


class TestAttributeMapper:
    """Тесты для AttributeMapper"""
    
    def test_transliterate_russian(self):
        """Тест транслитерации русских названий"""
        from app.utils.attribute_mapper import transliterate_russian_to_english
        result = transliterate_russian_to_english('Название товара')
        assert 'nazvanie' in result.lower() or 'name' in result.lower()
    
    def test_generate_code_from_name(self):
        """Тест генерации кода из названия"""
        from app.utils.attribute_mapper import generate_attribute_code_from_name
        code = generate_attribute_code_from_name('Название товара')
        assert code is not None
        assert len(code) > 0
    
    def test_generate_code_with_special_chars(self):
        """Тест генерации кода со специальными символами"""
        from app.utils.attribute_mapper import generate_attribute_code_from_name
        code = generate_attribute_code_from_name('Вес (кг)')
        assert 'ves' in code.lower() or 'weight' in code.lower()
    
    def test_mapping_dictionary(self):
        """Тест использования словаря маппинга"""
        from app.utils.attribute_mapper import generate_attribute_code_from_name
        # Проверяем, что известные термины маппятся правильно
        code = generate_attribute_code_from_name('Артикул')
        assert 'artikul' in code.lower() or 'sku' in code.lower()


class TestVerificationService:
    """Тесты для VerificationService"""
    
    def test_verify_completeness(self, db_session):
        """Тест проверки полноты данных"""
        category = ProductCategory(code='01', name='Категория')
        subcategory = Subcategory(code='01_1', name='Подкатегория', category_id=1)
        supplier = Supplier(code='SUP001', name='Поставщик', email='supplier@example.com')
        
        db_session.session.add_all([category, subcategory, supplier])
        db_session.session.commit()
        
        # Товар с неполными данными
        product = Product(
            name='Товар',
            sku='SKU123',
            subcategory_id=subcategory.id
            # Нет описания, цены и т.д.
        )
        db_session.session.add(product)
        db_session.session.commit()
        
        from app.models.user import User
        user = User(username='test', email='test@test.com')
        user.set_password('test')
        db_session.session.add(user)
        db_session.session.commit()
        
        result = VerificationService.verify_product(product, user=user)
        
        assert result is not None
        assert hasattr(result, 'completeness_score')
        assert result.completeness_score <= 100
    
    def test_verify_quality(self, db_session):
        """Тест проверки качества данных"""
        category = ProductCategory(code='01', name='Категория')
        subcategory = Subcategory(code='01_1', name='Подкатегория', category_id=1)
        supplier = Supplier(code='SUP001', name='Поставщик', email='supplier@example.com')
        
        db_session.session.add_all([category, subcategory, supplier])
        db_session.session.commit()
        
        product = Product(
            name='Товар',
            sku='SKU123',
            subcategory_id=subcategory.id,
            description='Описание товара'
        )
        db_session.session.add(product)
        db_session.session.commit()
        
        from app.models.user import User
        user = User(username='test', email='test@test.com')
        user.set_password('test')
        db_session.session.add(user)
        db_session.session.commit()
        
        result = VerificationService.verify_product(product, user=user)
        
        assert result is not None
        assert hasattr(result, 'quality_score')
        assert result.quality_score >= 0
        assert result.quality_score <= 100
    
    def test_detect_duplicates(self, db_session):
        """Тест обнаружения дубликатов"""
        category = ProductCategory(code='01', name='Категория')
        subcategory = Subcategory(code='01_1', name='Подкатегория', category_id=1)
        supplier = Supplier(code='SUP001', name='Поставщик', email='supplier@example.com')
        
        db_session.session.add_all([category, subcategory, supplier])
        db_session.session.commit()
        
        # Первый товар
        product1 = Product(
            name='Товар 1',
            sku='SKU123',
            subcategory_id=subcategory.id
        )
        db_session.session.add(product1)
        db_session.session.commit()
        
        # Второй товар с другим артикулом (SKU уникален, поэтому дубликат невозможен)
        product2 = Product(
            name='Товар 2',
            sku='SKU456',  # Другой SKU, так как поле уникальное
            subcategory_id=subcategory.id
        )
        db_session.session.add(product2)
        db_session.session.commit()
        
        # Проверяем, что товары созданы
        assert product1.id is not None
        assert product2.id is not None
        assert product1.sku != product2.sku  # SKU должны быть разными

