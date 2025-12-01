"""
Главные маршруты
"""
from flask import render_template, redirect, url_for, request, flash, jsonify, send_from_directory, abort, current_app, send_file
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
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timedelta

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    """
    Главная страница с дашбордом и вкладками workflow
    
    Данные загружаются через API endpoints для lazy loading
    Для обратной совместимости передаются пустые значения статистики
    """
    # Получить активную вкладку из параметров
    active_tab = request.args.get('tab', 'data_collection')
    
    # Получить только справочные данные для JavaScript (подкатегории)
    from app.models.subcategory import Subcategory
    all_subcategories = {subcat.id: {'id': subcat.id, 'name': subcat.name, 'code': subcat.code} 
                        for subcat in Subcategory.query.filter_by(is_active=True).all()}
    
    # Пустые значения для обратной совместимости (данные загружаются через API)
    data_collection_stats = {
        'suppliers_count': 0,
        'requests_active': 0,
        'requests_received': 0,
        'requests_pending': 0,
    }
    
    processing_stats = {
        'files_count': 0,
        'total_rows': 0,
    }
    
    catalog_stats = {
        'files_count': 0,
        'products_count': 0,
    }
    
    exported_stats = {
        'files_count': 0,
        'products_count': 0,
    }
    
    # Пустые списки для обратной совместимости
    suppliers_with_requests = []
    data_requests = []
    processing_files = []
    catalog_files = []
    exported_files = []
    categories_data = []
    
    return render_template('main/index.html', 
                         active_tab=active_tab,
                         all_subcategories=all_subcategories,
                         # Для обратной совместимости
                         data_collection_stats=data_collection_stats,
                         processing_stats=processing_stats,
                         catalog_stats=catalog_stats,
                         exported_stats=exported_stats,
                         suppliers_with_requests=suppliers_with_requests,
                         data_requests=data_requests,
                         processing_files=processing_files,
                         catalog_files=catalog_files,
                         exported_files=exported_files,
                         categories_data=categories_data)

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
    
    # Получить поставщиков для каждой категории
    categories_with_suppliers = []
    for category in categories_list:
        suppliers = category.suppliers.filter_by(is_active=True).all()
        categories_with_suppliers.append({
            'category': category,
            'suppliers': suppliers
        })
    
    return render_template('main/categories.html', 
                         categories_data=categories_with_suppliers,
                         categories=categories_list,
                         search=search)

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
    try:
        category = ProductCategory.query.get_or_404(category_id)
        
        # Проверить бизнес-правила из ТЗ: нельзя удалить категорию, если у неё есть подкатегории или поставщики
        if category.subcategories.count() > 0:
            flash('Нельзя удалить категорию с подкатегориями', 'error')
            return redirect(url_for('main.categories'))
        
        if category.suppliers.count() > 0:
            flash('Нельзя удалить категорию с поставщиками', 'error')
            return redirect(url_for('main.categories'))
        
        # Удалить все запросы данных со статусом new или cancelled (согласно ТЗ)
        from app.models.data_request import DataRequest, DataRequestStatus
        data_requests = DataRequest.query.filter_by(category_id=category_id).filter(
            DataRequest.status.in_([DataRequestStatus.NEW, DataRequestStatus.CANCELLED])
        ).all()
        for dr in data_requests:
            db.session.delete(dr)
        
        db.session.delete(category)
        db.session.commit()
        flash('Категория успешно удалена', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при удалении категории {category_id}: {str(e)}", exc_info=True)
        flash('Ошибка при удалении категории', 'error')
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
    from app.utils.code_generator import generate_supplier_code
    
    form = SupplierForm()
    if form.validate_on_submit():
        # Автоматическая генерация кода, если не указан
        code = form.code.data
        if not code or code.strip() == '':
            code = generate_supplier_code()
        
        # Проверить уникальность кода
        if Supplier.query.filter_by(code=code).first():
            flash('Поставщик с таким кодом уже существует', 'error')
            return render_template('main/supplier_form.html', form=form, title='Создать поставщика')
        
        supplier = Supplier(
            code=code,
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
        category_ids = form.category_ids.data if form.category_ids.data else []
        if category_ids and len(category_ids) > 0:
            for category_id in category_ids:
                if category_id:  # Проверить, что ID не None
                    try:
                        category = ProductCategory.query.get(category_id)
                        if category:
                            supplier.categories.append(category)
                    except Exception as e:
                        if current_app.logger:
                            current_app.logger.warning(f'Ошибка при привязке категории {category_id}: {e}')
        
        # Привязать подкатегории
        from app.models.subcategory import Subcategory
        subcategory_ids = form.subcategory_ids.data if form.subcategory_ids.data else []
        if subcategory_ids and len(subcategory_ids) > 0:
            for subcategory_id in subcategory_ids:
                if subcategory_id:  # Проверить, что ID не None
                    try:
                        subcategory = Subcategory.query.get(subcategory_id)
                        if subcategory:
                            try:
                                supplier.subcategories.append(subcategory)
                            except AttributeError:
                                # Если связь еще не инициализирована, пропускаем
                                pass
                    except Exception as e:
                        if current_app.logger:
                            current_app.logger.warning(f'Ошибка при привязке подкатегории {subcategory_id}: {e}')
        
        try:
            db.session.commit()
            flash('Поставщик успешно создан', 'success')
            return redirect(url_for('main.suppliers'))
        except Exception as e:
            db.session.rollback()
            import traceback
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            flash(f'Ошибка при создании поставщика: {error_msg}', 'error')
            if current_app.logger:
                current_app.logger.error(f'Ошибка создания поставщика: {error_msg}\n{error_traceback}')
            else:
                current_app.logger.error(f'Ошибка создания поставщика: {error_msg}', exc_info=True)
            return render_template('main/supplier_form.html', form=form, title='Создать поставщика')
    
    # Автоматически заполнить код при открытии формы
    try:
        if not form.code.data:
            form.code.data = generate_supplier_code()
    except Exception as e:
        # Если ошибка при генерации кода, оставить поле пустым
        if current_app.logger:
            current_app.logger.warning(f'Ошибка генерации кода поставщика: {e}')
        form.code.data = ''
    
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
        try:
            if hasattr(supplier, 'subcategories'):
                form.subcategory_ids.data = [s.id for s in supplier.subcategories.all()]
            else:
                form.subcategory_ids.data = []
        except Exception:
            form.subcategory_ids.data = []
    
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
        from app.models.subcategory import Subcategory
        if hasattr(supplier, 'subcategories'):
            # Очистить существующие связи
            supplier.subcategories = []
            if form.subcategory_ids.data:
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
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Проверить бизнес-правила из ТЗ: нельзя удалить поставщика, если у него есть товары
        # Товары связаны с поставщиком через подкатегории
        from app.models.product import Product
        from app.models.subcategory import Subcategory
        supplier_subcategories = supplier.subcategories.all()
        subcategory_ids = [sc.id for sc in supplier_subcategories]
        if subcategory_ids:
            products_count = Product.query.filter(Product.subcategory_id.in_(subcategory_ids)).count()
            if products_count > 0:
                flash('Нельзя удалить поставщика с товарами', 'error')
                return redirect(url_for('main.suppliers'))
        
        # Удалить все запросы данных со статусом new или cancelled (согласно ТЗ)
        from app.models.data_request import DataRequest, DataRequestStatus
        data_requests = DataRequest.query.filter_by(supplier_id=supplier_id).filter(
            DataRequest.status.in_([DataRequestStatus.NEW, DataRequestStatus.CANCELLED])
        ).all()
        for dr in data_requests:
            db.session.delete(dr)
        
        db.session.delete(supplier)
        db.session.commit()
        flash('Поставщик успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при удалении поставщика {supplier_id}: {str(e)}", exc_info=True)
        flash('Ошибка при удалении поставщика', 'error')
    return redirect(url_for('main.suppliers'))

@bp.route('/suppliers/<int:supplier_id>/download-template')
@login_required
def download_supplier_template(supplier_id):
    """Скачать Excel шаблон для поставщика"""
    from app.services.template_generator_service import TemplateGeneratorService
    
    category_id = request.args.get('category_id', type=int)
    
    try:
        template_file = TemplateGeneratorService.generate_supplier_template(
            supplier_id=supplier_id,
            category_id=category_id
        )
        
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Сформировать имя файла
        if category_id:
            category = ProductCategory.query.get(category_id)
            if category:
                filename = f"Шаблон_{category.code}_{category.name.replace(' ', '_')}_{supplier.code}.xlsx"
            else:
                filename = f"Шаблон_{supplier.code}_{supplier.name.replace(' ', '_')}.xlsx"
        else:
            filename = f"Шаблон_{supplier.code}_{supplier.name.replace(' ', '_')}.xlsx"
        
        # Очистить имя файла от недопустимых символов
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        
        return send_file(
            template_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('main.categories'))
    except Exception as e:
        flash(f'Ошибка при генерации шаблона: {str(e)}', 'error')
        if current_app.logger:
            current_app.logger.error(f'Ошибка генерации шаблона: {str(e)}', exc_info=True)
        return redirect(url_for('main.categories'))

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
    try:
        subcategory = Subcategory.query.get_or_404(subcategory_id)
        
        # Проверить бизнес-правила из ТЗ: нельзя удалить подкатегорию, если у неё есть товары
        if subcategory.products.count() > 0:
            flash('Нельзя удалить подкатегорию с товарами', 'error')
            return redirect(url_for('main.subcategories'))
        
        # Удалить все связи с атрибутами (SubcategoryAttribute)
        from app.models.subcategory_attribute import SubcategoryAttribute
        SubcategoryAttribute.query.filter_by(subcategory_id=subcategory_id).delete()
        
        # Удалить все запросы данных, включающие эту подкатегорию (только со статусом new или cancelled)
        from app.models.data_request import DataRequest, DataRequestStatus
        all_requests = DataRequest.query.filter(
            DataRequest.status.in_([DataRequestStatus.NEW, DataRequestStatus.CANCELLED])
        ).all()
        for dr in all_requests:
            subcat_ids = dr.get_subcategory_ids()
            if subcategory_id in subcat_ids:
                db.session.delete(dr)
        
        db.session.delete(subcategory)
        db.session.commit()
        flash('Подкатегория успешно удалена', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при удалении подкатегории {subcategory_id}: {str(e)}", exc_info=True)
        flash('Ошибка при удалении подкатегории', 'error')
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
    """Импорт атрибутов из файла с предпросмотром и маппингом"""
    from flask_wtf.csrf import generate_csrf
    from app.services.attribute_import_service import AttributeImportService
    from app.services.attribute_preview_service import AttributePreviewService
    from app.services.clipboard_attribute_service import ClipboardAttributeService
    from werkzeug.utils import secure_filename
    import os
    import json
    from config import Config
    
    if request.method == 'POST':
        # Проверка, это предпросмотр из буфера обмена
        if request.form.get('action') == 'preview_clipboard':
            clipboard_text = request.form.get('clipboard_data', '')
            if not clipboard_text:
                return jsonify({'error': 'Данные из буфера обмена не переданы'}), 400
            
            clipboard_text = clipboard_text.strip()
            if not clipboard_text:
                return jsonify({'error': 'Данные из буфера обмена пусты'}), 400
            
            try:
                # Логирование для отладки
                if current_app.config.get('DEBUG'):
                    current_app.logger.debug(f"Получены данные из буфера, длина: {len(clipboard_text)}")
                    current_app.logger.debug(f"Первые 200 символов: {clipboard_text[:200]}")
                    current_app.logger.debug(f"Есть табуляция: {'\\t' in clipboard_text}, переносы строк: {'\\n' in clipboard_text}")
                
                # Использовать новый полноценный сервис
                preview = ClipboardAttributeService.parse_clipboard_data(clipboard_text)
                
                # Получить существующие атрибуты
                existing_attrs = Attribute.query.all()
                existing_attrs_list = [{'code': a.code, 'name': a.name, 'type': a.type.value, 'unit': a.unit} for a in existing_attrs]
                
                # Предложить маппинг с проверкой единиц измерения
                for sheet in preview['sheets']:
                    mapping = ClipboardAttributeService.suggest_mapping(
                        sheet['columns'],
                        existing_attrs_list
                    )
                    sheet['mapping'] = mapping
                
                return jsonify(preview)
            except ValueError as e:
                # Ошибки валидации - вернуть понятное сообщение
                error_msg = str(e)
                current_app.logger.warning(f"ValueError при предпросмотре буфера: {error_msg}")
                # Убрать технические детали из сообщения
                if '\nДетали:' in error_msg:
                    error_msg = error_msg.split('\nДетали:')[0]
                return jsonify({'error': error_msg}), 400
            except Exception as e:
                # Другие ошибки
                import traceback
                error_details = traceback.format_exc()
                current_app.logger.error(f"Ошибка предпросмотра буфера: {error_details}", exc_info=True)
                
                # Вернуть понятное сообщение с более детальной информацией
                error_message = f'Ошибка при обработке данных: {str(e)}'
                
                # Если это ошибка парсинга, добавить подсказку
                if 'parse' in str(e).lower() or 'split' in str(e).lower() or 'ValueError' in str(type(e)):
                    error_message += ' Проверьте, что данные скопированы из таблицы и разделены табуляцией.'
                
                # Добавить информацию о типе ошибки для отладки
                if 'AttributeError' in str(type(e)) or 'TypeError' in str(type(e)):
                    error_message += f' (Техническая ошибка: {type(e).__name__})'
                
                return jsonify({'error': error_message}), 400
        
        # Проверка, это предпросмотр файла
        if request.form.get('action') == 'preview' or 'action' in request.files:
            # Предпросмотр файла (AJAX)
            if 'file' not in request.files:
                return jsonify({'error': 'Файл не выбран'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Файл не выбран'}), 400
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                file.save(filepath)
                
                try:
                    preview = AttributePreviewService.preview_file(filepath)
                    
                    # Получить существующие атрибуты
                    existing_attrs = Attribute.query.all()
                    existing_attrs_list = [{'code': a.code, 'name': a.name, 'type': a.type.value, 'unit': a.unit} for a in existing_attrs]
                    
                    # Предложить маппинг для каждого листа
                    for sheet in preview['sheets']:
                        mapping = AttributePreviewService.suggest_mapping(
                            sheet['columns'],
                            existing_attrs_list
                        )
                        sheet['mapping'] = mapping
                    
                    return jsonify(preview)
                except Exception as e:
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    return jsonify({'error': str(e)}), 400
        
        # Импорт с маппингом
        # Проверка, это импорт из буфера обмена
        if request.form.get('source') == 'clipboard':
            clipboard_text = request.form.get('clipboard_data', '')
            if not clipboard_text:
                flash('Данные из буфера обмена не переданы', 'error')
                return redirect(url_for('main.import_attributes'))
            
            try:
                # Получить маппинг из формы
                mapping_data = request.form.get('mapping', '{}')
                if current_app.config.get('DEBUG'):
                    current_app.logger.debug(f"Import: mapping_data length = {len(mapping_data)}, clipboard_text length = {len(clipboard_text)}")
                mapping = json.loads(mapping_data) if mapping_data else {}
                
                if not mapping:
                    flash('Маппинг не указан. Пожалуйста, настройте маппинг атрибутов перед импортом.', 'error')
                    return redirect(url_for('main.import_attributes'))
                
                # Использовать новый полноценный сервис с валидацией
                result = ClipboardAttributeService.import_attributes(clipboard_text, mapping)
                if current_app.config.get('DEBUG'):
                    current_app.logger.debug(f"Import result: success={result.get('success', False)}, imported={result.get('imported_count', 0)}")
                
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
                flash(f'❌ Ошибка при импорте: {str(e)}', 'error')
                return redirect(url_for('main.import_attributes'))
        
        # Импорт из файла
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
                # Получить маппинг из формы
                mapping_data = request.form.get('mapping', '{}')
                mapping = json.loads(mapping_data) if mapping_data else {}
                sheet_name = request.form.get('sheet_name')
                
                result = AttributeImportService.import_from_file(filepath, mapping=mapping, sheet_name=sheet_name)
                
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
                # Удалить файл при ошибке
                try:
                    os.remove(filepath)
                except:
                    pass
                flash(f'❌ Ошибка при импорте: {str(e)}', 'error')
                return redirect(url_for('main.import_attributes'))
        else:
            flash('Неверный формат файла', 'error')
    
    # GET запрос - показать форму
    # Получить существующие атрибуты для подсказок
    existing_attrs = Attribute.query.all()
    existing_attrs_list = [{'code': a.code, 'name': a.name, 'type': a.type.value, 'unit': a.unit} for a in existing_attrs]
    
    # Генерировать CSRF токен
    csrf_token_value = generate_csrf()
    
    return render_template('main/import_attributes.html', 
                         existing_attributes=existing_attrs_list,
                         csrf_token_value=csrf_token_value)

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

@bp.route('/api/subcategories', methods=['GET'])
@login_required
def get_subcategories_api():
    """API для получения списка подкатегорий с фильтрацией"""
    category_id = request.args.get('category_id', type=int)
    supplier_id = request.args.get('supplier_id', type=int)
    is_active = request.args.get('is_active', 'true').lower() == 'true'
    
    query = Subcategory.query.filter_by(is_active=is_active) if is_active else Subcategory.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if supplier_id:
        # Фильтровать по поставщику через many-to-many связь
        supplier = Supplier.query.get(supplier_id)
        if supplier:
            supplier_subcategory_ids = [s.id for s in supplier.subcategories.all()]
            query = query.filter(Subcategory.id.in_(supplier_subcategory_ids))
    
    subcategories = query.order_by(Subcategory.name).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'code': s.code,
        'category_id': s.category_id,
        'category_name': s.category.name if s.category else None
    } for s in subcategories])

# ==================== Роуты для работы с запросами данных ====================

@bp.route('/api/data-requests/create', methods=['POST'])
@login_required
def create_data_request():
    """Создать новый запрос данных"""
    from app.models.data_request import DataRequest, DataRequestStatus
    from app.services.data_request_service import DataRequestService
    from datetime import datetime, timedelta
    import json
    
    try:
        data = request.get_json()
        supplier_id = data.get('supplier_id')
        category_id = data.get('category_id')
        subcategory_ids = data.get('subcategory_ids', [])
        deadline_days = data.get('deadline_days', 30)
        request_message = data.get('request_message')
        
        if not supplier_id or not category_id or not subcategory_ids:
            return jsonify({'error': 'Необходимо указать supplier_id, category_id и subcategory_ids'}), 400
        
        # Вычислить deadline
        deadline = datetime.utcnow() + timedelta(days=deadline_days) if deadline_days else None
        
        # Создать запрос
        request_obj = DataRequestService.create_request(
            supplier_id=supplier_id,
            category_id=category_id,
            subcategory_ids=subcategory_ids,
            requested_by_id=current_user.id,
            deadline=deadline,
            request_message=request_message
        )
        
        return jsonify({
            'success': True,
            'request': request_obj.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Ошибка при создании запроса: {str(e)}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@bp.route('/api/data-requests/<int:request_id>/send', methods=['POST'])
@login_required
def send_data_request(request_id):
    """Отправить запрос поставщику"""
    from app.services.data_request_service import DataRequestService
    
    try:
        request_obj = DataRequestService.send_request(request_id)
        return jsonify({
            'success': True,
            'request': request_obj.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Ошибка при отправке запроса: {str(e)}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@bp.route('/api/data-requests/<int:request_id>/mark-received', methods=['POST'])
@login_required
def mark_data_received(request_id):
    """Отметить получение данных от поставщика"""
    from app.services.data_request_service import DataRequestService
    from app.models.import_history import ImportHistory, ImportFileStatus
    
    try:
        data = request.get_json() or {}
        import_history_id = data.get('import_history_id')
        
        request_obj = DataRequestService.mark_received(request_id, import_history_id)
        
        return jsonify({
            'success': True,
            'request': request_obj.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Ошибка при отметке получения данных: {str(e)}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@bp.route('/api/data-requests/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_data_request(request_id):
    """Отменить запрос данных"""
    from app.services.data_request_service import DataRequestService
    
    try:
        request_obj = DataRequestService.cancel_request(request_id)
        return jsonify({
            'success': True,
            'request': request_obj.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Ошибка при отмене запроса: {str(e)}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@bp.route('/api/data-requests/<int:request_id>', methods=['GET'])
@login_required
def get_data_request(request_id):
    """Получить информацию о запросе"""
    from app.models.data_request import DataRequest
    
    request_obj = DataRequest.query.get_or_404(request_id)
    return jsonify(request_obj.to_dict())

@bp.route('/api/data-requests', methods=['GET'])
@login_required
def list_data_requests():
    """Получить список запросов с фильтрацией"""
    from app.models.data_request import DataRequest, DataRequestStatus
    
    supplier_id = request.args.get('supplier_id', type=int)
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status')
    
    query = DataRequest.query
    
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        try:
            status_enum = DataRequestStatus[status.upper()]
            query = query.filter_by(status=status_enum)
        except (KeyError, AttributeError):
            pass
    
    requests = query.order_by(DataRequest.created_at.desc()).all()
    return jsonify([r.to_dict() for r in requests])

@bp.route('/api/export/<int:import_history_id>', methods=['POST'])
@login_required
def export_to_db(import_history_id):
    """Экспортировать товары из файла в основную БД"""
    from app.models.import_history import ImportHistory, ImportFileStatus
    from app.models.product import Product, ProductStatus
    from app.models.export_history import ExportHistory
    from datetime import datetime
    
    try:
        import_file = ImportHistory.query.get_or_404(import_history_id)
        
        # Проверить, что файл в каталоге
        if import_file.file_status != ImportFileStatus.IN_CATALOG:
            return jsonify({'error': 'Файл должен быть в статусе "В каталоге"'}), 400
        
        # Получить товары из файла
        products = Product.query.filter_by(import_history_id=import_history_id).all()
        
        if not products:
            return jsonify({'error': 'В файле нет товаров'}), 400
        
        # Проверить, что все товары утверждены
        not_approved = [p for p in products if p.status != ProductStatus.APPROVED]
        if not_approved:
            return jsonify({
                'error': f'Не все товары утверждены. Не утверждено: {len(not_approved)}',
                'not_approved_count': len(not_approved)
            }), 400
        
        # Создать запись экспорта
        export_history = ExportHistory(
            import_history_id=import_history_id,
            products_count=len(products),
            exported_by_id=current_user.id,
            status='success',
            export_format='json'
        )
        export_history.set_products_ids([p.id for p in products])
        db.session.add(export_history)
        
        # Обновить статусы товаров
        for product in products:
            product.is_exported = True
            product.exported_at = datetime.utcnow()
            product.status = ProductStatus.EXPORTED
        
        # Обновить статус файла
        import_file.file_status = ImportFileStatus.EXPORTED
        import_file.exported_at = datetime.utcnow()
        import_file.exported_by_id = current_user.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'exported_count': len(products),
            'export_id': export_history.id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при экспорте: {str(e)}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@bp.route('/api/export/<int:import_history_id>/rollback', methods=['POST'])
@login_required
def rollback_export(import_history_id):
    """Откатить экспорт (только для администраторов)"""
    from app.models.import_history import ImportHistory, ImportFileStatus
    from app.models.product import Product, ProductStatus
    from app.models.export_history import ExportHistory
    from datetime import datetime
    
    if not current_user.is_admin:
        return jsonify({'error': 'Только администраторы могут откатывать экспорт'}), 403
    
    try:
        import_file = ImportHistory.query.get_or_404(import_history_id)
        
        if import_file.file_status != ImportFileStatus.EXPORTED:
            return jsonify({'error': 'Файл не экспортирован'}), 400
        
        # Найти последний экспорт
        export_history = ExportHistory.query.filter_by(
            import_history_id=import_history_id,
            is_rolled_back=False
        ).order_by(ExportHistory.exported_at.desc()).first()
        
        if not export_history:
            return jsonify({'error': 'Запись экспорта не найдена'}), 404
        
        # Получить товары
        products_ids = export_history.get_products_ids()
        products = Product.query.filter(Product.id.in_(products_ids)).all()
        
        # Откатить статусы товаров
        for product in products:
            product.is_exported = False
            product.exported_at = None
            product.status = ProductStatus.APPROVED
        
        # Обновить статус файла
        import_file.file_status = ImportFileStatus.IN_CATALOG
        import_file.exported_at = None
        import_file.exported_by_id = None
        
        # Отметить экспорт как откаченный
        export_history.is_rolled_back = True
        export_history.rolled_back_at = datetime.utcnow()
        export_history.rolled_back_by_id = current_user.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'rolled_back_count': len(products)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при откате экспорта: {str(e)}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@bp.route('/api/import/<int:import_history_id>/log', methods=['GET'])
@login_required
def get_import_log(import_history_id):
    """Получить логи импорта"""
    from app.models.import_history import ImportHistory, ImportFileStatus
    from app.models.product import Product
    import enum
    
    import_file = ImportHistory.query.get_or_404(import_history_id)
    products = Product.query.filter_by(import_history_id=import_history_id).all()
    
    log_data = {
        'file': {
            'id': import_file.id,
            'filename': import_file.filename,
            'status': import_file.status,
            'file_status': import_file.file_status.value if isinstance(import_file.file_status, enum.Enum) else import_file.file_status,
            'total_rows': import_file.total_rows,
            'imported_count': import_file.imported_count,
            'errors_count': import_file.errors_count,
            'warnings_count': import_file.warnings_count,
            'error_message': import_file.error_message,
            'imported_at': import_file.imported_at.isoformat() if import_file.imported_at else None,
        },
        'products': [{
            'id': p.id,
            'sku': p.sku,
            'name': p.name,
            'status': p.status.value if isinstance(p.status, enum.Enum) else p.status,
        } for p in products],
        'errors': import_file.error_message.split('; ') if import_file.error_message else []
    }
    
    return jsonify(log_data)

@bp.route('/api/import/<int:import_history_id>/reverify', methods=['POST'])
@login_required
def reverify_import(import_history_id):
    """Повторная верификация всех товаров из файла"""
    from app.models.import_history import ImportHistory
    from app.models.product import Product
    from app.services.verification_service import VerificationService
    
    try:
        import_file = ImportHistory.query.get_or_404(import_history_id)
        products = Product.query.filter_by(import_history_id=import_history_id).all()
        
        if not products:
            return jsonify({'error': 'В файле нет товаров'}), 400
        
        verified_count = 0
        errors = []
        
        for product in products:
            try:
                VerificationService.verify_product(product, current_user)
                verified_count += 1
            except Exception as e:
                errors.append(f"Товар {product.sku}: {str(e)}")
        
        return jsonify({
            'success': True,
            'verified_count': verified_count,
            'total_count': len(products),
            'errors': errors
        })
        
    except Exception as e:
        current_app.logger.error(f"Ошибка при повторной верификации: {str(e)}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@bp.route('/api/import/<int:import_history_id>/cancel', methods=['POST'])
@login_required
def cancel_import(import_history_id):
    """Отменить импорт (удалить товары из файла)"""
    from app.models.import_history import ImportHistory, ImportFileStatus
    from app.models.product import Product
    
    if not current_user.is_admin:
        return jsonify({'error': 'Только администраторы могут отменять импорт'}), 403
    
    try:
        import_file = ImportHistory.query.get_or_404(import_history_id)
        
        if import_file.file_status == ImportFileStatus.EXPORTED:
            return jsonify({'error': 'Нельзя отменить импорт экспортированного файла'}), 400
        
        # Удалить все товары из этого файла
        products = Product.query.filter_by(import_history_id=import_history_id).all()
        products_count = len(products)
        
        for product in products:
            db.session.delete(product)
        
        # Обновить статус файла
        import_file.file_status = ImportFileStatus.FAILED
        import_file.status = 'failed'
        import_file.error_message = 'Импорт отменен пользователем'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_products': products_count
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при отмене импорта: {str(e)}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@bp.route('/api/export/<int:import_history_id>', methods=['GET'])
@login_required
def get_export_details(import_history_id):
    """Получить детали экспорта"""
    from app.models.import_history import ImportHistory
    from app.models.export_history import ExportHistory
    
    import_file = ImportHistory.query.get_or_404(import_history_id)
    export_history = ExportHistory.query.filter_by(
        import_history_id=import_history_id,
        is_rolled_back=False
    ).order_by(ExportHistory.exported_at.desc()).first()
    
    data = {
        'filename': import_file.filename,
        'exported_count': import_file.imported_count,
        'exported_at': import_file.exported_at.isoformat() if import_file.exported_at else None,
        'exported_by': import_file.exported_by.username if import_file.exported_by else None,
        'status': 'exported',
    }
    
    if export_history:
        data.update({
            'export_id': export_history.id,
            'products_count': export_history.products_count,
            'export_format': export_history.export_format,
        })
    
    return jsonify(data)

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
