"""
Главные маршруты
"""
from flask import render_template, redirect, url_for, request, flash, jsonify, send_from_directory, abort
from flask_login import login_required, current_user
from app.main import bp
from app import db
from app.models.category import ProductCategory
from app.models.supplier import Supplier
from app.models.subcategory import Subcategory
from app.models.product import Product, ProductStatus
from app.models.attribute import Attribute
from app.models.verification import ProductVerification
from app.models.workflow import ProductStatusHistory
from app.models.version import ProductVersion
from app.forms.category_form import CategoryForm
from app.forms.supplier_form import SupplierForm
from app.forms.subcategory_form import SubcategoryForm
from app.services.verification_service import VerificationService
from sqlalchemy import func
from datetime import datetime, timedelta

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    """Главная страница с дашбордом"""
    from app.models.import_history import ImportHistory
    from app.models.verification import ProductVerification
    
    # Базовая статистика
    stats = {
        'categories_count': ProductCategory.query.count(),
        'suppliers_count': Supplier.query.count(),
        'subcategories_count': Subcategory.query.count(),
        'products_count': Product.query.count(),
    }
    
    # Статистика по статусам товаров
    status_stats = {}
    for status in ProductStatus:
        status_stats[status.value] = Product.query.filter_by(status=status).count()
    
    # Статистика верификации
    verification_stats = db.session.query(
        func.avg(ProductVerification.overall_score).label('avg_score'),
        func.count(ProductVerification.id).label('total_verifications')
    ).first()
    
    avg_score = round(verification_stats.avg_score, 1) if verification_stats.avg_score else 0
    total_verifications = verification_stats.total_verifications or 0
    
    # Получить категории с детальной статистикой
    categories_data = []
    for category in ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all():
        # Статистика по категории
        # subcategories - это список, а не Query, поэтому фильтруем вручную
        subcategories = [s for s in category.subcategories if s.is_active]
        # suppliers - это тоже список через many-to-many
        suppliers = [s for s in category.suppliers if s.is_active]
        
        # Подсчет товаров по категории
        products_in_category = Product.query.join(Subcategory).filter(
            Subcategory.category_id == category.id
        ).all()
        
        products_count = len(products_in_category)
        products_by_status = {}
        for status in ProductStatus:
            products_by_status[status.value] = len([p for p in products_in_category if p.status == status])
        
        # Средняя оценка верификации по категории
        category_verifications = ProductVerification.query.join(Product).join(Subcategory).filter(
            Subcategory.category_id == category.id
        ).all()
        category_avg_score = 0
        if category_verifications:
            category_avg_score = round(sum(v.overall_score for v in category_verifications) / len(category_verifications), 1)
        
        # Данные по поставщикам в категории
        suppliers_data = []
        for supplier in suppliers:
            try:
                # Подкатегории поставщика в этой категории (через many-to-many связь)
                # Получаем все подкатегории поставщика и фильтруем по категории
                # supplier.subcategories может быть списком или Query объектом
                if hasattr(supplier.subcategories, 'filter_by'):
                    # Это Query объект (lazy='dynamic')
                    supplier_subcategories_all = supplier.subcategories.filter_by(is_active=True).all()
                else:
                    # Это список (InstrumentedList)
                    supplier_subcategories_all = [s for s in supplier.subcategories if s.is_active]
                supplier_subcategories = [s for s in supplier_subcategories_all if s.category_id == category.id]
                
                if not supplier_subcategories:
                    continue  # Пропустить поставщика без подкатегорий в этой категории
                
                # Товары поставщика через подкатегории
                subcategory_ids = [s.id for s in supplier_subcategories]
                if not subcategory_ids:
                    continue
                    
                supplier_products = Product.query.join(Subcategory).filter(
                    Subcategory.id.in_(subcategory_ids)
                ).all()
                
                supplier_products_count = len(supplier_products)
                supplier_products_by_status = {}
                for status in ProductStatus:
                    supplier_products_by_status[status.value] = len([p for p in supplier_products if p.status == status])
                
                # Средняя оценка верификации по поставщику
                supplier_verifications = ProductVerification.query.join(Product).filter(
                    Product.id.in_([p.id for p in supplier_products])
                ).all()
                supplier_avg_score = 0
                if supplier_verifications:
                    supplier_avg_score = round(sum(v.overall_score for v in supplier_verifications) / len(supplier_verifications), 1)
                
                # Последний импорт поставщика
                last_import = None
                try:
                    last_import = ImportHistory.query.join(Subcategory).filter(
                        Subcategory.id.in_(subcategory_ids)
                    ).order_by(ImportHistory.imported_at.desc()).first()
                except Exception:
                    pass
                
                # Файлы для валидации (история импортов)
                import_files = []
                try:
                    import_files = ImportHistory.query.join(Subcategory).filter(
                        Subcategory.id.in_(subcategory_ids)
                    ).order_by(ImportHistory.imported_at.desc()).limit(10).all()
                except Exception:
                    pass
                
                # Подкатегории с детальной статистикой
                subcategories_data = []
                for subcat in supplier_subcategories:
                    subcat_products = [p for p in supplier_products if p.subcategory_id == subcat.id]
                    subcat_products_count = len(subcat_products)
                    subcat_products_by_status = {}
                    for status in ProductStatus:
                        subcat_products_by_status[status.value] = len([p for p in subcat_products if p.status == status])
                    
                    # Наполнение подкатегории (количество загруженных товаров)
                    # Это просто количество товаров в подкатегории
                    subcat_fill_count = subcat_products_count
                    
                    # Товары из файлов, которые еще не загружены
                    # Считаем из истории импортов: total_rows - imported_count
                    subcat_not_loaded = 0
                    try:
                        subcat_imports = ImportHistory.query.filter_by(subcategory_id=subcat.id).all()
                        subcat_not_loaded = sum(max(0, imp.total_rows - imp.imported_count) for imp in subcat_imports)
                    except Exception:
                        pass
                    
                    subcategories_data.append({
                        'subcategory': subcat,
                        'products_count': subcat_products_count,
                        'products_by_status': subcat_products_by_status,
                        'fill_count': subcat_fill_count,  # Загружено в БД
                        'not_loaded_count': subcat_not_loaded,  # Еще не загружено из файлов
                    })
                
                suppliers_data.append({
                    'supplier': supplier,
                    'subcategories': subcategories_data,
                    'products_count': supplier_products_count,
                    'products_by_status': supplier_products_by_status,
                    'avg_score': supplier_avg_score,
                    'last_import': last_import,
                    'import_files': import_files,
                })
            except Exception as e:
                # Логируем ошибку, но продолжаем обработку других поставщиков
                import traceback
                print(f"Ошибка при обработке поставщика {supplier.id}: {str(e)}")
                print(traceback.format_exc())
                continue
        
        categories_data.append({
            'category': category,
            'subcategories_count': len(subcategories),
            'suppliers_count': len(suppliers),
            'products_count': products_count,
            'products_by_status': products_by_status,
            'avg_score': category_avg_score,
            'suppliers': suppliers_data,
        })
    
    # Последние импорты (для отдельного блока)
    recent_imports = ImportHistory.query.order_by(ImportHistory.imported_at.desc()).limit(10).all()
    
    # Товары на проверке
    products_to_review = Product.query.filter_by(status=ProductStatus.TO_REVIEW).limit(5).all()
    
    return render_template('main/index.html', 
                         stats=stats,
                         status_stats=status_stats,
                         avg_score=avg_score,
                         total_verifications=total_verifications,
                         categories_data=categories_data,
                         recent_imports=recent_imports,
                         products_to_review=products_to_review)

