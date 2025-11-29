"""
API маршруты
"""
from flask import jsonify, request, url_for
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models.category import ProductCategory
from app.models.supplier import Supplier
from app.models.subcategory import Subcategory
from app.models.product import Product, ProductStatus
from app.models.attribute import Attribute
from app.models.verification import ProductVerification
from app.models.workflow import ProductStatusHistory
from app.models.version import ProductVersion
from app.api.serializers import (
    CategorySerializer, SupplierSerializer, SubcategorySerializer,
    ProductSerializer, AttributeSerializer, VerificationSerializer
)
from app.services.verification_service import VerificationService
from app.models.version import ProductVersion as PV

# ========== КАТЕГОРИИ ==========

@bp.route('/categories', methods=['GET'])
def get_categories():
    """Получить список категорий"""
    include_suppliers = request.args.get('include_suppliers', 'false').lower() == 'true'
    categories = ProductCategory.query.all()
    return jsonify([CategorySerializer.serialize(cat, include_suppliers=include_suppliers) for cat in categories])

@bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Получить категорию по ID"""
    category = ProductCategory.query.get_or_404(category_id)
    include_suppliers = request.args.get('include_suppliers', 'false').lower() == 'true'
    return jsonify(CategorySerializer.serialize(category, include_suppliers=include_suppliers))

@bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    """Создать категорию"""
    data = request.get_json()
    
    if not data or not data.get('code') or not data.get('name'):
        return jsonify({'error': 'Необходимо указать code и name'}), 400
    
    # Проверить уникальность кода
    if ProductCategory.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Категория с таким кодом уже существует'}), 400
    
    category = ProductCategory(
        code=data['code'],
        name=data['name'],
        description=data.get('description'),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify(CategorySerializer.serialize(category)), 201

@bp.route('/categories/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    """Обновить категорию"""
    category = ProductCategory.query.get_or_404(category_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Необходимо передать данные'}), 400
    
    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'is_active' in data:
        category.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify(CategorySerializer.serialize(category))

@bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    """Удалить категорию"""
    category = ProductCategory.query.get_or_404(category_id)
    
    # Проверить, есть ли поставщики
    if category.suppliers.count() > 0:
        return jsonify({'error': 'Нельзя удалить категорию с поставщиками'}), 400
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'message': 'Категория удалена'}), 200

# ========== ПОСТАВЩИКИ ==========

@bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    """Получить список поставщиков"""
    category_id = request.args.get('category_id', type=int)
    include_subcategories = request.args.get('include_subcategories', 'false').lower() == 'true'
    
    query = Supplier.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    suppliers = query.all()
    return jsonify([SupplierSerializer.serialize(sup, include_subcategories=include_subcategories) for sup in suppliers])

@bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """Получить поставщика по ID"""
    supplier = Supplier.query.get_or_404(supplier_id)
    include_subcategories = request.args.get('include_subcategories', 'false').lower() == 'true'
    return jsonify(SupplierSerializer.serialize(supplier, include_subcategories=include_subcategories))

@bp.route('/suppliers', methods=['POST'])
@login_required
def create_supplier():
    """Создать поставщика"""
    data = request.get_json()
    
    if not data or not data.get('code') or not data.get('name') or not data.get('category_id'):
        return jsonify({'error': 'Необходимо указать code, name и category_id'}), 400
    
    # Проверить существование категории
    category = ProductCategory.query.get(data['category_id'])
    if not category:
        return jsonify({'error': 'Категория не найдена'}), 404
    
    # Проверить уникальность кода в категории
    if Supplier.query.filter_by(code=data['code'], category_id=data['category_id']).first():
        return jsonify({'error': 'Поставщик с таким кодом уже существует в этой категории'}), 400
    
    supplier = Supplier(
        code=data['code'],
        name=data['name'],
        category_id=data['category_id'],
        contact_person=data.get('contact_person'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(supplier)
    db.session.commit()
    
    return jsonify(SupplierSerializer.serialize(supplier)), 201

@bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
@login_required
def update_supplier(supplier_id):
    """Обновить поставщика"""
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Необходимо передать данные'}), 400
    
    if 'name' in data:
        supplier.name = data['name']
    if 'contact_person' in data:
        supplier.contact_person = data['contact_person']
    if 'email' in data:
        supplier.email = data['email']
    if 'phone' in data:
        supplier.phone = data['phone']
    if 'address' in data:
        supplier.address = data['address']
    if 'is_active' in data:
        supplier.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify(SupplierSerializer.serialize(supplier))

@bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
@login_required
def delete_supplier(supplier_id):
    """Удалить поставщика"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Проверить, есть ли подкатегории
    if supplier.subcategories.count() > 0:
        return jsonify({'error': 'Нельзя удалить поставщика с подкатегориями'}), 400
    
    db.session.delete(supplier)
    db.session.commit()
    
    return jsonify({'message': 'Поставщик удален'}), 200

