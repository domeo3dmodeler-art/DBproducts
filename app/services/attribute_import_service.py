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
    def import_from_file(file_path):
        """
        Импортировать атрибуты из файла
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            dict: Результаты импорта
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        # Определить формат файла и получить данные
        if file_extension in ['.xlsx', '.xls']:
            data, total_rows = AttributeImportService._parse_excel(file_path)
        elif file_extension == '.csv':
            data, total_rows = AttributeImportService._parse_csv(file_path)
        elif file_extension == '.json':
            data, total_rows = AttributeImportService._parse_json(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")
        
        # Выполнить импорт
        result = AttributeImportService._import_attributes(data)
        result['total_rows'] = total_rows
        return result
    
    @staticmethod
    def _parse_excel(file_path):
        """Парсинг Excel файла"""
        try:
            if file_path.suffix == '.xlsx':
                df = pd.read_excel(file_path, engine='openpyxl')
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
    def _import_attributes(data):
        """
        Импортировать атрибуты из данных
        
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
        
        # Маппинг полей (автоматический)
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
                # Нормализовать ключи (нижний регистр, убрать пробелы)
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
                
                # Автоматическая генерация кода из названия, если не указан
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
                    'text': AttributeType.TEXT,
                    'текст': AttributeType.TEXT,
                    'number': AttributeType.NUMBER,
                    'число': AttributeType.NUMBER,
                    'date': AttributeType.DATE,
                    'дата': AttributeType.DATE,
                    'boolean': AttributeType.BOOLEAN,
                    'булево': AttributeType.BOOLEAN,
                    'url': AttributeType.URL,
                    'image': AttributeType.IMAGE,
                    'изображение': AttributeType.IMAGE,
                    'select': AttributeType.SELECT,
                    'выбор': AttributeType.SELECT
                }
                
                attr_type = type_mapping.get(type_str)
                if not attr_type:
                    errors.append(f"Строка {row_num}: Неверный тип атрибута: {mapped_data['type']}")
                    continue
                
                # Проверить существование атрибута по коду
                existing_by_code = Attribute.query.filter_by(code=mapped_data['code']).first()
                
                # Проверить существование атрибута по названию
                existing_by_name = Attribute.query.filter_by(name=mapped_data['name']).first()
                
                if existing_by_code:
                    # Обновить существующий по коду
                    existing_by_code.name = mapped_data['name']
                    existing_by_code.type = attr_type
                    existing_by_code.description = mapped_data.get('description')
                    existing_by_code.unit = mapped_data.get('unit')
                    if 'is_unique' in mapped_data:
                        existing_by_code.is_unique = bool(mapped_data['is_unique'])
                    updated_count += 1
                elif existing_by_name:
                    # Атрибут с таким названием уже существует
                    errors.append(f"Строка {row_num}: Атрибут с названием '{mapped_data['name']}' уже существует")
                    continue
                else:
                    # Создать новый
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