@bp.route('/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    """API для статистики дашборда"""
    # Статистика по статусам
    status_data = {}
    for status in ProductStatus:
        status_data[status.value] = Product.query.filter_by(status=status).count()
    
    # Статистика по дням (последние 7 дней)
    daily_stats = []
    for i in range(6, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        count = Product.query.filter(
            func.date(Product.created_at) == date.date()
        ).count()
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Топ подкатегорий по количеству товаров
    top_subcategories = db.session.query(
        Subcategory.name,
        func.count(Product.id).label('products_count')
    ).join(Product).group_by(Subcategory.id).order_by(
        func.count(Product.id).desc()
    ).limit(5).all()
    
    return jsonify({
        'status_data': status_data,
        'daily_stats': daily_stats,
        'top_subcategories': [{'name': name, 'count': count} for name, count in top_subcategories]
    })

@bp.route('/categories')
@login_required
def categories():
    """Список категорий"""
    search = request.args.get('search', '')
    query = ProductCategory.query
    
    if search:
        query = query.filter(
            (ProductCategory.name.ilike(f'%{search}%')) |
            (ProductCategory.code.ilike(f'%{search}%'))
        )
    
    categories_list = query.order_by(ProductCategory.name).all()
    return render_template('main/categories.html', categories=categories_list, search=search)

@bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
def new_category():
    """Создать новую категорию"""
    from app.utils.code_generator import generate_category_code
    
    form = CategoryForm()
    if form.validate_on_submit():
        # Автоматическая генерация кода, если не указан
        code = form.code.data
        if not code or code.strip() == '':
            code = generate_category_code()
        
        # Проверить уникальность кода
        if ProductCategory.query.filter_by(code=code).first():
            flash('Категория с таким кодом уже существует', 'error')
            return render_template('main/category_form.html', form=form, title='Создать категорию')
        
        category = ProductCategory(
            code=code,
            name=form.name.data,
            description=form.description.data,
            is_active=form.is_active.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Категория успешно создана', 'success')
        return redirect(url_for('main.categories'))
    
    # Автоматически заполнить код при открытии формы
    if not form.code.data:
        form.code.data = generate_category_code()
    
    return render_template('main/category_form.html', form=form, title='Создать категорию')

@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Редактировать категорию"""
    category = ProductCategory.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        # Проверить уникальность кода (если изменился)
        if form.code.data != category.code:
            if ProductCategory.query.filter_by(code=form.code.data).first():
                flash('Категория с таким кодом уже существует', 'error')
                return render_template('main/category_form.html', form=form, title='Редактировать категорию', category=category)
        
        category.code = form.code.data
        category.name = form.name.data
        category.description = form.description.data
        category.is_active = form.is_active.data
        
        db.session.commit()
        flash('Категория успешно обновлена', 'success')
        return redirect(url_for('main.categories'))
    
    return render_template('main/category_form.html', form=form, title='Редактировать категорию', category=category)

@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """Удалить категорию"""
    category = ProductCategory.query.get_or_404(category_id)
    
    if category.suppliers.count() > 0:
        flash('Нельзя удалить категорию с поставщиками', 'error')
        return redirect(url_for('main.categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Категория успешно удалена', 'success')
    return redirect(url_for('main.categories'))

@bp.route('/suppliers')
@login_required
def suppliers():
    """Список поставщиков"""
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    query = Supplier.query
    
    if category_id:
        # Фильтрация по категории через many-to-many связь
        query = query.join(Supplier.categories).filter(ProductCategory.id == category_id)
    
    if search:
        query = query.filter(
            (Supplier.name.ilike(f'%{search}%')) |
            (Supplier.code.ilike(f'%{search}%')) |
            (Supplier.email.ilike(f'%{search}%'))
        )
    
    suppliers_list = query.order_by(Supplier.name).all()
    categories = ProductCategory.query.order_by(ProductCategory.name).all()
    
    return render_template('main/suppliers.html', 
                         suppliers=suppliers_list, 
                         categories=categories,
                         selected_category_id=category_id,
                         search=search)

@bp.route('/suppliers/new', methods=['GET', 'POST'])
@login_required
def new_supplier():
    """Создать нового поставщика"""
    form = SupplierForm()
    if form.validate_on_submit():
        # Проверить уникальность кода
        if Supplier.query.filter_by(code=form.code.data).first():
            flash('Поставщик с таким кодом уже существует', 'error')
            return render_template('main/supplier_form.html', form=form, title='Создать поставщика')
        
        supplier = Supplier(
            code=form.code.data,
            name=form.name.data,
            contact_person=form.contact_person.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            is_active=form.is_active.data
        )
        db.session.add(supplier)
        
        # Привязать категории
        from app.models.category import ProductCategory
        for category_id in form.category_ids.data:
            category = ProductCategory.query.get(category_id)
            if category:
                supplier.categories.append(category)
        
        # Привязать подкатегории
        from app.models.subcategory import Subcategory
        for subcategory_id in form.subcategory_ids.data:
            subcategory = Subcategory.query.get(subcategory_id)
            if subcategory:
                supplier.subcategories.append(subcategory)
        
        db.session.commit()
        flash('Поставщик успешно создан', 'success')
        return redirect(url_for('main.suppliers'))
    
    return render_template('main/supplier_form.html', form=form, title='Создать поставщика')

@bp.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    """Редактировать поставщика"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=supplier)
    
    # Заполнить выбранные категории и подкатегории
    if request.method == 'GET':
        form.category_ids.data = [c.id for c in supplier.categories.all()]
        form.subcategory_ids.data = [s.id for s in supplier.subcategories.all()]
    
    if form.validate_on_submit():
        # Проверить уникальность кода (если изменился)
        if form.code.data != supplier.code:
            if Supplier.query.filter_by(code=form.code.data).first():
                flash('Поставщик с таким кодом уже существует', 'error')
                return render_template('main/supplier_form.html', form=form, title='Редактировать поставщика', supplier=supplier)
        
        supplier.code = form.code.data
        supplier.name = form.name.data
        supplier.contact_person = form.contact_person.data
        supplier.email = form.email.data
        supplier.phone = form.phone.data
        supplier.address = form.address.data
        supplier.is_active = form.is_active.data
        
        # Обновить связи с категориями
        supplier.categories = []
        from app.models.category import ProductCategory
        for category_id in form.category_ids.data:
            category = ProductCategory.query.get(category_id)
            if category:
                supplier.categories.append(category)
        
        # Обновить связи с подкатегориями
        supplier.subcategories = []
        from app.models.subcategory import Subcategory
        for subcategory_id in form.subcategory_ids.data:
            subcategory = Subcategory.query.get(subcategory_id)
            if subcategory:
                supplier.subcategories.append(subcategory)
        
        db.session.commit()
        flash('Поставщик успешно обновлен', 'success')
        return redirect(url_for('main.suppliers'))
    
    return render_template('main/supplier_form.html', form=form, title='Редактировать поставщика', supplier=supplier)

@bp.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    """Удалить поставщика"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Проверить, есть ли товары у поставщика через подкатегории
    from app.models.product import Product
    products_count = Product.query.join(Subcategory).filter(
        Subcategory.suppliers.contains(supplier)
    ).count()
    
    if products_count > 0:
        flash('Нельзя удалить поставщика, у которого есть товары', 'error')
        return redirect(url_for('main.suppliers'))
    
    db.session.delete(supplier)
    db.session.commit()
    flash('Поставщик успешно удален', 'success')
    return redirect(url_for('main.suppliers'))

@bp.route('/subcategories')
@login_required
def subcategories():
    """Список подкатегорий"""
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    query = Subcategory.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(
            (Subcategory.name.ilike(f'%{search}%')) |
            (Subcategory.code.ilike(f'%{search}%'))
        )
    
    subcategories_list = query.order_by(Subcategory.name).all()
    categories = ProductCategory.query.order_by(ProductCategory.name).all()
    
    return render_template('main/subcategories.html',
                          subcategories=subcategories_list,
                          categories=categories,
                          selected_category_id=category_id,
                          search=search)

@bp.route('/subcategories/new', methods=['GET', 'POST'])
@login_required
def new_subcategory():
    """Создать новую подкатегорию"""
    from app.utils.code_generator import generate_subcategory_code
    
    form = SubcategoryForm()
    if form.validate_on_submit():
        # Автоматическая генерация кода, если не указан
        code = form.code.data
        if not code or code.strip() == '':
            if form.category_id.data:
                try:
                    code = generate_subcategory_code(form.category_id.data)
                except ValueError as e:
                    flash(str(e), 'error')
                    return render_template('main/subcategory_form.html', form=form, title='Создать подкатегорию')
            else:
                flash('Необходимо выбрать категорию для автоматической генерации кода', 'error')
                return render_template('main/subcategory_form.html', form=form, title='Создать подкатегорию')
        
        # Проверить уникальность кода в категории
        if Subcategory.query.filter_by(code=code, category_id=form.category_id.data).first():
            flash('Подкатегория с таким кодом уже существует в этой категории', 'error')
            return render_template('main/subcategory_form.html', form=form, title='Создать подкатегорию')
        
        subcategory = Subcategory(
            code=code,
            name=form.name.data,
            category_id=form.category_id.data,
            description=form.description.data,
            is_active=form.is_active.data
        )
        db.session.add(subcategory)
        db.session.commit()
        flash('Подкатегория успешно создана', 'success')
        return redirect(url_for('main.subcategories'))
    
    return render_template('main/subcategory_form.html', form=form, title='Создать подкатегорию')

@bp.route('/subcategories/<int:subcategory_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subcategory(subcategory_id):
    """Редактировать подкатегорию"""
    subcategory = Subcategory.query.get_or_404(subcategory_id)
    form = SubcategoryForm(obj=subcategory)
    
    if form.validate_on_submit():
        # Проверить уникальность кода (если изменился)
        if form.code.data != subcategory.code or form.category_id.data != subcategory.category_id:
            if Subcategory.query.filter_by(code=form.code.data, category_id=form.category_id.data).first():
                flash('Подкатегория с таким кодом уже существует в этой категории', 'error')
                return render_template('main/subcategory_form.html', form=form, title='Редактировать подкатегорию', subcategory=subcategory)
        
        subcategory.code = form.code.data
        subcategory.name = form.name.data
        subcategory.category_id = form.category_id.data
        subcategory.description = form.description.data
        subcategory.is_active = form.is_active.data
        
        db.session.commit()
        flash('Подкатегория успешно обновлена', 'success')
        return redirect(url_for('main.subcategories'))
    
    return render_template('main/subcategory_form.html', form=form, title='Редактировать подкатегорию', subcategory=subcategory)

@bp.route('/subcategories/<int:subcategory_id>/delete', methods=['POST'])
@login_required
def delete_subcategory(subcategory_id):
    """Удалить подкатегорию"""
    subcategory = Subcategory.query.get_or_404(subcategory_id)
    
    if subcategory.products.count() > 0:
        flash('Нельзя удалить подкатегорию с товарами', 'error')
        return redirect(url_for('main.subcategories'))
    
    db.session.delete(subcategory)
    db.session.commit()
    flash('Подкатегория успешно удалена', 'success')
    return redirect(url_for('main.subcategories'))

@bp.route('/subcategories/<int:subcategory_id>/attributes', methods=['GET', 'POST'])
@login_required
def manage_subcategory_attributes(subcategory_id):
    """Управление эталонными атрибутами подкатегории"""
    subcategory = Subcategory.query.get_or_404(subcategory_id)
    
    if request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        attribute_id = data.get('attribute_id')
        
        if action == 'add':
            # Добавить атрибут
            from app.models.subcategory_attribute import SubcategoryAttribute
            existing = SubcategoryAttribute.query.filter_by(
                subcategory_id=subcategory_id,
                attribute_id=attribute_id
            ).first()
            
            if not existing:
                subcat_attr = SubcategoryAttribute(
                    subcategory_id=subcategory_id,
                    attribute_id=attribute_id,
                    is_required=data.get('is_required', False),
                    sort_order=data.get('sort_order', 0)
                )
                db.session.add(subcat_attr)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Атрибут добавлен'})
            else:
                return jsonify({'success': False, 'message': 'Атрибут уже добавлен'}), 400
        
        elif action == 'remove':
            # Удалить атрибут
            from app.models.subcategory_attribute import SubcategoryAttribute
            subcat_attr = SubcategoryAttribute.query.filter_by(
                subcategory_id=subcategory_id,
                attribute_id=attribute_id
            ).first()
            
            if subcat_attr:
                db.session.delete(subcat_attr)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Атрибут удален'})
            else:
                return jsonify({'success': False, 'message': 'Атрибут не найден'}), 404
        
        elif action == 'update':
            # Обновить атрибут
            from app.models.subcategory_attribute import SubcategoryAttribute
            subcat_attr = SubcategoryAttribute.query.filter_by(
                subcategory_id=subcategory_id,
                attribute_id=attribute_id
            ).first()
            
            if subcat_attr:
                if 'is_required' in data:
                    subcat_attr.is_required = data['is_required']
                if 'sort_order' in data:
                    subcat_attr.sort_order = data['sort_order']
                db.session.commit()
                return jsonify({'success': True, 'message': 'Атрибут обновлен'})
            else:
                return jsonify({'success': False, 'message': 'Атрибут не найден'}), 404
    
    # GET - показать страницу управления
    all_attributes = Attribute.query.order_by(Attribute.name).all()
    subcategory_attributes = subcategory.get_all_attributes()
    
    return render_template('main/subcategory_attributes.html',
                         subcategory=subcategory,
                         all_attributes=all_attributes,
                         subcategory_attributes=subcategory_attributes)

@bp.route('/products')
@login_required
def products():
    """Список товаров"""
    subcategory_id = request.args.get('subcategory_id', type=int)
    status = request.args.get('status')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Product.query
    
    if subcategory_id:
        query = query.filter_by(subcategory_id=subcategory_id)
    
    if status:
        try:
            query = query.filter_by(status=ProductStatus[status.upper()])
        except KeyError:
            pass
    
    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.sku.ilike(f'%{search}%'))
        )
    
    # Пагинация
    from config import Config
    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page,
        per_page=Config.ITEMS_PER_PAGE,
        error_out=False
    )
    
    subcategories = Subcategory.query.order_by(Subcategory.name).all()
    statuses = [s.value for s in ProductStatus]
    
    return render_template('main/products.html',
                         products=pagination.items,
                         pagination=pagination,
                         subcategories=subcategories,
                         statuses=statuses,
                         selected_subcategory_id=subcategory_id,
                         selected_status=status,
                         search=search)

@bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    """Детали товара"""
    product = Product.query.get_or_404(product_id)
    
    # Получить медиа-файлы товара
    from app.models.product_media import ProductMedia, MediaType
    images = ProductMedia.query.filter_by(
        product_id=product.id,
        media_type=MediaType.IMAGE
    ).order_by(ProductMedia.sort_order).all()
    
    models_3d = ProductMedia.query.filter_by(
        product_id=product.id,
        media_type=MediaType.THREE_D_MODEL
    ).order_by(ProductMedia.sort_order).all()
    
    # Получить последнюю верификацию
    from app.models.verification import ProductVerification
    latest_verification = ProductVerification.query.filter_by(
        product_id=product.id
    ).order_by(ProductVerification.verified_at.desc()).first()
    
    # Получить последнюю версию
    from app.models.version import ProductVersion
    latest_version = ProductVersion.query.filter_by(
        product_id=product.id
    ).order_by(ProductVersion.version_number.desc()).first()
    
    # Получить все версии
    all_versions = ProductVersion.query.filter_by(
        product_id=product.id
    ).order_by(ProductVersion.version_number.desc()).all()
    
    return render_template('main/product_detail.html',
                         product=product,
                         verification=latest_verification,
                         latest_version=latest_version,
                         all_versions=all_versions,
                         images=images,
                         models_3d=models_3d)

@bp.route('/products/<int:product_id>/verify', methods=['POST'])
@login_required
def verify_product(product_id):
    """Запустить верификацию товара"""
    product = Product.query.get_or_404(product_id)
    
    try:
        verification = VerificationService.verify_product(product, current_user)
        flash(f'Верификация завершена. Оценка: {verification.overall_score}%', 'success')
    except Exception as e:
        flash(f'Ошибка при верификации: {str(e)}', 'error')
    
    return redirect(url_for('main.product_detail', product_id=product_id))

@bp.route('/products/<int:product_id>/status', methods=['POST'])
@login_required
def change_product_status(product_id):
    """Изменить статус товара"""
    product = Product.query.get_or_404(product_id)
    new_status_str = request.form.get('status')
    comment = request.form.get('comment', '')
    
    try:
        new_status = ProductStatus[new_status_str.upper()]
    except KeyError:
        flash('Неверный статус', 'error')
        return redirect(url_for('main.product_detail', product_id=product_id))
    
    old_status = product.status
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
    
    # Перевод статусов для сообщения
    status_names = {
        'draft': 'Черновик',
        'in_progress': 'В работе',
        'to_review': 'На проверке',
        'approved': 'Утвержден',
        'rejected': 'Отклонен',
        'exported': 'Экспортирован'
    }
    flash(f'Статус изменен: {status_names.get(old_status.value, old_status.value)} → {status_names.get(new_status.value, new_status.value)}', 'success')
    return redirect(url_for('main.product_detail', product_id=product_id))

@bp.route('/attributes')
@login_required
def attributes():
    """Список атрибутов"""
    search = request.args.get('search', '')
    attr_type = request.args.get('type', '')
    
    query = Attribute.query
    
    if search:
        query = query.filter(
            (Attribute.name.ilike(f'%{search}%')) |
            (Attribute.code.ilike(f'%{search}%'))
        )
    
    if attr_type:
        from app.models.attribute import AttributeType
        try:
            query = query.filter_by(type=AttributeType[attr_type.upper()])
        except KeyError:
            pass
    
    attributes_list = query.order_by(Attribute.name).all()
    
    from app.models.attribute import AttributeType
    types = [t.value for t in AttributeType]
    
    return render_template('main/attributes.html',
                         attributes=attributes_list,
                         search=search,
                         selected_type=attr_type,
                         types=types)

@bp.route('/attributes/import', methods=['GET', 'POST'])
@login_required
def import_attributes():
    """Импорт атрибутов из файла"""
    from app.services.attribute_import_service import AttributeImportService
    from werkzeug.utils import secure_filename
    import os
    from config import Config
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не выбран', 'error')
            return redirect(url_for('main.import_attributes'))
        
        file = request.files['file']
        if file.filename == '':
            flash('Файл не выбран', 'error')
            return redirect(url_for('main.import_attributes'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            file.save(filepath)
            
            try:
                result = AttributeImportService.import_from_file(filepath)
                
                # Удалить файл после импорта
                try:
                    os.remove(filepath)
                except:
                    pass
                
                # Показать результаты
                if result['imported'] > 0:
                    flash(f'✅ Успешно импортировано атрибутов: {result["imported"]}', 'success')
                if result['updated'] > 0:
                    flash(f'✅ Обновлено атрибутов: {result["updated"]}', 'success')
                
                if result['errors']:
                    for error in result['errors'][:10]:
                        flash(f'❌ {error}', 'error')
                
                if result['warnings']:
                    for warning in result['warnings'][:10]:
                        flash(f'⚠️ {warning}', 'warning')
                
                return redirect(url_for('main.attributes'))
                
            except Exception as e:
                try:
                    os.remove(filepath)
                except:
                    pass
                flash(f'❌ Ошибка при импорте: {str(e)}', 'error')
                return redirect(url_for('main.import_attributes'))
        else:
            flash('Неверный формат файла', 'error')
    
    return render_template('main/import_attributes.html')

@bp.route('/api/subcategories/generate-code', methods=['GET'])
@login_required
def generate_subcategory_code_api():
    """API для генерации кода подкатегории"""
    from app.utils.code_generator import generate_subcategory_code
    
    category_id = request.args.get('category_id', type=int)
    if not category_id:
        return jsonify({'error': 'Необходимо указать category_id'}), 400
    
    try:
        code = generate_subcategory_code(category_id)
        return jsonify({'code': code})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/media/<path:file_path>')
@login_required
def serve_media(file_path):
    """Отдать медиа-файл"""
    from flask import send_from_directory
    from config import Config
    import os
    
    # Безопасность: проверить, что путь находится в папке media
    full_path = Config.basedir / file_path
    media_folder = Config.basedir / 'media'
    
    try:
        # Проверить, что файл находится внутри папки media
        full_path.resolve().relative_to(media_folder.resolve())
    except ValueError:
        from flask import abort
        abort(403)
    
    if not full_path.exists():
        from flask import abort
        abort(404)
    
    directory = str(full_path.parent)
    filename = full_path.name
    
    return send_from_directory(directory, filename)

@bp.route('/products/<int:product_id>/download-media')
@login_required
def download_product_media(product_id):
    """Скачать медиа-файлы товара"""
    from app.services.media_service import MediaService
    
    product = Product.query.get_or_404(product_id)
    stats = MediaService.process_product_media(product, auto_download=True)
    
    flash(f'Скачано изображений: {stats["images_downloaded"]}, 3D моделей: {stats["models_downloaded"]}', 'success')
    return redirect(url_for('main.product_detail', product_id=product_id))

def allowed_file(filename):
    """Проверить, разрешен ли тип файла"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
