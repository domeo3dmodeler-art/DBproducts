"""
Маршруты для импорта данных
"""
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import FileField, SelectField, BooleanField
from wtforms.validators import DataRequired
from app.import_data import bp
from app.models.subcategory import Subcategory
from app.models.supplier import Supplier
from app.services.import_service import ImportService
from werkzeug.utils import secure_filename
import os
from config import Config

class ImportForm(FlaskForm):
    """Форма импорта"""
    file = FileField('Файл', validators=[DataRequired()])
    subcategory_id = SelectField('Подкатегория', coerce=int, validators=[DataRequired()])
    auto_verify = BooleanField('Автоматическая верификация', default=True)

@bp.route('/', methods=['GET', 'POST'])
@login_required
def import_page():
    """Страница импорта данных"""
    form = ImportForm()
    
    # Заполнить список подкатегорий
    from app.models.category import ProductCategory
    form.subcategory_id.choices = []
    for category in ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all():
        for subcategory in Subcategory.query.filter_by(category_id=category.id, is_active=True).order_by(Subcategory.name).all():
            form.subcategory_id.choices.append((subcategory.id, f"{category.name} → {subcategory.name} ({subcategory.code})"))
    
    if request.method == 'POST' and form.validate():
        file = request.files.get('file')
        subcategory_id = form.subcategory_id.data
        auto_verify = form.auto_verify.data
        
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            file.save(filepath)
            
            try:
                # Создать запись истории импорта
                from app.models.import_history import ImportHistory
                from app import db
                
                import_history = ImportHistory(
                    filename=filename,
                    file_path=filepath,  # Сохраняем путь для возможного повторного использования
                    subcategory_id=subcategory_id,
                    imported_by_id=current_user.id,
                    total_rows=0,  # Будет обновлено после импорта
                    status='processing'
                )
                db.session.add(import_history)
                db.session.commit()
                
                # Выполнить импорт
                result = ImportService.import_from_file(
                    filepath, 
                    subcategory_id, 
                    user=current_user,
                    auto_verify=auto_verify
                )
                
                # Обновить историю импорта
                import_history.total_rows = result.get('total_rows', 0)
                import_history.imported_count = result['imported']
                import_history.errors_count = len(result['errors'])
                import_history.warnings_count = len(result['warnings'])
                import_history.status = 'completed' if result['imported'] > 0 else 'failed'
                if result['errors']:
                    import_history.error_message = '; '.join(result['errors'][:5])  # Первые 5 ошибок
                db.session.commit()
                
                # Удалить файл после импорта (опционально, можно сохранить для истории)
                # try:
                #     os.remove(filepath)
                # except:
                #     pass
                
                # Показать результаты
                if result['imported'] > 0:
                    flash(f'✅ Успешно импортировано товаров: {result["imported"]}', 'success')
                else:
                    flash('⚠️ Товары не были импортированы', 'warning')
                
                if result['errors']:
                    for error in result['errors'][:10]:  # Показать первые 10 ошибок
                        flash(f'❌ Ошибка: {error}', 'error')
                
                if result['warnings']:
                    for warning in result['warnings'][:10]:  # Показать первые 10 предупреждений
                        flash(f'⚠️ Предупреждение: {warning}', 'warning')
                
                return redirect(url_for('import_data.import_page'))
                
            except Exception as e:
                # Обновить историю импорта с ошибкой
                try:
                    from app.models.import_history import ImportHistory
                    from app import db
                    import_history = ImportHistory.query.filter_by(filename=filename).order_by(ImportHistory.id.desc()).first()
                    if import_history:
                        import_history.status = 'failed'
                        import_history.error_message = str(e)
                        db.session.commit()
                except:
                    pass
                
                # Удалить файл при ошибке
                # try:
                #     os.remove(filepath)
                # except:
                #     pass
                
                flash(f'❌ Ошибка при импорте: {str(e)}', 'error')
                return redirect(url_for('import_data.import_page'))
        else:
            flash('Неверный формат файла', 'error')
    
    # Получить списки для выбора
    suppliers = Supplier.query.filter_by(is_active=True).all()
    subcategories = Subcategory.query.filter_by(is_active=True).all()
    
    return render_template('import/import.html', 
                         form=form,
                         suppliers=suppliers, 
                         subcategories=subcategories)

@bp.route('/api/mapping', methods=['POST'])
@login_required
def get_field_mapping():
    """Получить маппинг полей для файла (API)"""
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не выбран'}), 400
    
    file = request.files['file']
    subcategory_id = request.form.get('subcategory_id', type=int)
    
    if not subcategory_id:
        return jsonify({'error': 'Необходимо указать подкатегорию'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, f'temp_{filename}')
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)
        
        try:
            # Прочитать первую строку для определения колонок
            from pathlib import Path
            file_ext = Path(filepath).suffix.lower()
            
            if file_ext in ['.xlsx', '.xls']:
                import pandas as pd
                df = pd.read_excel(filepath, nrows=1)
                columns = df.columns.tolist()
            elif file_ext == '.csv':
                import csv
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    columns = next(reader)
            elif file_ext == '.json':
                import json
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        columns = list(data[0].keys())
                    else:
                        columns = []
            else:
                columns = []
            
            # Получить атрибуты подкатегории
            subcategory = Subcategory.query.get_or_404(subcategory_id)
            attributes = {attr.attribute.code: attr.attribute.name 
                         for attr in subcategory.get_all_attributes()}
            
            # Автоматический маппинг
            from app.services.import_service import ImportService
            mapping = ImportService._auto_map_fields(columns, attributes.keys())
            
            # Удалить временный файл
            try:
                os.remove(filepath)
            except:
                pass
            
            return jsonify({
                'columns': columns,
                'attributes': attributes,
                'mapping': mapping
            })
            
        except Exception as e:
            try:
                os.remove(filepath)
            except:
                pass
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Неподдерживаемый формат файла'}), 400

def allowed_file(filename):
    """Проверить, разрешен ли тип файла"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

