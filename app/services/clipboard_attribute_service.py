"""
Полноценный сервис для работы с данными из буфера обмена:
- Парсинг данных
- Маппинг с существующими атрибутами
- Проверка единиц измерения
- Валидация данных
- Импорт атрибутов
"""
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
from app import db
from app.models.attribute import Attribute, AttributeType
from app.utils.attribute_mapper import generate_attribute_code_from_name
from app.services.attribute_preview_service import AttributePreviewService


class ClipboardAttributeService:
    """Полноценный сервис для работы с атрибутами из буфера обмена"""
    
    # Стандартные единицы измерения по типам атрибутов
    STANDARD_UNITS = {
        'length': ['мм', 'см', 'м', 'дм', 'km', 'm', 'cm', 'mm', 'inch', 'ft'],
        'width': ['мм', 'см', 'м', 'дм', 'km', 'm', 'cm', 'mm', 'inch', 'ft'],
        'height': ['мм', 'см', 'м', 'дм', 'km', 'm', 'cm', 'mm', 'inch', 'ft'],
        'depth': ['мм', 'см', 'м', 'дм', 'km', 'm', 'cm', 'mm', 'inch', 'ft'],
        'weight': ['г', 'кг', 'т', 'g', 'kg', 't', 'lb', 'oz'],
        'volume': ['л', 'мл', 'м³', 'л', 'l', 'ml', 'm³', 'm3', 'gal', 'fl oz'],
        'diameter': ['мм', 'см', 'м', 'cm', 'mm', 'm', 'inch'],
        'thickness': ['мм', 'см', 'м', 'cm', 'mm', 'm', 'inch'],
        'temperature': ['°C', '°F', 'K', 'C', 'F'],
        'pressure': ['Па', 'кПа', 'МПа', 'бар', 'атм', 'Pa', 'kPa', 'MPa', 'bar', 'atm', 'psi'],
        'power': ['Вт', 'кВт', 'МВт', 'W', 'kW', 'MW', 'hp'],
        'voltage': ['В', 'кВ', 'V', 'kV'],
        'frequency': ['Гц', 'кГц', 'МГц', 'Hz', 'kHz', 'MHz'],
        'speed': ['м/с', 'км/ч', 'об/мин', 'm/s', 'km/h', 'rpm'],
        'time': ['сек', 'мин', 'ч', 'дн', 's', 'min', 'h', 'd', 'day'],
        'quantity': ['шт', 'ед', 'pcs', 'pcs.', 'units', 'unit'],
        'area': ['м²', 'см²', 'мм²', 'm²', 'm2', 'cm²', 'cm2', 'mm²', 'mm2', 'sq ft'],
        'price': ['руб', '₽', 'RUB', 'USD', '$', 'EUR', '€'],
    }
    
    # Маппинг названий атрибутов на типы единиц измерения
    ATTRIBUTE_UNIT_TYPES = {
        'длина': 'length', 'length': 'length', 'высота': 'height', 'height': 'height',
        'ширина': 'width', 'width': 'width', 'глубина': 'depth', 'depth': 'depth',
        'вес': 'weight', 'weight': 'weight', 'масса': 'weight', 'mass': 'weight',
        'объем': 'volume', 'volume': 'volume', 'объём': 'volume',
        'диаметр': 'diameter', 'diameter': 'diameter',
        'толщина': 'thickness', 'thickness': 'thickness',
        'температура': 'temperature', 'temperature': 'temperature',
        'давление': 'pressure', 'pressure': 'pressure',
        'мощность': 'power', 'power': 'power',
        'напряжение': 'voltage', 'voltage': 'voltage',
        'частота': 'frequency', 'frequency': 'frequency',
        'скорость': 'speed', 'speed': 'speed',
        'время': 'time', 'time': 'time',
        'количество': 'quantity', 'quantity': 'quantity',
        'площадь': 'area', 'area': 'area',
        'цена': 'price', 'price': 'price', 'стоимость': 'price', 'cost': 'price',
    }
    
    @staticmethod
    def parse_clipboard_data(clipboard_text: str) -> Dict:
        """
        Парсинг данных из буфера обмена
        
        Args:
            clipboard_text: Текст из буфера обмена
        
        Returns:
            dict: Результат парсинга с колонками и данными
        """
        try:
            preview_result = AttributePreviewService.preview_clipboard_data(clipboard_text)
            return preview_result
        except Exception as e:
            raise ValueError(f"Ошибка при парсинге данных из буфера: {str(e)}")
    
    @staticmethod
    def suggest_mapping(columns: List[str], existing_attributes: List[Dict]) -> Dict:
        """
        Предложить маппинг колонок с существующими атрибутами
        
        Args:
            columns: Список названий колонок
            existing_attributes: Список существующих атрибутов [{'code': '...', 'name': '...', 'unit': '...', 'type': '...'}]
        
        Returns:
            dict: {
                'column_name': {
                    'attribute_code': '...',  # код существующего атрибута или None
                    'attribute_name': '...',  # название существующего атрибута
                    'is_new': True/False,     # новый атрибут или существующий
                    'match_score': 0.0-1.0,   # оценка совпадения
                    'suggested_type': '...',  # предложенный тип
                    'suggested_unit': '...',  # предложенная единица измерения
                    'unit_validation': {...} # результаты проверки единицы измерения
                }
            }
        """
        mapping = {}
        
        # Нормализовать колонки
        normalized_columns = {}
        for col in columns:
            normalized = col.lower().strip().replace(' ', '_').replace('-', '_')
            normalized_columns[normalized] = col
        
        # Создать индекс существующих атрибутов
        attr_index = {}
        for attr in existing_attributes:
            code = attr.get('code', '').lower().strip()
            name = attr.get('name', '').lower().strip()
            attr_index[code] = attr
            attr_index[name] = attr
            
            # Также индексировать по транслитерации
            try:
                from transliterate import translit
                name_translit = translit(name, 'ru', reversed=True).lower().strip()
                if name_translit != name:
                    attr_index[name_translit] = attr
            except:
                pass
        
        # Для каждой колонки найти лучшее совпадение
        for column in columns:
            column_lower = column.lower().strip()
            column_normalized = column_lower.replace(' ', '_').replace('-', '_')
            
            best_match = None
            best_score = 0.0
            best_attr = None
            
            # Поиск точного совпадения
            if column_lower in attr_index:
                best_attr = attr_index[column_lower]
                best_score = 1.0
            elif column_normalized in attr_index:
                best_attr = attr_index[column_normalized]
                best_score = 0.95
            
            # Поиск частичного совпадения
            if not best_attr:
                for key, attr in attr_index.items():
                    # Проверить вхождение
                    if column_lower in key or key in column_lower:
                        score = len(column_lower) / max(len(column_lower), len(key))
                        if score > best_score:
                            best_score = score
                            best_attr = attr
                    
                    # Проверить схожесть строк
                    similarity = SequenceMatcher(None, column_lower, key).ratio()
                    if similarity > best_score and similarity > 0.6:
                        best_score = similarity
                        best_attr = attr
            
            # Определить тип и единицу измерения
            suggested_type = ClipboardAttributeService._suggest_attribute_type(column)
            suggested_unit = ClipboardAttributeService._suggest_unit(column)
            
            # Проверить единицу измерения
            unit_validation = None
            if best_attr:
                existing_unit = best_attr.get('unit')
                if existing_unit:
                    unit_validation = ClipboardAttributeService.validate_unit(
                        suggested_unit, existing_unit, column
                    )
            
            if best_attr and best_score > 0.6:
                mapping[column] = {
                    'attribute_code': best_attr.get('code'),
                    'attribute_name': best_attr.get('name'),
                    'is_new': False,
                    'match_score': best_score,
                    'suggested_type': suggested_type,
                    'suggested_unit': suggested_unit,
                    'existing_unit': best_attr.get('unit'),
                    'unit_validation': unit_validation
                }
            else:
                mapping[column] = {
                    'attribute_code': None,
                    'attribute_name': None,
                    'is_new': True,
                    'match_score': best_score if best_attr else 0.0,
                    'suggested_type': suggested_type,
                    'suggested_unit': suggested_unit,
                    'existing_unit': None,
                    'unit_validation': None
                }
        
        return mapping
    
    @staticmethod
    def _suggest_attribute_type(column_name: str) -> str:
        """
        Предложить тип атрибута на основе названия колонки
        
        Args:
            column_name: Название колонки
        
        Returns:
            str: Тип атрибута (text, number, date, boolean, url, image, 3d_model)
        """
        name_lower = column_name.lower()
        
        # Изображения и 3D модели
        if any(word in name_lower for word in ['фото', 'изображение', 'картинка', 'image', 'photo', 'picture', 'img']):
            return 'image'
        if any(word in name_lower for word in ['3d', '3д', '3d_model', '3dmodel', 'модель_3d', 'модель3d']):
            # Проверить, есть ли тип THREE_D_MODEL в AttributeType
            try:
                if hasattr(AttributeType, 'THREE_D_MODEL'):
                    return '3d_model'
            except:
                pass
            return 'image'  # Fallback на image, если 3d_model не поддерживается
        
        # URL
        if any(word in name_lower for word in ['url', 'ссылка', 'link', 'href']):
            return 'url'
        
        # Дата
        if any(word in name_lower for word in ['дата', 'date', 'время', 'time', 'создан', 'created', 'обновлен', 'updated']):
            return 'date'
        
        # Boolean
        if any(word in name_lower for word in ['есть', 'нет', 'да', 'нет', 'включен', 'выключен', 'yes', 'no', 'true', 'false', 'bool']):
            return 'boolean'
        
        # Числовые типы
        numeric_keywords = [
            'вес', 'масса', 'weight', 'mass',
            'длина', 'ширина', 'высота', 'глубина', 'length', 'width', 'height', 'depth',
            'диаметр', 'diameter', 'толщина', 'thickness',
            'объем', 'объём', 'volume',
            'цена', 'стоимость', 'price', 'cost',
            'количество', 'quantity', 'count',
            'мощность', 'power', 'напряжение', 'voltage',
            'температура', 'temperature', 'давление', 'pressure'
        ]
        
        if any(keyword in name_lower for keyword in numeric_keywords):
            return 'number'
        
        # По умолчанию - текст
        return 'text'
    
    @staticmethod
    def _suggest_unit(column_name: str) -> Optional[str]:
        """
        Предложить единицу измерения на основе названия колонки
        
        Args:
            column_name: Название колонки
        
        Returns:
            str или None: Предложенная единица измерения
        """
        name_lower = column_name.lower()
        
        # Определить тип единицы измерения
        unit_type = None
        for keyword, utype in ClipboardAttributeService.ATTRIBUTE_UNIT_TYPES.items():
            if keyword in name_lower:
                unit_type = utype
                break
        
        if not unit_type:
            return None
        
        # Извлечь единицу измерения из названия, если она указана
        # Например: "Длина (мм)", "Высота, см", "Вес кг"
        unit_patterns = [
            r'\(([^)]+)\)',  # В скобках
            r',\s*([а-яa-z]+)',  # После запятой
            r'\s+([а-яa-z]+)$',  # В конце
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, name_lower)
            if match:
                potential_unit = match.group(1).strip()
                # Проверить, что это валидная единица для данного типа
                if unit_type in ClipboardAttributeService.STANDARD_UNITS:
                    standard_units = ClipboardAttributeService.STANDARD_UNITS[unit_type]
                    for std_unit in standard_units:
                        if potential_unit.lower() in std_unit.lower() or std_unit.lower() in potential_unit.lower():
                            return std_unit
        
        # Если единица не найдена в названии, предложить стандартную
        if unit_type in ClipboardAttributeService.STANDARD_UNITS:
            return ClipboardAttributeService.STANDARD_UNITS[unit_type][0]
        
        return None
    
    @staticmethod
    def validate_unit(suggested_unit: Optional[str], existing_unit: Optional[str], column_name: str) -> Dict:
        """
        Проверить совместимость единиц измерения
        
        Args:
            suggested_unit: Предложенная единица измерения
            existing_unit: Существующая единица измерения атрибута
            column_name: Название колонки (для контекста)
        
        Returns:
            dict: {
                'is_valid': True/False,
                'is_compatible': True/False,
                'message': '...',
                'suggested_unit': '...',
                'existing_unit': '...'
            }
        """
        if not existing_unit:
            return {
                'is_valid': True,
                'is_compatible': True,
                'message': 'Единица измерения не задана у существующего атрибута',
                'suggested_unit': suggested_unit,
                'existing_unit': None
            }
        
        if not suggested_unit:
            return {
                'is_valid': True,
                'is_compatible': True,
                'message': 'Единица измерения не указана для новой колонки',
                'suggested_unit': None,
                'existing_unit': existing_unit
            }
        
        # Нормализовать единицы измерения
        suggested_norm = suggested_unit.lower().strip()
        existing_norm = existing_unit.lower().strip()
        
        # Точное совпадение
        if suggested_norm == existing_norm:
            return {
                'is_valid': True,
                'is_compatible': True,
                'message': 'Единицы измерения совпадают',
                'suggested_unit': suggested_unit,
                'existing_unit': existing_unit
            }
        
        # Проверить совместимость по типам
        suggested_type = ClipboardAttributeService._get_unit_type(suggested_norm)
        existing_type = ClipboardAttributeService._get_unit_type(existing_norm)
        
        if suggested_type and existing_type and suggested_type == existing_type:
            return {
                'is_valid': True,
                'is_compatible': True,
                'message': f'Единицы измерения совместимы (тип: {suggested_type})',
                'suggested_unit': suggested_unit,
                'existing_unit': existing_unit,
                'unit_type': suggested_type
            }
        
        # Несовместимые единицы
        return {
            'is_valid': False,
            'is_compatible': False,
            'message': f'⚠️ Внимание: несовместимые единицы измерения! Предложено: "{suggested_unit}", у атрибута: "{existing_unit}"',
            'suggested_unit': suggested_unit,
            'existing_unit': existing_unit,
            'warning': True
        }
    
    @staticmethod
    def _get_unit_type(unit: str) -> Optional[str]:
        """
        Определить тип единицы измерения
        
        Args:
            unit: Единица измерения
        
        Returns:
            str или None: Тип единицы измерения
        """
        unit_lower = unit.lower().strip()
        
        for unit_type, units in ClipboardAttributeService.STANDARD_UNITS.items():
            for std_unit in units:
                if unit_lower == std_unit.lower() or unit_lower in std_unit.lower() or std_unit.lower() in unit_lower:
                    return unit_type
        
        return None
    
    @staticmethod
    def validate_mapping(mapping: Dict, columns: List[str]) -> Tuple[bool, List[str]]:
        """
        Валидация маппинга перед импортом
        
        Args:
            mapping: Словарь маппинга
            columns: Список колонок
        
        Returns:
            tuple: (is_valid, errors)
        """
        errors = []
        
        # Проверить, что все колонки имеют маппинг
        for column in columns:
            if column not in mapping:
                errors.append(f"Колонка '{column}' не имеет маппинга")
                continue
            
            map_info = mapping[column]
            
            # Если это новый атрибут, проверить обязательные поля
            if map_info.get('is_new', True):
                if not map_info.get('type'):
                    errors.append(f"Колонка '{column}': не указан тип атрибута")
                
                # Проверить уникальность названия
                name = column
                existing = Attribute.query.filter_by(name=name).first()
                if existing:
                    errors.append(f"Колонка '{column}': атрибут с таким названием уже существует")
            else:
                # Если это существующий атрибут, проверить его наличие
                attr_code = map_info.get('attribute_code')
                if not attr_code:
                    errors.append(f"Колонка '{column}': не указан код существующего атрибута")
                else:
                    existing = Attribute.query.filter_by(code=attr_code).first()
                    if not existing:
                        errors.append(f"Колонка '{column}': атрибут с кодом '{attr_code}' не найден")
                    
                    # Проверить единицы измерения
                    unit_validation = map_info.get('unit_validation')
                    if unit_validation and not unit_validation.get('is_compatible', True):
                        errors.append(f"Колонка '{column}': {unit_validation.get('message', 'Несовместимые единицы измерения')}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def import_attributes(clipboard_text: str, mapping: Dict) -> Dict:
        """
        Импортировать атрибуты из буфера обмена с маппингом
        
        Args:
            clipboard_text: Текст из буфера обмена
            mapping: Словарь маппинга {column_name: {attribute_code, is_new, type, unit, ...}}
        
        Returns:
            dict: Результаты импорта
        """
        from app.services.attribute_import_service import AttributeImportService
        
        # Валидация маппинга
        preview_result = ClipboardAttributeService.parse_clipboard_data(clipboard_text)
        original_columns = preview_result['sheets'][0]['columns']  # Оригинальные названия из данных
        
        # Создать маппинг оригинальных названий на отредактированные
        # Если пользователь отредактировал название, нужно найти соответствие
        column_name_mapping = {}  # отредактированное -> оригинальное
        
        for edited_name in mapping.keys():
            # Попробовать найти точное совпадение
            if edited_name in original_columns:
                column_name_mapping[edited_name] = edited_name
            else:
                # Попробовать найти похожую колонку
                found = False
                for orig_name in original_columns:
                    # Проверить начало названия
                    if orig_name.startswith(edited_name[:10]) or edited_name.startswith(orig_name[:10]):
                        column_name_mapping[edited_name] = orig_name
                        found = True
                        break
                if not found:
                    # Если не найдено, использовать первое доступное название
                    # или пропустить
                    from flask import current_app
                    if current_app:
                        current_app.logger.warning(f"Колонка '{edited_name}' не найдена в оригинальных колонках: {original_columns}")
        
        # Валидация маппинга использует отредактированные названия
        is_valid, errors = ClipboardAttributeService.validate_mapping(mapping, list(mapping.keys()))
        if not is_valid:
            return {
                'success': False,
                'imported': 0,
                'updated': 0,
                'errors': errors,
                'warnings': []
            }
        
        # Импорт через существующий сервис
        try:
            from flask import current_app
            if current_app and current_app.config.get('DEBUG'):
                current_app.logger.debug(f"ClipboardAttributeService.import_attributes: mapping keys={list(mapping.keys()) if mapping else []}, clipboard_text length={len(clipboard_text)}")
            
            result = AttributeImportService.import_from_clipboard(clipboard_text, mapping=mapping)
            result['success'] = True
            if current_app and current_app.config.get('DEBUG'):
                current_app.logger.debug(f"ClipboardAttributeService.import_attributes: result success={result.get('success', False)}, imported={result.get('imported', 0)}")
            return result
        except Exception as e:
            from flask import current_app
            if current_app:
                current_app.logger.error(f"ClipboardAttributeService.import_attributes: Exception = {str(e)}", exc_info=True)
            return {
                'success': False,
                'imported': 0,
                'updated': 0,
                'errors': [str(e)],
                'warnings': []
            }

