"""
Сервис импорта данных о товарах
"""
import pandas as pd
import json
import csv
from pathlib import Path
from app import db
from app.models.product import Product, ProductStatus
from app.models.subcategory import Subcategory
from app.models.attribute import Attribute, AttributeType
from app.models.subcategory_attribute import SubcategoryAttribute
from app.models.product import ProductAttributeValue
from app.models.workflow import ProductStatusHistory
from app.services.verification_service import VerificationService
from flask_login import current_user
from datetime import datetime

class ImportService:
    """Сервис для импорта товаров из файлов"""
    
    @staticmethod
    def import_from_file(file_path, subcategory_id, user=None, auto_verify=True, import_history_id=None):
        """
        Импортировать товары из файла
        
        Args:
            file_path: Путь к файлу
            subcategory_id: ID подкатегории
            user: Пользователь, выполняющий импорт
            auto_verify: Автоматически запускать верификацию после импорта
            import_history_id: ID записи ImportHistory (опционально)
        
        Returns:
            dict: Результаты импорта
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        # Получить информацию о подкатегории для поиска листа
        subcategory = Subcategory.query.get(subcategory_id)
        subcategory_name = subcategory.name if subcategory else None
        
        # Определить формат файла и получить данные
        if file_extension in ['.xlsx', '.xls']:
            data, total_rows = ImportService._parse_excel(file_path, subcategory_name=subcategory_name)
        elif file_extension == '.csv':
            data, total_rows = ImportService._parse_csv(file_path)
        elif file_extension == '.json':
            data, total_rows = ImportService._parse_json(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")
        
        # Выполнить импорт
        result = ImportService._import_products(data, subcategory_id, user, auto_verify, import_history_id)
        result['total_rows'] = total_rows
        return result
    
    @staticmethod
    def _parse_excel(file_path, sheet_name=None, subcategory_name=None):
        """
        Парсинг Excel файла
        
        Args:
            file_path: Путь к файлу
            sheet_name: Имя листа (если None - первый лист или поиск по подкатегории)
            subcategory_name: Название подкатегории для поиска листа
        """
        try:
            # Определить движок
            if file_path.suffix == '.xlsx':
                engine = 'openpyxl'
            else:
                engine = 'xlrd'
            
            # Если указано имя листа - использовать его
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)
            elif subcategory_name:
                # Попытаться найти лист по названию подкатегории
                excel_file = pd.ExcelFile(file_path, engine=engine)
                found_sheet = None
                
                # Точное совпадение
                if subcategory_name in excel_file.sheet_names:
                    found_sheet = subcategory_name
                else:
                    # Частичное совпадение (первые 31 символ - ограничение Excel)
                    subcat_short = subcategory_name[:31]
                    for sheet in excel_file.sheet_names:
                        if subcat_short in sheet or sheet in subcategory_name:
                            found_sheet = sheet
                            break
                
                if found_sheet:
                    df = pd.read_excel(file_path, sheet_name=found_sheet, engine=engine)
                else:
                    # Если не найден - использовать первый лист (пропустить инструкции)
                    available_sheets = [s for s in excel_file.sheet_names if not s.startswith('📋') and s != 'ИНСТРУКЦИЯ']
                    if available_sheets:
                        df = pd.read_excel(file_path, sheet_name=available_sheets[0], engine=engine)
                    else:
                        df = pd.read_excel(file_path, engine=engine)
            else:
                # Использовать первый лист (пропустить инструкции)
                excel_file = pd.ExcelFile(file_path, engine=engine)
                available_sheets = [s for s in excel_file.sheet_names if not s.startswith('📋') and s != 'ИНСТРУКЦИЯ']
                if available_sheets:
                    df = pd.read_excel(file_path, sheet_name=available_sheets[0], engine=engine)
                else:
                    df = pd.read_excel(file_path, engine=engine)
            
            # Пропустить строку с примером (если есть)
            # Проверить первую строку данных
            if len(df) > 0:
                first_row = df.iloc[0]
                # Если первая строка содержит "ПРИМЕР" - пропустить её
                if any('ПРИМЕР' in str(val).upper() for val in first_row.values if pd.notna(val)):
                    df = df.iloc[1:].reset_index(drop=True)
            
            # Преобразовать в список словарей
            data = df.to_dict('records')
            
            # Очистить NaN значения
            for row in data:
                for key, value in row.items():
                    try:
                        if pd.isna(value):
                            row[key] = None
                    except (TypeError, ValueError):
                        # Если не pandas значение, проверить на None
                        if value is None:
                            row[key] = None
            
            total_rows = len(data)
            return data, total_rows
        except Exception as e:
            raise ValueError(f"Ошибка при чтении Excel файла: {str(e)}")
    
    @staticmethod
    def _parse_csv(file_path):
        """Парсинг CSV файла"""
        try:
            # Попробовать разные кодировки
            encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin-1']
            data = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        # Определить разделитель
                        sample = f.read(1024)
                        f.seek(0)
                        sniffer = csv.Sniffer()
                        delimiter = sniffer.sniff(sample).delimiter
                        
                        reader = csv.DictReader(f, delimiter=delimiter)
                        data = list(reader)
                        break
                except UnicodeDecodeError:
                    continue
            
            if data is None:
                raise ValueError("Не удалось определить кодировку CSV файла")
            
            total_rows = len(data)
            return data, total_rows
        except Exception as e:
            raise ValueError(f"Ошибка при чтении CSV файла: {str(e)}")
    
    @staticmethod
    def _parse_json(file_path):
        """Парсинг JSON файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Если это список словарей - вернуть как есть
            if isinstance(data, list):
                total_rows = len(data)
                return data, total_rows
            
            # Если это словарь с ключом 'products' или 'items'
            if isinstance(data, dict):
                if 'products' in data:
                    result_data = data['products']
                    total_rows = len(result_data) if isinstance(result_data, list) else 1
                    return result_data, total_rows
                elif 'items' in data:
                    result_data = data['items']
                    total_rows = len(result_data) if isinstance(result_data, list) else 1
                    return result_data, total_rows
                else:
                    # Вернуть как список с одним элементом
                    return [data], 1
            
            raise ValueError("Неверный формат JSON файла")
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка при парсинге JSON: {str(e)}")
    
    @staticmethod
    def _import_products(data, subcategory_id, user=None, auto_verify=True, import_history_id=None):
        """
        Импортировать товары из данных
        
        Args:
            data: Данные для импорта
            subcategory_id: ID подкатегории
            user: Пользователь
            auto_verify: Автоматическая верификация
            import_history_id: ID записи ImportHistory (для связи товаров с файлом)
        
        Returns:
            dict: {
                'imported': количество импортированных,
                'errors': список ошибок,
                'warnings': список предупреждений,
                'products': список созданных товаров
            }
        """
        subcategory = Subcategory.query.get_or_404(subcategory_id)
        
        imported_count = 0
        errors = []
        warnings = []
        products = []
        
        # Получить эталонные атрибуты подкатегории
        reference_attributes = {attr.attribute.code: attr for attr in subcategory.get_all_attributes()}
        
        # Определить маппинг полей (автоматический)
        if not data:
            return {
                'imported': 0,
                'errors': ['Файл пуст или не содержит данных'],
                'warnings': [],
                'products': []
            }
        
        # Получить названия колонок из первой строки
        first_row = data[0]
        column_mapping = ImportService._auto_map_fields(first_row.keys(), reference_attributes.keys())
        
        # Обработать каждую строку
        for row_num, row_data in enumerate(data, start=2):  # Начинаем с 2 (первая строка - заголовки)
            try:
                # Создать товар
                product = ImportService._create_product_from_row(
                    row_data, 
                    subcategory, 
                    column_mapping, 
                    reference_attributes,
                    user
                )
                
                products.append(product)
                imported_count += 1
                
                # Скачать медиа-файлы (фото и 3D модели)
                try:
                    from app.services.media_service import MediaService
                    media_stats = MediaService.process_product_media(product, auto_download=True)
                    if media_stats['images_downloaded'] > 0:
                        warnings.append(f"Строка {row_num}: Скачано изображений: {media_stats['images_downloaded']}")
                    if media_stats['models_downloaded'] > 0:
                        warnings.append(f"Строка {row_num}: Скачано 3D моделей: {media_stats['models_downloaded']}")
                    if media_stats['errors']:
                        for error in media_stats['errors']:
                            warnings.append(f"Строка {row_num}: {error}")
                except Exception as e:
                    warnings.append(f"Строка {row_num}: Ошибка при скачивании медиа-файлов - {str(e)}")
                
                # Автоматическая верификация
                if auto_verify:
                    try:
                        VerificationService.verify_product(product, user)
                    except Exception as e:
                        warnings.append(f"Строка {row_num}: Ошибка верификации - {str(e)}")
                
            except Exception as e:
                errors.append(f"Строка {row_num}: {str(e)}")
                continue
        
        db.session.commit()
        
        return {
            'imported': imported_count,
            'total_rows': total_rows,
            'errors': errors,
            'warnings': warnings,
            'products': [p.to_dict() for p in products]
        }
    
    @staticmethod
    def _auto_map_fields(file_columns, attribute_codes):
        """
        Автоматический маппинг полей файла с атрибутами
        
        Args:
            file_columns: Список названий колонок в файле
            attribute_codes: Список кодов атрибутов
        
        Returns:
            dict: Маппинг {название_колонки: код_атрибута}
        """
        mapping = {}
        
        # Нормализовать названия (нижний регистр, убрать пробелы)
        normalized_columns = {col.lower().strip(): col for col in file_columns}
        normalized_attributes = {code.lower().strip(): code for code in attribute_codes}
        
        # Специальные маппинги для стандартных полей
        special_mappings = {
            'sku': ['sku', 'артикул', 'article', 'код', 'code'],
            'name': ['name', 'название', 'title', 'наименование'],
            'description': ['description', 'описание', 'desc'],
        }
        
        # Маппинг стандартных полей
        for attr_code, possible_names in special_mappings.items():
            if attr_code in normalized_attributes:
                for name in possible_names:
                    if name in normalized_columns:
                        mapping[normalized_columns[name]] = attr_code
                        break
        
        # Маппинг атрибутов по точному совпадению
        for norm_col, orig_col in normalized_columns.items():
            if norm_col in normalized_attributes:
                if orig_col not in mapping:  # Не перезаписывать уже найденные
                    mapping[orig_col] = normalized_attributes[norm_col]
        
        # Маппинг по частичному совпадению
        for norm_col, orig_col in normalized_columns.items():
            if orig_col not in mapping:
                for norm_attr, attr_code in normalized_attributes.items():
                    if norm_attr in norm_col or norm_col in norm_attr:
                        mapping[orig_col] = attr_code
                        break
        
        return mapping
    
    @staticmethod
    def _create_product_from_row(row_data, subcategory, column_mapping, reference_attributes, user):
        """
        Создать товар из строки данных
        
        Args:
            row_data: Словарь с данными строки
            subcategory: Объект Subcategory
            column_mapping: Маппинг колонок на коды атрибутов
            reference_attributes: Словарь эталонных атрибутов {code: SubcategoryAttribute}
            user: Пользователь
        
        Returns:
            Product: Созданный товар
        """
        # Получить SKU (обязательное поле)
        sku = None
        for col_name, attr_code in column_mapping.items():
            if attr_code == 'sku' and col_name in row_data:
                sku = str(row_data[col_name]).strip() if row_data[col_name] is not None else None
                break
        
        # Если SKU не найден, попробовать найти в любом поле
        if not sku:
            for key, value in row_data.items():
                if value and ('sku' in key.lower() or 'артикул' in key.lower() or 'код' in key.lower()):
                    sku = str(value).strip()
                    break
        
        if not sku:
            raise ValueError("Не найден артикул (SKU) товара")
        
        # Проверить уникальность SKU
        if Product.query.filter_by(sku=sku).first():
            raise ValueError(f"Товар с артикулом {sku} уже существует")
        
        # Проверить дублирование по артикулу производителя (если есть такой атрибут)
        manufacturer_sku = None
        manufacturer_sku_attr_code = None
        
        # Ищем атрибут артикула производителя
        for col_name, attr_code in column_mapping.items():
            if attr_code in ['manufacturer_sku', 'manufacturer_code', 'manufacturer_article', 
                            'производитель_артикул', 'артикул_производителя']:
                if col_name in row_data and row_data[col_name]:
                    manufacturer_sku = str(row_data[col_name]).strip()
                    manufacturer_sku_attr_code = attr_code
                    break
        
        # Если не нашли в маппинге, ищем в данных
        if not manufacturer_sku:
            for key, value in row_data.items():
                key_lower = key.lower()
                if value and ('manufacturer' in key_lower or 'производитель' in key_lower) and \
                   ('sku' in key_lower or 'code' in key_lower or 'article' in key_lower or 'артикул' in key_lower):
                    manufacturer_sku = str(value).strip()
                    break
        
        # Проверить дублирование по артикулу производителя
        if manufacturer_sku:
            from app.models.attribute import Attribute
            from app.models.product import ProductAttributeValue
            
            # Найти атрибут артикула производителя
            manufacturer_attr = Attribute.query.filter(
                Attribute.code.in_(['manufacturer_sku', 'manufacturer_code', 'manufacturer_article'])
            ).first()
            
            if manufacturer_attr:
                # Проверить, есть ли уже товар с таким артикулом производителя
                duplicate_pav = ProductAttributeValue.query.filter(
                    ProductAttributeValue.attribute_id == manufacturer_attr.id,
                    ProductAttributeValue.value == manufacturer_sku
                ).first()
                
                if duplicate_pav:
                    raise ValueError(f"Товар с артикулом производителя {manufacturer_sku} уже существует (товар ID: {duplicate_pav.product_id})")
        
        # Получить название
        name = None
        for col_name, attr_code in column_mapping.items():
            if attr_code == 'name' and col_name in row_data:
                name = str(row_data[col_name]).strip() if row_data[col_name] is not None else None
                break
        
        if not name:
            # Попробовать найти название в любом поле
            for key, value in row_data.items():
                if value and ('name' in key.lower() or 'название' in key.lower() or 'title' in key.lower()):
                    name = str(value).strip()
                    break
        
        if not name:
            name = f"Товар {sku}"  # Использовать SKU как название по умолчанию
        
        # Создать товар
        product = Product(
            sku=sku,
            name=name,
            subcategory_id=subcategory.id,
            status=ProductStatus.DRAFT,
            created_by_id=user.id if user else None,
            import_history_id=import_history_id  # Связь с файлом импорта
        )
        db.session.add(product)
        
        # Записать переход в статус in_progress
        history = ProductStatusHistory(
            product_id=product.id,
            old_status=ProductStatus.DRAFT.value,
            new_status=ProductStatus.IN_PROGRESS.value,
            changed_by_id=user.id if user else None,
            comment='Автоматический переход при импорте'
        )
        product.status = ProductStatus.IN_PROGRESS
        db.session.add(history)
        
        # Обработать атрибуты
        for col_name, value in row_data.items():
            if value is None:
                continue
            try:
                if hasattr(pd, 'isna') and pd.isna(value):
                    continue
            except (TypeError, ValueError):
                pass
            
            # Найти соответствующий атрибут
            attr_code = column_mapping.get(col_name)
            if not attr_code or attr_code not in reference_attributes:
                continue  # Пропустить поля, которые не маппятся на эталонные атрибуты
            
            subcat_attr = reference_attributes[attr_code]
            attribute = subcat_attr.attribute
            
            # Преобразовать значение в строку
            str_value = str(value).strip()
            if not str_value:
                continue
            
            # Валидация типа данных
            if not ImportService._validate_attribute_value(attribute, str_value):
                continue  # Пропустить невалидные значения
            
            # Создать или обновить значение атрибута
            pav = ProductAttributeValue.query.filter_by(
                product_id=product.id,
                attribute_id=attribute.id
            ).first()
            
            if pav:
                pav.value = str_value
            else:
                pav = ProductAttributeValue(
                    product_id=product.id,
                    attribute_id=attribute.id,
                    value=str_value
                )
                db.session.add(pav)
        
        db.session.flush()  # Сохранить в БД для получения ID
        
        return product
    
    @staticmethod
    def _validate_attribute_value(attribute, value):
        """Проверить значение атрибута на соответствие типу"""
        try:
            if attribute.type == AttributeType.NUMBER:
                float(value)
            elif attribute.type == AttributeType.BOOLEAN:
                value.lower() in ['true', 'false', '1', '0', 'yes', 'no', 'да', 'нет']
            elif attribute.type == AttributeType.DATE:
                # Попробовать разные форматы даты
                from dateutil import parser
                parser.parse(value)
            elif attribute.type == AttributeType.SELECT:
                # Проверить, что значение есть в списке допустимых
                allowed_values = [av.value for av in attribute.values.all()]
                return value in allowed_values
        except (ValueError, TypeError):
            return False
        
        return True

