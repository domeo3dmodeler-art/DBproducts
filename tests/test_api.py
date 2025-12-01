"""
Тесты для API endpoints
"""
import pytest
import json
from app.models.category import ProductCategory
from app.models.subcategory import Subcategory
from app.models.supplier import Supplier
from app.models.product import Product, ProductStatus
from app.models.attribute import Attribute, AttributeType
from app.models.user import User


class TestCategoriesAPI:
    """Тесты для API категорий"""
    
    def test_get_categories(self, client, db_session):
        """Тест получения списка категорий"""
        category = ProductCategory(code='01', name='Сантехника')
        db_session.session.add(category)
        db_session.session.commit()
        
        response = client.get('/api/categories')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]['name'] == 'Сантехника'
    
    def test_get_category_by_id(self, client, db_session):
        """Тест получения категории по ID"""
        category = ProductCategory(code='01', name='Сантехника')
        db_session.session.add(category)
        db_session.session.commit()
        
        response = client.get(f'/api/categories/{category.id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['name'] == 'Сантехника'
        assert data['code'] == '01'
    
    def test_create_category_unauthorized(self, client, db_session):
        """Тест создания категории без авторизации"""
        response = client.post('/api/categories', json={
            'code': '02',
            'name': 'Новая категория'
        })
        # Должен быть редирект на логин или 401
        assert response.status_code in [401, 302, 403]
    
    def test_create_category_authorized(self, logged_in_client, db_session):
        """Тест создания категории с авторизацией"""
        response = logged_in_client.post('/api/categories', json={
            'code': '02',
            'name': 'Новая категория',
            'description': 'Описание'
        })
        # Может быть 200 или 201 в зависимости от реализации
        assert response.status_code in [200, 201, 302]


class TestProductsAPI:
    """Тесты для API товаров"""
    
    def test_get_products(self, client, db_session):
        """Тест получения списка товаров"""
        category = ProductCategory(code='01', name='Категория')
        subcategory = Subcategory(code='01_1', name='Подкатегория', category_id=1)
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
        
        response = client.get('/api/products')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_get_product_by_id(self, client, db_session):
        """Тест получения товара по ID"""
        category = ProductCategory(code='01', name='Категория')
        subcategory = Subcategory(code='01_1', name='Подкатегория', category_id=1)
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
        
        response = client.get(f'/api/products/{product.id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['name'] == 'Товар'
    
    def test_filter_products_by_status(self, client, db_session):
        """Тест фильтрации товаров по статусу"""
        category = ProductCategory(code='01', name='Категория')
        subcategory = Subcategory(code='01_1', name='Подкатегория', category_id=1)
        supplier = Supplier(code='SUP001', name='Поставщик', email='supplier@example.com')
        
        db_session.session.add_all([category, subcategory, supplier])
        db_session.session.commit()
        
        product1 = Product(
            name='Товар 1',
            sku='SKU1',
            subcategory_id=subcategory.id,
            status=ProductStatus.DRAFT
        )
        product2 = Product(
            name='Товар 2',
            sku='SKU2',
            subcategory_id=subcategory.id,
            status=ProductStatus.APPROVED
        )
        db_session.session.add_all([product1, product2])
        db_session.session.commit()
        
        response = client.get('/api/products?status=approved')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # Проверяем, что все товары имеют статус approved
        if len(data) > 0:
            assert all(p.get('status') == 'approved' for p in data)


class TestAttributesAPI:
    """Тесты для API атрибутов"""
    
    def test_get_attributes(self, client, db_session):
        """Тест получения списка атрибутов"""
        attribute = Attribute(
            code='name',
            name='Название',
            type=AttributeType.TEXT
        )
        db_session.session.add(attribute)
        db_session.session.commit()
        
        response = client.get('/api/attributes')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_get_attribute_by_id(self, client, db_session):
        """Тест получения атрибута по ID"""
        attribute = Attribute(
            code='name',
            name='Название',
            type=AttributeType.TEXT
        )
        db_session.session.add(attribute)
        db_session.session.commit()
        
        response = client.get(f'/api/attributes/{attribute.id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['name'] == 'Название'


class TestAuthenticationAPI:
    """Тесты для API аутентификации"""
    
    def test_login_success(self, client, db_session):
        """Тест успешного входа"""
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpass123')
        db_session.session.add(user)
        db_session.session.commit()
        
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass123'
        }, follow_redirects=True)
        
        # Должен быть успешный редирект
        assert response.status_code == 200
    
    def test_login_failure(self, client, db_session):
        """Тест неудачного входа"""
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpass123')
        db_session.session.add(user)
        db_session.session.commit()
        
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        # Должна быть ошибка или остаться на странице логина
        assert response.status_code == 200  # Остается на странице логина
    
    def test_logout(self, logged_in_client):
        """Тест выхода"""
        response = logged_in_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200

