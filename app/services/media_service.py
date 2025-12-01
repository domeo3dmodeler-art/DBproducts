"""
Сервис для работы с медиа-файлами товаров
"""
import os
import requests
from pathlib import Path
from urllib.parse import urlparse
from app import db
from app.models.product_media import ProductMedia, MediaType
from app.models.attribute import AttributeType
from config import Config
from PIL import Image
import io

class MediaService:
    """Сервис для скачивания и хранения медиа-файлов"""
    
    # Расширения для изображений
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
    
    # Расширения для 3D моделей
    MODEL_EXTENSIONS = {'.glb', '.gltf', '.obj', '.fbx', '.dae', '.3ds', '.stl', '.ply'}
    
    # MIME типы для изображений
    IMAGE_MIME_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/webp', 'image/bmp', 'image/svg+xml'
    }
    
    # MIME типы для 3D моделей
    MODEL_MIME_TYPES = {
        'model/gltf-binary', 'model/gltf+json', 'model/obj',
        'application/octet-stream'  # Для некоторых форматов
    }
    
    @staticmethod
    def download_and_save_media(product, attribute_code, url, sort_order=0):
        """
        Скачать медиа-файл по URL и сохранить в базу данных
        
        Args:
            product: Объект Product
            attribute_code: Код атрибута (для связи)
            url: URL медиа-файла
            sort_order: Порядок сортировки
        
        Returns:
            ProductMedia: Созданный объект медиа-файла или None при ошибке
        """
        try:
            # Определить тип медиа-файла
            media_type = MediaService._detect_media_type(url)
            if not media_type:
                return None
            
            # Скачать файл
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Получить информацию о файле
            content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
            file_size = int(response.headers.get('Content-Length', 0))
            
            # Проверить размер файла
            if media_type == MediaType.IMAGE and file_size > Config.MAX_IMAGE_SIZE:
                return None
            if media_type == MediaType.THREE_D_MODEL and file_size > Config.MAX_MODEL_SIZE:
                return None
            
            # Определить расширение и имя файла
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)
            if not original_filename or '.' not in original_filename:
                # Сгенерировать имя файла
                ext = MediaService._get_extension_from_mime(content_type, media_type)
                original_filename = f"{product.sku}_{attribute_code}_{sort_order}{ext}"
            
            # Создать директории
            if media_type == MediaType.IMAGE:
                media_folder = Config.IMAGES_FOLDER
            else:
                media_folder = Config.MODELS_FOLDER
            
            # Создать папки, если их нет
            os.makedirs(media_folder, exist_ok=True)
            
            # Сгенерировать уникальное имя файла
            file_name = MediaService._generate_unique_filename(media_folder, original_filename, product.id)
            file_path = media_folder / file_name
            
            # Сохранить файл
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Получить реальный размер файла
            actual_size = file_path.stat().st_size
            
            # Получить атрибут
            from app.models.attribute import Attribute
            attribute = Attribute.query.filter_by(code=attribute_code).first()
            
            # Метаданные для изображений
            width = None
            height = None
            if media_type == MediaType.IMAGE:
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                except Exception:
                    pass
            
            # Метаданные для 3D моделей
            model_format = None
            if media_type == MediaType.THREE_D_MODEL:
                model_format = Path(file_name).suffix.lower()
            
            # Создать запись в БД
            media = ProductMedia(
                product_id=product.id,
                attribute_id=attribute.id if attribute else None,
                media_type=media_type,
                original_url=url,
                file_path=str(file_path.relative_to(Config.basedir)),
                file_name=file_name,
                file_size=actual_size,
                mime_type=content_type,
                width=width,
                height=height,
                model_format=model_format,
                sort_order=sort_order
            )
            
            db.session.add(media)
            db.session.commit()
            
            return media
            
        except Exception as e:
            from flask import current_app
            if current_app:
                current_app.logger.error(f"Ошибка при скачивании медиа-файла {url}: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def _detect_media_type(url):
        """Определить тип медиа-файла по URL"""
        url_lower = url.lower()
        
        # Проверить расширение файла
        parsed = urlparse(url)
        path = parsed.path.lower()
        ext = Path(path).suffix
        
        # Ключевые слова для 3D моделей
        model_keywords = ['3d', 'model', 'glb', 'gltf', 'obj', 'fbx', 'dae', '3ds', 'stl']
        
        if ext in MediaService.MODEL_EXTENSIONS or any(kw in url_lower for kw in model_keywords):
            return MediaType.THREE_D_MODEL
        
        if ext in MediaService.IMAGE_EXTENSIONS:
            return MediaType.IMAGE
        
        # По умолчанию считаем изображением
        return MediaType.IMAGE
    
    @staticmethod
    def _get_extension_from_mime(mime_type, media_type):
        """Получить расширение файла из MIME типа"""
        mime_to_ext = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/bmp': '.bmp',
            'image/svg+xml': '.svg',
            'model/gltf-binary': '.glb',
            'model/gltf+json': '.gltf',
            'model/obj': '.obj',
        }
        
        ext = mime_to_ext.get(mime_type)
        if ext:
            return ext
        
        # По умолчанию
        if media_type == MediaType.IMAGE:
            return '.jpg'
        else:
            return '.glb'
    
    @staticmethod
    def _generate_unique_filename(folder, filename, product_id):
        """Сгенерировать уникальное имя файла"""
        base_name = Path(filename).stem
        ext = Path(filename).suffix
        
        counter = 1
        while True:
            if counter == 1:
                new_filename = f"{product_id}_{base_name}{ext}"
            else:
                new_filename = f"{product_id}_{base_name}_{counter}{ext}"
            
            if not (folder / new_filename).exists():
                return new_filename
            
            counter += 1
    
    @staticmethod
    def process_product_media(product, auto_download=True):
        """
        Обработать все медиа-файлы товара (скачать и сохранить)
        
        Args:
            product: Объект Product
            auto_download: Автоматически скачивать файлы
        
        Returns:
            dict: Статистика обработки
        """
        from app.models.attribute import AttributeType
        
        stats = {
            'images_found': 0,
            'images_downloaded': 0,
            'models_found': 0,
            'models_downloaded': 0,
            'errors': []
        }
        
        # Найти все атрибуты типа IMAGE
        image_attrs = [pav for pav in product.attribute_values.all() 
                      if pav.attribute.type == AttributeType.IMAGE]
        
        # Найти все атрибуты типа URL (могут быть 3D модели)
        url_attrs = [pav for pav in product.attribute_values.all() 
                    if pav.attribute.type == AttributeType.URL]
        
        # Обработать изображения
        for pav in image_attrs:
            if not pav.value or not pav.value.strip():
                continue
            
            stats['images_found'] += 1
            
            # Проверить, не скачан ли уже этот файл
            existing = ProductMedia.query.filter_by(
                product_id=product.id,
                attribute_id=pav.attribute_id,
                original_url=pav.value.strip()
            ).first()
            
            if existing:
                continue
            
            if auto_download:
                media = MediaService.download_and_save_media(
                    product, 
                    pav.attribute.code, 
                    pav.value.strip(),
                    sort_order=stats['images_found']
                )
                if media:
                    stats['images_downloaded'] += 1
                else:
                    stats['errors'].append(f"Не удалось скачать изображение: {pav.value}")
        
        # Обработать URL (проверить на 3D модели)
        for pav in url_attrs:
            if not pav.value or not pav.value.strip():
                continue
            
            url = pav.value.strip()
            media_type = MediaService._detect_media_type(url)
            
            if media_type == MediaType.THREE_D_MODEL:
                stats['models_found'] += 1
                
                # Проверить, не скачан ли уже этот файл
                existing = ProductMedia.query.filter_by(
                    product_id=product.id,
                    attribute_id=pav.attribute_id,
                    original_url=url
                ).first()
                
                if existing:
                    continue
                
                if auto_download:
                    media = MediaService.download_and_save_media(
                        product,
                        pav.attribute.code,
                        url,
                        sort_order=stats['models_found']
                    )
                    if media:
                        stats['models_downloaded'] += 1
                    else:
                        stats['errors'].append(f"Не удалось скачать 3D модель: {url}")
        
        return stats

