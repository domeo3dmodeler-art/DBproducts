"""
Утилиты для генерации кодов категорий и подкатегорий
"""
from app import db
from app.models.category import ProductCategory
from app.models.subcategory import Subcategory

def generate_category_code():
    """
    Генерирует автоматический код для категории в формате 01, 02, 03...
    
    Returns:
        str: Код категории
    """
    # Найти максимальный числовой код
    categories = ProductCategory.query.all()
    max_num = 0
    
    for category in categories:
        try:
            # Попробовать извлечь число из кода
            num = int(category.code)
            if num > max_num:
                max_num = num
        except (ValueError, TypeError):
            # Если код не числовой, пропустить
            continue
    
    # Следующий номер
    next_num = max_num + 1
    
    # Форматировать с ведущим нулем (01, 02, ..., 10, 11, ...)
    return f"{next_num:02d}"

def generate_subcategory_code(category_id):
    """
    Генерирует автоматический код для подкатегории в формате XX_Y
    где XX - код категории, Y - номер подкатегории в категории
    
    Args:
        category_id: ID категории
    
    Returns:
        str: Код подкатегории
    """
    category = ProductCategory.query.get(category_id)
    if not category:
        raise ValueError(f"Категория с ID {category_id} не найдена")
    
    category_code = category.code
    
    # Найти все подкатегории в этой категории
    subcategories = Subcategory.query.filter_by(category_id=category_id).all()
    
    # Найти максимальный номер подкатегории
    max_num = 0
    for subcat in subcategories:
        # Код подкатегории должен быть в формате XX_Y
        if '_' in subcat.code:
            try:
                parts = subcat.code.split('_')
                if parts[0] == category_code:
                    num = int(parts[1])
                    if num > max_num:
                        max_num = num
            except (ValueError, IndexError):
                continue
    
    # Следующий номер
    next_num = max_num + 1
    
    # Форматировать как XX_Y
    return f"{category_code}_{next_num}"

