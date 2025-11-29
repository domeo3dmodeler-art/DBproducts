"""
Утилиты для маппинга русских названий атрибутов на английские коды
"""
import re
import unicodedata

# Словарь маппинга русских названий на английские коды
RUSSIAN_TO_ENGLISH_MAP = {
    # Общие
    'название': 'name',
    'описание': 'description',
    'вес': 'weight',
    'длина': 'length',
    'ширина': 'width',
    'высота': 'height',
    'глубина': 'depth',
    'цвет': 'color',
    'материал': 'material',
    'размер': 'size',
    'цена': 'price',
    'количество': 'quantity',
    'артикул': 'sku',
    'бренд': 'brand',
    'производитель': 'manufacturer',
    'модель': 'model',
    'серия': 'series',
    'коллекция': 'collection',
    'страна': 'country',
    'гарантия': 'warranty',
    'изображение': 'image',
    'фото': 'photo',
    'видео': 'video',
    'ссылка': 'url',
    'дата': 'date',
    'время': 'time',
    'статус': 'status',
    'тип': 'type',
    'категория': 'category',
    'подкатегория': 'subcategory',
    'единица': 'unit',
    'измерения': 'measurement',
    'объем': 'volume',
    'площадь': 'area',
    'диаметр': 'diameter',
    'радиус': 'radius',
    'мощность': 'power',
    'напряжение': 'voltage',
    'ток': 'current',
    'частота': 'frequency',
    'температура': 'temperature',
    'влажность': 'humidity',
    'давление': 'pressure',
    'скорость': 'speed',
    'расход': 'consumption',
    'емкость': 'capacity',
    'ресурс': 'resource',
    'срок': 'lifetime',
    'эксплуатации': 'service_life',
}

def transliterate_russian_to_english(text):
    """
    Транслитерирует русский текст в английский
    
    Args:
        text: Русский текст
    
    Returns:
        str: Английский текст
    """
    if not text:
        return ''
    
    # Нормализовать текст (нижний регистр, убрать лишние пробелы)
    text = text.lower().strip()
    
    # Сначала проверить словарь
    if text in RUSSIAN_TO_ENGLISH_MAP:
        return RUSSIAN_TO_ENGLISH_MAP[text]
    
    # Транслитерация по символам
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    
    result = []
    for char in text:
        if char in translit_map:
            result.append(translit_map[char])
        elif char.isalnum() or char in ['_', '-']:
            result.append(char)
        elif char == ' ':
            result.append('_')
    
    code = ''.join(result)
    
    # Убрать множественные подчеркивания
    code = re.sub(r'_+', '_', code)
    
    # Убрать подчеркивания в начале и конце
    code = code.strip('_')
    
    return code

def generate_attribute_code_from_name(name):
    """
    Генерирует английский код атрибута из русского названия
    
    Args:
        name: Русское название атрибута
    
    Returns:
        str: Английский код
    """
    return transliterate_russian_to_english(name)