# ========== ПОДКАТЕГОРИИ ==========

@bp.route('/subcategories', methods=['GET'])
def get_subcategories():
    """Получить список подкатегорий"""
    supplier_id = request.args.get('supplier_id', type=int)
    include_attributes = request.args.get('include_attributes', 'false').lower() == 'true'
    include_products = request.args.get('include_products', 'false').lower() == 'true'
    
    query = Subcategory.query
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    
    subcategories = query.all()
    return jsonify([SubcategorySerializer.serialize(sub, include_attributes=include_attributes, include_products=include_products) for sub in subcategories])

@bp.route('/subcategories/<int:subcategory_id>', methods=['GET'])
def get_subcategory(subcategory_id):
    """Получить подкатегорию по ID"""
    subcategory = Subcategory.query.get_or_404(subcategory_id)
    include_attributes = request.args.get('include_attributes', 'false').lower() == 'true'
    include_products = request.args.get('include_products', 'false').lower() == 'true'
    return jsonify(SubcategorySerializer.serialize(subcategory, include_attributes=include_attributes, include_products=include_products))

@bp.route('/subcategories', methods=['POST'])
@login_required
def create_subcategory():
    """Создать подкатегорию"""
    data = request.get_json()
    
    if not data or not data.get('code') or not data.get('name') or not data.get('supplier_id'):
        return jsonify({'error': 'Необходимо указать code, name и supplier_id'}), 400
    
    # Проверить существование поставщика
    supplier = Supplier.query.get(data['supplier_id'])
    if not supplier:
        return jsonify({'error': 'Поставщик не найден'}), 404
    
    # Проверить уникальность кода у поставщика
    if Subcategory.query.filter_by(code=data['code'], supplier_id=data['supplier_id']).first():
        return jsonify({'error': 'Подкатегория с таким кодом уже существует у этого поставщика'}), 400
    
    subcategory = Subcategory(
        code=data['code'],
        name=data['name'],
        supplier_id=data['supplier_id'],
        description=data.get('description'),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(subcategory)
    db.session.commit()
    
    return jsonify(SubcategorySerializer.serialize(subcategory)), 201

@bp.route('/subcategories/<int:subcategory_id>', methods=['PUT'])
@login_required
def update_subcategory(subcategory_id):
    """Обновить подкатегорию"""
    subcategory = Subcategory.query.get_or_404(subcategory_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Необходимо передать данные'}), 400
    
    if 'name' in data:
        subcategory.name = data['name']
    if 'description' in data:
        subcategory.description = data['description']
    if 'is_active' in data:
        subcategory.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify(SubcategorySerializer.serialize(subcategory))

@bp.route('/subcategories/<int:subcategory_id>', methods=['DELETE'])
@login_required
def delete_subcategory(subcategory_id):
    """Удалить подкатегорию"""
    subcategory = Subcategory.query.get_or_404(subcategory_id)
    
    # Проверить, есть ли товары
    if subcategory.products.count() > 0:
        return jsonify({'error': 'Нельзя удалить подкатегорию с товарами'}), 400
    
    db.session.delete(subcategory)
    db.session.commit()
    
    return jsonify({'message': 'Подкатегория удалена'}), 200

# ========== ТОВАРЫ ==========

@bp.route('/products', methods=['GET'])
def get_products():
    """Получить список товаров"""
    subcategory_id = request.args.get('subcategory_id', type=int)
    status = request.args.get('status')
    include_attributes = request.args.get('include_attributes', 'false').lower() == 'true'
    include_verification = request.args.get('include_verification', 'false').lower() == 'true'
    
    query = Product.query
    if subcategory_id:
        query = query.filter_by(subcategory_id=subcategory_id)
    if status:
        try:
            query = query.filter_by(status=ProductStatus[status.upper()])
        except KeyError:
            pass
    
    products = query.all()
    return jsonify([ProductSerializer.serialize(prod, include_attributes=include_attributes, include_verification=include_verification) for prod in products])

@bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Получить товар по ID"""
    product = Product.query.get_or_404(product_id)
    include_attributes = request.args.get('include_attributes', 'true').lower() == 'true'
    include_verification = request.args.get('include_verification', 'true').lower() == 'true'
    include_history = request.args.get('include_history', 'false').lower() == 'true'
    return jsonify(ProductSerializer.serialize(product, include_attributes=include_attributes, include_verification=include_verification, include_history=include_history))

@bp.route('/products/<int:product_id>/verify', methods=['POST'])
@login_required
def verify_product(product_id):
    """Запустить верификацию товара"""
    product = Product.query.get_or_404(product_id)
    
    try:
        verification = VerificationService.verify_product(product, current_user)
        return jsonify(VerificationSerializer.serialize(verification, include_issues=True)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/products/<int:product_id>/status', methods=['PUT'])
@login_required
def update_product_status(product_id):
    """Изменить статус товара"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if not data or not data.get('status'):
        return jsonify({'error': 'Необходимо указать status'}), 400
    
    try:
        new_status = ProductStatus[data['status'].upper()]
    except KeyError:
        return jsonify({'error': f'Неверный статус: {data["status"]}'}), 400
    
    old_status = product.status
    comment = data.get('comment', '')
    
    # Изменить статус
    product.status = new_status
    
    # Записать в историю
    history = ProductStatusHistory(
        product_id=product.id,
        old_status=old_status.value,
        new_status=new_status.value,
        changed_by_id=current_user.id,
        comment=comment
    )
    db.session.add(history)
    db.session.commit()
    
    return jsonify(ProductSerializer.serialize(product)), 200

@bp.route('/products/<int:product_id>/versions', methods=['GET'])
def get_product_versions(product_id):
    """Получить версии товара"""
    product = Product.query.get_or_404(product_id)
    versions = ProductVersion.query.filter_by(product_id=product_id).order_by(ProductVersion.version_number.desc()).all()
    return jsonify([v.to_dict() for v in versions])

@bp.route('/products/<int:product_id>/versions', methods=['POST'])
@login_required
def create_product_version(product_id):
    """Создать версию товара"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    comment = data.get('comment') if data else None
    version = PV.create_version(product, current_user, comment)
    db.session.commit()
    
    return jsonify(version.to_dict()), 201

# ========== АТРИБУТЫ ==========

@bp.route('/attributes', methods=['GET'])
def get_attributes():
    """Получить список атрибутов"""
    include_values = request.args.get('include_values', 'false').lower() == 'true'
    attributes = Attribute.query.all()
    return jsonify([AttributeSerializer.serialize(attr, include_values=include_values) for attr in attributes])

@bp.route('/attributes/<int:attribute_id>', methods=['GET'])
def get_attribute(attribute_id):
    """Получить атрибут по ID"""
    attribute = Attribute.query.get_or_404(attribute_id)
    include_values = request.args.get('include_values', 'true').lower() == 'true'
    return jsonify(AttributeSerializer.serialize(attribute, include_values=include_values))

@bp.route('/attributes', methods=['POST'])
@login_required
def create_attribute():
    """Создать атрибут"""
    from app.utils.attribute_mapper import generate_attribute_code_from_name
    
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('type'):
        return jsonify({'error': 'Необходимо указать name и type'}), 400
    
    # Автоматическая генерация кода из названия, если не указан
    code = data.get('code')
    if not code or code.strip() == '':
        code = generate_attribute_code_from_name(data['name'])
    
    # Проверить уникальность кода
    if Attribute.query.filter_by(code=code).first():
        return jsonify({'error': 'Атрибут с таким кодом уже существует'}), 400
    
    # Проверить уникальность названия
    if Attribute.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Атрибут с таким названием уже существует'}), 400
    
    from app.models.attribute import AttributeType
    try:
        attr_type = AttributeType[data['type'].upper()]
    except KeyError:
        return jsonify({'error': f'Неверный тип атрибута: {data["type"]}'}), 400
    
    attribute = Attribute(
        code=data['code'],
        name=data['name'],
        type=attr_type,
        description=data.get('description'),
        unit=data.get('unit'),
        is_unique=data.get('is_unique', False),
        validation_rules=data.get('validation_rules')
    )
    
    db.session.add(attribute)
    db.session.commit()
    
    return jsonify(AttributeSerializer.serialize(attribute)), 201

@bp.route('/attributes/<int:attribute_id>', methods=['PUT'])
@login_required
def update_attribute(attribute_id):
    """Обновить атрибут"""
    attribute = Attribute.query.get_or_404(attribute_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Необходимо передать данные'}), 400
    
    if 'name' in data:
        attribute.name = data['name']
    if 'description' in data:
        attribute.description = data['description']
    if 'unit' in data:
        attribute.unit = data['unit']
    if 'is_unique' in data:
        attribute.is_unique = data['is_unique']
    if 'validation_rules' in data:
        attribute.validation_rules = data['validation_rules']
    
    db.session.commit()
    
    return jsonify(AttributeSerializer.serialize(attribute))

@bp.route('/attributes/<int:attribute_id>', methods=['DELETE'])
@login_required
def delete_attribute(attribute_id):
    """Удалить атрибут"""
    attribute = Attribute.query.get_or_404(attribute_id)
    
    # Проверить использование
    if attribute.subcategory_attributes.count() > 0:
        return jsonify({'error': 'Атрибут используется в подкатегориях'}), 400
    
    db.session.delete(attribute)
    db.session.commit()
    
    return jsonify({'message': 'Атрибут удален'}), 200

