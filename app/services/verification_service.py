"""
Сервис верификации данных товаров
"""
from app import db
from app.models.product import Product, ProductStatus
from app.models.verification import ProductVerification, VerificationIssue, IssueType
from app.models.subcategory_attribute import SubcategoryAttribute
from app.models.attribute import AttributeType
from datetime import datetime
import requests
from PIL import Image
import io
import re

class VerificationService:
    """Сервис для верификации товаров"""
    
    @staticmethod
    def verify_product(product, user=None):
        """
        Выполнить полную верификацию товара
        
        Returns:
            ProductVerification: объект с результатами верификации
        """
        verification = ProductVerification(
            product_id=product.id,
            verified_by_id=user.id if user else None,
            verified_at=datetime.utcnow()
        )
        
        # Проверка полноты данных
        completeness_score, completeness_issues = VerificationService._check_completeness(product)
        verification.completeness_score = completeness_score
        
        # Проверка качества данных
        quality_score, quality_issues = VerificationService._check_quality(product)
        verification.quality_score = quality_score
        
        # Проверка медиа-контента
        media_score, media_issues = VerificationService._check_media(product)
        verification.media_score = media_score
        
        # Расчет общей оценки (взвешенная сумма)
        verification.overall_score = int(
            completeness_score * 0.4 + 
            quality_score * 0.4 + 
            media_score * 0.2
        )
        
        db.session.add(verification)
        
        # Сохранить все проблемы
        all_issues = completeness_issues + quality_issues + media_issues
        for issue_data in all_issues:
            issue = VerificationIssue(
                verification_id=verification.id,
                issue_type=issue_data['type'],
                attribute_id=issue_data.get('attribute_id'),
                message=issue_data['message'],
                severity=issue_data.get('severity', 'warning')
            )
            db.session.add(issue)
        
        db.session.commit()
        
        # Автоматический переход статуса на основе оценки
        VerificationService._update_status_based_on_score(product, verification.overall_score)
        
        return verification
    
    @staticmethod
    def _check_completeness(product):
        """
        Проверить полноту данных
        
        Returns:
            tuple: (score 0-100, list of issues)
        """
        # Получить обязательные атрибуты для подкатегории
        required_attrs = product.subcategory.get_required_attributes()
        
        if not required_attrs:
            return 100, []  # Нет обязательных атрибутов - все заполнено
        
        total_required = len(required_attrs)
        filled_count = 0
        issues = []
        
        for subcat_attr in required_attrs:
            attribute = subcat_attr.attribute
            pav = product.attribute_values.filter_by(attribute_id=attribute.id).first()
            
            if pav and pav.value and pav.value.strip():
                filled_count += 1
            else:
                issues.append({
                    'type': IssueType.MISSING_REQUIRED,
                    'attribute_id': attribute.id,
                    'message': f'Отсутствует обязательное поле: {attribute.name}',
                    'severity': 'error'
                })
        
        score = int((filled_count / total_required) * 100) if total_required > 0 else 100
        
        return score, issues
    
    @staticmethod
    def _check_quality(product):
        """
        Проверить качество данных
        
        Returns:
            tuple: (score 0-100, list of issues)
        """
        issues = []
        total_attrs = 0
        valid_attrs = 0
        
        # Проверить все атрибуты товара
        for pav in product.attribute_values.all():
            total_attrs += 1
            attribute = pav.attribute
            value = pav.value
            
            if not value or not value.strip():
                continue  # Пустые значения уже проверены в полноте
            
            # Проверка типа данных
            if not VerificationService._validate_attribute_type(attribute, value):
                issues.append({
                    'type': IssueType.INVALID_TYPE,
                    'attribute_id': attribute.id,
                    'message': f'Неверный тип данных для атрибута {attribute.name}',
                    'severity': 'error'
                })
                continue
            
            # Проверка правил валидации
            if attribute.validation_rules:
                if not VerificationService._validate_rules(attribute, value):
                    issues.append({
                        'type': IssueType.INVALID_VALUE,
                        'attribute_id': attribute.id,
                        'message': f'Значение не соответствует правилам валидации для {attribute.name}',
                        'severity': 'warning'
                    })
                    continue
            
            # Проверка уникальности (для атрибутов с флагом is_unique)
            if attribute.is_unique:
                duplicate = VerificationService._check_uniqueness(attribute, value, product)
                if duplicate:
                    issues.append({
                        'type': IssueType.DUPLICATE,
                        'attribute_id': attribute.id,
                        'message': f'Дубликат значения для уникального атрибута {attribute.name}: {value}',
                        'severity': 'error'
                    })
                    continue
            
            valid_attrs += 1
        
        score = int((valid_attrs / total_attrs) * 100) if total_attrs > 0 else 100
        
        return score, issues
    
    @staticmethod
    def _check_media(product):
        """
        Проверить медиа-контент (фото и 3D модели)
        
        Returns:
            tuple: (score 0-100, list of issues)
        """
        issues = []
        score = 100
        
        # Найти атрибуты типа IMAGE
        image_attrs = [pav for pav in product.attribute_values.all() 
                      if pav.attribute.type == AttributeType.IMAGE]
        
        # Найти атрибуты типа URL (могут быть 3D модели)
        url_attrs = [pav for pav in product.attribute_values.all() 
                    if pav.attribute.type == AttributeType.URL]
        
        # Проверка количества изображений
        if not image_attrs:
            issues.append({
                'type': IssueType.MEDIA_COUNT_LOW,
                'message': 'Отсутствуют изображения товара',
                'severity': 'warning'
            })
            score = 50  # Штраф за отсутствие изображений
        elif len(image_attrs) < 3:
            issues.append({
                'type': IssueType.MEDIA_COUNT_LOW,
                'message': f'Мало изображений товара: {len(image_attrs)} (рекомендуется минимум 3)',
                'severity': 'warning'
            })
            score = max(60, score - (3 - len(image_attrs)) * 10)  # Штраф за недостаточное количество
        
        # Проверить каждое изображение
        valid_images = 0
        for pav in image_attrs:
            image_url = pav.value.strip()
            
            if not image_url:
                continue
            
            # Проверка доступности URL
            if not VerificationService._check_image_url(image_url):
                issues.append({
                    'type': IssueType.IMAGE_NOT_ACCESSIBLE,
                    'attribute_id': pav.attribute.id,
                    'message': f'Изображение недоступно: {image_url}',
                    'severity': 'error'
                })
                continue
            
            # Проверка разрешения
            resolution_ok, width, height = VerificationService._check_image_resolution(image_url)
            if not resolution_ok:
                issues.append({
                    'type': IssueType.IMAGE_LOW_RESOLUTION,
                    'attribute_id': pav.attribute.id,
                    'message': f'Низкое разрешение изображения ({width}x{height}): {image_url}',
                    'severity': 'warning'
                })
                # Не считаем невалидным, но снижаем оценку
                continue
            
            # Проверка формата
            format_ok, image_format = VerificationService._check_image_format(image_url)
            if not format_ok:
                issues.append({
                    'type': IssueType.IMAGE_INVALID_FORMAT,
                    'attribute_id': pav.attribute.id,
                    'message': f'Неподдерживаемый формат изображения ({image_format}): {image_url}',
                    'severity': 'warning'
                })
                continue
            
            # Проверка размера файла
            size_ok, file_size = VerificationService._check_image_size(image_url)
            if not size_ok:
                issues.append({
                    'type': IssueType.IMAGE_INVALID_FORMAT,
                    'attribute_id': pav.attribute.id,
                    'message': f'Слишком большой размер файла ({file_size / 1024 / 1024:.1f}MB): {image_url}',
                    'severity': 'warning'
                })
                continue
            
            valid_images += 1
        
        # Пересчитать оценку на основе валидных изображений
        if len(image_attrs) > 0:
            image_score = int((valid_images / len(image_attrs)) * 100)
            score = min(score, image_score)
        
        # Проверка 3D моделей (в URL атрибутах)
        model_attrs = [pav for pav in url_attrs 
                      if VerificationService._is_3d_model_url(pav.value)]
        
        if model_attrs:
            valid_models = 0
            for pav in model_attrs:
                model_url = pav.value.strip()
                
                # Проверка доступности 3D модели
                if VerificationService._check_3d_model_url(model_url):
                    valid_models += 1
                else:
                    issues.append({
                        'type': IssueType.IMAGE_NOT_ACCESSIBLE,
                        'attribute_id': pav.attribute.id,
                        'message': f'3D модель недоступна: {model_url}',
                        'severity': 'warning'
                    })
            
            # Если есть 3D модели, но они недоступны - снижаем оценку
            if len(model_attrs) > 0 and valid_models == 0:
                score = max(0, score - 20)
            elif len(model_attrs) > 0 and valid_models < len(model_attrs):
                score = max(0, score - 10)
        
        return score, issues
    
    @staticmethod
    def _validate_attribute_type(attribute, value):
        """Проверить соответствие типа данных"""
        try:
            if attribute.type == AttributeType.NUMBER:
                float(value)
            elif attribute.type == AttributeType.BOOLEAN:
                value.lower() in ['true', 'false', '1', '0', 'yes', 'no', 'да', 'нет']
            elif attribute.type == AttributeType.DATE:
                from datetime import datetime
                # Попробовать разные форматы даты
                formats = ['%Y-%m-%d', '%d.%m.%Y', '%Y/%m/%d', '%d-%m-%Y']
                parsed = False
                for fmt in formats:
                    try:
                        datetime.strptime(value, fmt)
                        parsed = True
                        break
                    except:
                        continue
                if not parsed:
                    datetime.fromisoformat(value)
            elif attribute.type == AttributeType.SELECT:
                # Проверить, что значение есть в списке допустимых
                allowed_values = [av.value for av in attribute.values.all()]
                return value in allowed_values
            elif attribute.type == AttributeType.URL:
                # Базовая проверка URL
                return value.startswith(('http://', 'https://'))
        except (ValueError, TypeError, AttributeError):
            return False
        
        return True
    
    @staticmethod
    def _validate_rules(attribute, value):
        """Проверить правила валидации"""
        rules = attribute.validation_rules or {}
        
        if attribute.type == AttributeType.NUMBER:
            try:
                num_value = float(value)
                if 'min' in rules and num_value < rules['min']:
                    return False
                if 'max' in rules and num_value > rules['max']:
                    return False
            except (ValueError, TypeError):
                return False
        
        if 'pattern' in rules:
            try:
                if not re.match(rules['pattern'], value):
                    return False
            except:
                pass
        
        if 'min_length' in rules:
            if len(value) < rules['min_length']:
                return False
        
        if 'max_length' in rules:
            if len(value) > rules['max_length']:
                return False
        
        return True
    
    @staticmethod
    def _check_uniqueness(attribute, value, current_product):
        """
        Проверить уникальность значения атрибута
        
        Returns:
            Product or None: Найденный дубликат или None
        """
        from app.models.product_attribute_value import ProductAttributeValue
        
        # Найти другие товары с таким же значением этого атрибута
        duplicate_pav = ProductAttributeValue.query.filter(
            ProductAttributeValue.attribute_id == attribute.id,
            ProductAttributeValue.value == value,
            ProductAttributeValue.product_id != current_product.id
        ).first()
        
        return duplicate_pav.product if duplicate_pav else None
    
    @staticmethod
    def _check_image_url(url):
        """Проверить доступность изображения по URL"""
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def _check_image_resolution(url):
        """Проверить разрешение изображения"""
        from config import Config
        try:
            response = requests.get(url, timeout=10, stream=True)
            if response.status_code != 200:
                return False, 0, 0
            
            img = Image.open(io.BytesIO(response.content))
            width, height = img.size
            min_width, min_height = Config.MIN_IMAGE_RESOLUTION
            
            return width >= min_width and height >= min_height, width, height
        except:
            return False, 0, 0
    
    @staticmethod
    def _check_image_format(url):
        """Проверить формат изображения"""
        ALLOWED_FORMATS = ['JPEG', 'JPG', 'PNG', 'WEBP']
        try:
            response = requests.get(url, timeout=10, stream=True)
            if response.status_code != 200:
                return False, 'unknown'
            
            img = Image.open(io.BytesIO(response.content))
            format_name = img.format
            return format_name in ALLOWED_FORMATS, format_name or 'unknown'
        except:
            return False, 'unknown'
    
    @staticmethod
    def _check_image_size(url):
        """Проверить размер файла изображения"""
        from config import Config
        try:
            response = requests.get(url, timeout=10, stream=True)
            if response.status_code != 200:
                return False, 0
            
            content_length = response.headers.get('content-length')
            if content_length:
                file_size = int(content_length)
                return file_size <= Config.MAX_IMAGE_SIZE, file_size
            
            # Если нет заголовка, проверим размер контента
            content = response.content
            file_size = len(content)
            return file_size <= Config.MAX_IMAGE_SIZE, file_size
        except:
            return False, 0
    
    @staticmethod
    def _is_3d_model_url(url):
        """Проверить, является ли URL ссылкой на 3D модель"""
        if not url:
            return False
        
        url_lower = url.lower()
        # Проверка по расширению файла
        model_extensions = ['.glb', '.gltf', '.obj', '.fbx', '.3ds', '.dae', '.stl']
        if any(url_lower.endswith(ext) for ext in model_extensions):
            return True
        
        # Проверка по ключевым словам в URL
        model_keywords = ['3d', 'model', 'glb', 'gltf', 'obj', 'fbx']
        if any(keyword in url_lower for keyword in model_keywords):
            return True
        
        return False
    
    @staticmethod
    def _check_3d_model_url(url):
        """Проверить доступность 3D модели по URL"""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def _update_status_based_on_score(product, score):
        """Обновить статус товара на основе оценки верификации"""
        from app.models.workflow import ProductStatusHistory
        from flask_login import current_user
        
        old_status = product.status
        
        if score >= 80:
            new_status = ProductStatus.APPROVED
        elif score >= 50:
            new_status = ProductStatus.TO_REVIEW
        else:
            new_status = ProductStatus.REJECTED
        
        if old_status != new_status:
            product.status = new_status
            
            # Записать в историю
            history = ProductStatusHistory(
                product_id=product.id,
                old_status=old_status.value,
                new_status=new_status.value,
                changed_by_id=current_user.id if current_user.is_authenticated else None,
                comment=f'Автоматический переход на основе верификации (оценка: {score}%)'
            )
            db.session.add(history)
            db.session.commit()
