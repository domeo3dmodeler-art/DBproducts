"""
Сервис для работы с запросами данных от поставщиков
"""
from app import db
from app.models.data_request import DataRequest, DataRequestStatus
from app.models.supplier import Supplier
from app.models.category import ProductCategory
from app.models.subcategory import Subcategory
from datetime import datetime
from flask import current_app


class DataRequestService:
    """Сервис для управления запросами данных от поставщиков"""
    
    @staticmethod
    def create_request(supplier_id, category_id, subcategory_ids, requested_by_id, 
                      deadline=None, request_message=None):
        """
        Создать новый запрос данных
        
        Args:
            supplier_id: ID поставщика
            category_id: ID категории
            subcategory_ids: Список ID подкатегорий
            requested_by_id: ID пользователя, создающего запрос
            deadline: Срок получения данных (опционально)
            request_message: Текст запроса (опционально)
        
        Returns:
            DataRequest: Созданный запрос
        
        Raises:
            ValueError: Если валидация не прошла
        """
        # Валидация: поставщик существует
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            raise ValueError(f"Поставщик с ID {supplier_id} не найден")
        
        # Валидация: категория существует
        category = ProductCategory.query.get(category_id)
        if not category:
            raise ValueError(f"Категория с ID {category_id} не найдена")
        
        # Валидация: все подкатегории принадлежат выбранной категории
        subcategories = Subcategory.query.filter(Subcategory.id.in_(subcategory_ids)).all()
        if len(subcategories) != len(subcategory_ids):
            raise ValueError("Некоторые подкатегории не найдены")
        
        for subcategory in subcategories:
            if subcategory.category_id != category_id:
                raise ValueError(f"Подкатегория {subcategory.name} не принадлежит категории {category.name}")
        
        # Валидация: все подкатегории привязаны к поставщику
        supplier_subcategory_ids = [s.id for s in supplier.subcategories.all()]
        for subcategory in subcategories:
            if subcategory.id not in supplier_subcategory_ids:
                raise ValueError(f"Подкатегория {subcategory.name} не привязана к поставщику {supplier.name}")
        
        # Создать запрос
        request = DataRequest(
            supplier_id=supplier_id,
            category_id=category_id,
            requested_by_id=requested_by_id,
            deadline=deadline,
            request_message=request_message,
            status=DataRequestStatus.NEW
        )
        request.set_subcategory_ids(subcategory_ids)
        
        db.session.add(request)
        db.session.commit()
        
        return request
    
    @staticmethod
    def send_request(request_id):
        """
        Отправить запрос поставщику (изменить статус на REQUEST_SENT)
        
        Args:
            request_id: ID запроса
        
        Returns:
            DataRequest: Обновленный запрос
        
        Raises:
            ValueError: Если запрос не найден или уже отправлен
        """
        request = DataRequest.query.get(request_id)
        if not request:
            raise ValueError(f"Запрос с ID {request_id} не найден")
        
        if request.status != DataRequestStatus.NEW:
            raise ValueError(f"Запрос уже отправлен или имеет статус {request.status.value}")
        
        request.status = DataRequestStatus.REQUEST_SENT
        request.request_sent_at = datetime.utcnow()
        
        db.session.commit()
        
        return request
    
    @staticmethod
    def mark_received(request_id, import_history_id=None):
        """
        Отметить получение данных от поставщика
        
        Args:
            request_id: ID запроса
            import_history_id: ID файла импорта (опционально)
        
        Returns:
            DataRequest: Обновленный запрос
        
        Raises:
            ValueError: Если запрос не найден
        """
        request = DataRequest.query.get(request_id)
        if not request:
            raise ValueError(f"Запрос с ID {request_id} не найден")
        
        if request.status != DataRequestStatus.REQUEST_SENT:
            raise ValueError(f"Запрос должен быть в статусе REQUEST_SENT, текущий статус: {request.status.value}")
        
        request.status = DataRequestStatus.DATA_RECEIVED
        request.data_received_at = datetime.utcnow()
        
        if import_history_id:
            request.import_history_id = import_history_id
        
        db.session.commit()
        
        return request
    
    @staticmethod
    def mark_no_response(request_id):
        """
        Отметить отсутствие ответа от поставщика
        
        Args:
            request_id: ID запроса
        
        Returns:
            DataRequest: Обновленный запрос
        """
        request = DataRequest.query.get(request_id)
        if not request:
            raise ValueError(f"Запрос с ID {request_id} не найден")
        
        request.status = DataRequestStatus.NO_RESPONSE
        
        db.session.commit()
        
        return request
    
    @staticmethod
    def cancel_request(request_id):
        """
        Отменить запрос
        
        Args:
            request_id: ID запроса
        
        Returns:
            DataRequest: Обновленный запрос
        """
        request = DataRequest.query.get(request_id)
        if not request:
            raise ValueError(f"Запрос с ID {request_id} не найден")
        
        if request.status == DataRequestStatus.DATA_RECEIVED:
            raise ValueError("Нельзя отменить запрос, по которому уже получены данные")
        
        request.status = DataRequestStatus.CANCELLED
        
        db.session.commit()
        
        return request
    
    @staticmethod
    def check_overdue_requests():
        """
        Проверить просроченные запросы и обновить их статус
        
        Returns:
            int: Количество обновленных запросов
        """
        now = datetime.utcnow()
        overdue_requests = DataRequest.query.filter(
            DataRequest.status == DataRequestStatus.REQUEST_SENT,
            DataRequest.deadline.isnot(None),
            DataRequest.deadline < now
        ).all()
        
        count = 0
        for request in overdue_requests:
            request.status = DataRequestStatus.NO_RESPONSE
            count += 1
        
        if count > 0:
            db.session.commit()
        
        return count
    
    @staticmethod
    def get_supplier_stats(supplier_id):
        """
        Получить статистику по запросам для поставщика
        
        Args:
            supplier_id: ID поставщика
        
        Returns:
            dict: Статистика по запросам
        """
        requests = DataRequest.query.filter_by(supplier_id=supplier_id).all()
        
        return {
            'total': len(requests),
            'new': len([r for r in requests if r.status == DataRequestStatus.NEW]),
            'request_sent': len([r for r in requests if r.status == DataRequestStatus.REQUEST_SENT]),
            'data_received': len([r for r in requests if r.status == DataRequestStatus.DATA_RECEIVED]),
            'no_response': len([r for r in requests if r.status == DataRequestStatus.NO_RESPONSE]),
            'cancelled': len([r for r in requests if r.status == DataRequestStatus.CANCELLED]),
            'overdue': len([r for r in requests if r.is_overdue()]),
        }
    
    @staticmethod
    def get_requests_by_status(status, supplier_id=None, category_id=None):
        """
        Получить запросы по статусу с фильтрацией
        
        Args:
            status: Статус запроса (DataRequestStatus)
            supplier_id: ID поставщика (опционально)
            category_id: ID категории (опционально)
        
        Returns:
            list: Список запросов
        """
        query = DataRequest.query.filter_by(status=status)
        
        if supplier_id:
            query = query.filter_by(supplier_id=supplier_id)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        return query.order_by(DataRequest.created_at.desc()).all()

