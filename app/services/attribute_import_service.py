"""
Сервис импорта атрибутов из файлов
"""
import pandas as pd
import json
import csv
from pathlib import Path
from app import db
from app.models.attribute import Attribute, AttributeType
from app.utils.attribute_mapper import generate_attribute_code_from_name

class AttributeImportService:
    """Сервис для импорта атрибутов из файлов"""
    
    @staticmethod
    def import_from_file(file_path, mapping=None, sheet_name=None):
        """
        Импортировать атрибуты из файла
        
        Args:
            file_path: Путь к файлу
            mapping: Словарь маппинга {column_name: {attribute_code, is_new, unit, type}}
            sheet_name: Имя листа для Excel (если None - первый лист)
        
        Returns:
            dict: Результаты импорта
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        # Определить формат файла и получить данные
        if file_extension in ['.xlsx', '.xls']:
            data, total_rows = AttributeImportService._parse_excel(file_path, sheet_name=sheet_name)
        elif file_extension == '.csv':
            data, total_rows = AttributeImportService._parse_csv(file_path)
        elif file_extension == '.json':
            data, total_rows = AttributeImportService._parse_json(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")
        
        # Выполнить импорт с маппингом
        result = AttributeImportService._import_attributes(data, mapping=mapping)
        result['total_rows'] = total_rows
        return result
    
    @staticmethod
    def import_from_clipboard(clipboard_text, mapping=None):
        """
        Импортировать атрибуты из буфера обмена
        
        Args:
            clipboard_text: Текст из буфера обмена (TSV/CSV формат)
            mapping: Словарь маппинга {column_name: {attribute_code, is_new, unit, type}}
        
        Returns:
            dict: Результаты импорта
        """
        import io
        
        # Парсинг данных из буфера
        lines = clipboard_text.strip().split('\n')
        if not lines:
            raise ValueError("Буфер обмена пуст")
        
        # Определить разделитель
        first_line = lines[0]
        if '\t' in first_line:
            delimiter = '\t'
        elif ',' in first_line:
            delimiter = ','
        elif ';' in first_line:
            delimiter = ';'
        else:
            delimiter = '\t'
        
        # Создать DataFrame с правильной обработкой переносов строк
        df = pd.read_csv(
            io.StringIO(clipboard_text), 
            delimiter=delimiter,
            dtype=str,  # Все как строки
            keep_default_na=False,  # Не преобразовывать пустые в NaN
            on_bad_lines='skip',
            engine='python'
        )
        
        # Преобразовать в список словарей
        data = df.to_dict('records')
        
        from flask import current_app
        if current_app and current_app.config.get('DEBUG'):
            current_app.logger.debug(f"import_from_clipboard: columns={list(df.columns)}, shape={df.shape}")
        
        # Очистить NaN значения
        for row in data:
            for key, value in row.items():
                try:
                    if pd.isna(value):
                        row[key] = None
                except (TypeError, ValueError):
                    if value is None:
                        row[key] = None
        
        total_rows = len(data)
        
        # Выполнить импорт с маппингом
        result = AttributeImportService._import_attributes(data, mapping=mapping)
        result['total_rows'] = total_rows
        return result
    
    @staticmethod
    def _parse_excel(file_path, sheet_name=None):
        """Парсинг Excel файла"""
        try:
            if file_path.suffix == '.xlsx':
                if sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
                else:
                    df = pd.read_excel(file_path, engine='openpyxl')
            else:
                if sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='xlrd')
                else:
                    df = pd.read_excel(file_path, engine='xlrd')
            
            data = df.to_dict('records')
            
            # Очистить NaN значения
            for row in data:
                for key, value in row.items():
                    try:
                        if pd.isna(value):
                            row[key] = None
                    except (TypeError, ValueError):
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
            encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin-1']
            data = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
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
            
            if isinstance(data, list):
                total_rows = len(data)
                return data, total_rows
            elif isinstance(data, dict):
                if 'attributes' in data:
                    result_data = data['attributes']
                    total_rows = len(result_data) if isinstance(result_data, list) else 1
                    return result_data, total_rows
                else:
                    return [data], 1
            
            raise ValueError("Неверный формат JSON файла")
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка при парсинге JSON: {str(e)}")
    
    @staticmethod
    def _import_attributes(data, mapping=None):
        """
        Импортировать атрибуты из данных
        
        Args:
            data: Список словарей с данными
            mapping: Словарь маппинга {column_name: {attribute_code, is_new, unit, type}}
                    Если маппинг есть, каждая колонка = отдельный атрибут
        
        Returns:
            dict: {
                'imported': количество импортированных,
                'updated': количество обновленных,
                'errors': список ошибок,
                'warnings': список предупреждений
            }
        """
        imported_count = 0
        updated_count = 0
        errors = []
        warnings = []
        
        # Если есть маппинг от пользователя - каждая колонка = отдельный атрибут
        if mapping and data:
            print(f"DEBUG _import_attributes: mapping keys = {list(mapping.keys())}")
            print(f"DEBUG _import_attributes: data columns = {list(data[0].keys()) if data else []}")
            
            # Получить все уникальные колонки из данных
            all_columns = set()
            for row in data:
                all_columns.update(row.keys())
            
            from flask import current_app
            if current_app and current_app.config.get('DEBUG'):
                current_app.logger.debug(f"_import_attributes: all_columns = {all_columns}")
            
            # Обработать каждую колонку из маппинга
            # Пользователь может отредактировать названия колонок в UI
            # В маппинге может быть 'original_column_name' для связи с данными
            for edited_column_name in mapping.keys():
                map_info = mapping[edited_column_name]
                
                # Получить оригинальное название колонки из данных
                original_column_name = map_info.get('original_column_name', edited_column_name)
                
                # Проверить, есть ли эта колонка в данных
                if original_column_name not in all_columns:
                    from flask import current_app
                    if current_app:
                        current_app.logger.warning(f"_import_attributes: колонка '{original_column_name}' (отредактировано: '{edited_column_name}') не найдена в данных. Доступные: {all_columns}")
                    warnings.append(f"Колонка '{edited_column_name}': не найдена в данных, пропущена")
                    continue
                
                try:
                    if map_info.get('is_new', True):
                        # Новый атрибут
                        # Использовать отредактированное название (пользователь мог его изменить в UI)
                        name = edited_column_name
                        code = generate_attribute_code_from_name(name)
                        attr_type_str = map_info.get('type', 'text')
                        unit = map_info.get('unit')
                        
                        # Преобразовать тип
                        type_mapping = {
                            'text': AttributeType.TEXT,
                            'number': AttributeType.NUMBER,
                            'date': AttributeType.DATE,
                            'boolean': AttributeType.BOOLEAN,
                            'url': AttributeType.URL,
                            'image': AttributeType.IMAGE,
                            'select': AttributeType.SELECT
                        }
                        
                        # Проверить наличие THREE_D_MODEL
                        try:
                            from app.models.attribute import AttributeType
                            if hasattr(AttributeType, 'THREE_D_MODEL'):
                                type_mapping['3d_model'] = AttributeType.THREE_D_MODEL
                        except:
                            pass
                        
                        attr_type = type_mapping.get(attr_type_str.lower())
                        if not attr_type:
                            errors.append(f"Колонка '{edited_column_name}': Неверный тип '{attr_type_str}'")
                            continue
                        
                        # Проверить уникальность
                        existing_by_code = Attribute.query.filter_by(code=code).first()
                        existing_by_name = Attribute.query.filter_by(name=name).first()
                        
                        if existing_by_code or existing_by_name:
                            warnings.append(f"Колонка '{edited_column_name}': Атрибут уже существует, пропущена")
                            continue
                        
                        # Создать новый атрибут
                        attribute = Attribute(
                            code=code,
                            name=name,
                            type=attr_type,
                            unit=unit,
                            is_unique=False
                        )
                        db.session.add(attribute)
                        imported_count += 1
                    else:
                        # Существующий атрибут - обновить единицу измерения, если указана
                        attr_code = map_info.get('attribute_code')
                        if attr_code:
                            attr = Attribute.query.filter_by(code=attr_code).first()
                            if attr:
                                if map_info.get('unit'):
                                    attr.unit = map_info['unit']
                                    updated_count += 1
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    from flask import current_app
                    if current_app:
                        current_app.logger.error(f"_import_attributes: Ошибка для колонки '{edited_column_name}': {str(e)}", exc_info=True)
                    errors.append(f"Колонка '{edited_column_name}': {str(e)}")
                    continue
        else:
            # Старый способ - построчный импорт (для обратной совместимости)
            field_mapping = {
                'code': ['code', 'код', 'id', 'attribute_code'],
                'name': ['name', 'название', 'title', 'attribute_name'],
                'type': ['type', 'тип', 'attribute_type'],
                'description': ['description', 'описание', 'desc'],
                'unit': ['unit', 'единица', 'единица_измерения', 'unit_of_measure'],
                'is_unique': ['is_unique', 'уникальный', 'unique', 'isunique']
            }
            
            for row_num, row_data in enumerate(data, start=2):
                try:
                    # Нормализовать ключи
                    normalized_row = {}
                    for key, value in row_data.items():
                        normalized_key = key.lower().strip().replace(' ', '_')
                        normalized_row[normalized_key] = value
                    
                    # Маппинг полей
                    mapped_data = {}
                    for target_field, possible_fields in field_mapping.items():
                        for field in possible_fields:
                            if field in normalized_row:
                                mapped_data[target_field] = normalized_row[field]
                                break
                    
                    # Обязательные поля
                    if not mapped_data.get('name'):
                        errors.append(f"Строка {row_num}: Отсутствует название атрибута")
                        continue
                    
                    # Автоматическая генерация кода
                    code = mapped_data.get('code')
                    if not code or code.strip() == '':
                        code = generate_attribute_code_from_name(mapped_data['name'])
                    mapped_data['code'] = code
                    
                    if not mapped_data.get('type'):
                        errors.append(f"Строка {row_num}: Отсутствует тип атрибута")
                        continue
                    
                    # Преобразовать тип
                    type_str = str(mapped_data['type']).lower().strip()
                    type_mapping = {
                        'text': AttributeType.TEXT, 'текст': AttributeType.TEXT,
                        'number': AttributeType.NUMBER, 'число': AttributeType.NUMBER,
                        'date': AttributeType.DATE, 'дата': AttributeType.DATE,
                        'boolean': AttributeType.BOOLEAN, 'булево': AttributeType.BOOLEAN,
                        'url': AttributeType.URL,
                        'image': AttributeType.IMAGE, 'изображение': AttributeType.IMAGE,
                        'select': AttributeType.SELECT, 'выбор': AttributeType.SELECT
                    }
                    
                    attr_type = type_mapping.get(type_str)
                    if not attr_type:
                        errors.append(f"Строка {row_num}: Неверный тип атрибута: {mapped_data['type']}")
                        continue
                    
                    # Проверить существование
                    existing_by_code = Attribute.query.filter_by(code=mapped_data['code']).first()
                    existing_by_name = Attribute.query.filter_by(name=mapped_data['name']).first()
                    
                    if existing_by_code:
                        existing_by_code.name = mapped_data['name']
                        existing_by_code.type = attr_type
                        existing_by_code.description = mapped_data.get('description')
                        existing_by_code.unit = mapped_data.get('unit')
                        updated_count += 1
                    elif existing_by_name:
                        errors.append(f"Строка {row_num}: Атрибут с названием '{mapped_data['name']}' уже существует")
                        continue
                    else:
                        attribute = Attribute(
                            code=mapped_data['code'],
                            name=mapped_data['name'],
                            type=attr_type,
                            description=mapped_data.get('description'),
                            unit=mapped_data.get('unit'),
                            is_unique=bool(mapped_data.get('is_unique', False))
                        )
                        db.session.add(attribute)
                        imported_count += 1
                
                except Exception as e:
                    errors.append(f"Строка {row_num}: {str(e)}")
                    continue
        
        db.session.commit()
        
        return {
            'imported': imported_count,
            'updated': updated_count,
            'errors': errors,
            'warnings': warnings
        }

