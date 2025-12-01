"""
Валидаторы для проверки данных
"""
import re
from urllib.parse import urlparse
from PIL import Image
import requests
from io import BytesIO

def validate_email(email):
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url):
    """Валидация URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def validate_image_url(url, min_resolution=(800, 600)):
    """
    Валидация URL изображения
    
    Returns:
        tuple: (is_valid, width, height, format, error_message)
    """
    try:
        response = requests.get(url, timeout=10, stream=True)
        response.raise_for_status()
        
        # Проверить Content-Type
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            return False, 0, 0, None, f'Неверный Content-Type: {content_type}'
        
        # Загрузить изображение
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        
        # Проверить разрешение
        if width < min_resolution[0] or height < min_resolution[1]:
            return False, width, height, img.format, f'Низкое разрешение: {width}x{height}'
        
        return True, width, height, img.format, None
        
    except requests.exceptions.RequestException as e:
        return False, 0, 0, None, f'Ошибка загрузки: {str(e)}'
    except Exception as e:
        return False, 0, 0, None, f'Ошибка обработки: {str(e)}'

def validate_3d_model_url(url):
    """
    Валидация URL 3D модели
    
    Returns:
        tuple: (is_valid, format, error_message)
    """
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        # Проверить расширение файла
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        valid_extensions = ['.glb', '.gltf', '.obj', '.fbx', '.dae', '.3ds']
        if not any(path.endswith(ext) for ext in valid_extensions):
            return False, None, 'Неподдерживаемый формат 3D модели'
        
        # Определить формат
        for ext in valid_extensions:
            if path.endswith(ext):
                format_name = ext[1:].upper()
                return True, format_name, None
        
        return False, None, 'Не удалось определить формат'
        
    except requests.exceptions.RequestException as e:
        return False, None, f'Ошибка загрузки: {str(e)}'
    except Exception as e:
        return False, None, f'Ошибка обработки: {str(e)}'

def sanitize_filename(filename):
    """Очистка имени файла от опасных символов"""
    import os
    # Удалить опасные символы
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Ограничить длину
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    return filename

