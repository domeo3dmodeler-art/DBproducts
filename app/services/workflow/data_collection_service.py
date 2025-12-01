"""
Сервис для этапа "Сбор данных"
"""
from app import db
from app.models.supplier import Supplier
from app.models.data_request import DataRequest, DataRequestStatus
from app.services.data_request_service import DataRequestService
from datetime import datetime
from flask import current_app
from sqlalchemy import or_


class DataCollectionService:
    """Сервис для управления этапом 'Сбор данных'"""
    
    @staticmethod
    def get_stats():
        """
        Получить статистику этапа 'Сбор данных'
        
        Returns:
            dict: Статистика
        """
        try:
            stats = {
                'suppliers_count': Supplier.query.filter_by(is_active=True).count(),
                'requests_active': DataRequest.query.filter_by(status=DataRequestStatus.REQUEST_SENT).count(),
                'requests_received': DataRequest.query.filter_by(status=DataRequestStatus.DATA_RECEIVED).count(),
                'requests_pending': DataRequest.query.filter(
                    DataRequest.status.in_([DataRequestStatus.NO_RESPONSE, DataRequestStatus.REQUEST_SENT]),
                    DataRequest.deadline.isnot(None),
                    DataRequest.deadline < datetime.utcnow()
                ).count(),
            }
            return stats
        except Exception as e:
            current_app.logger.error(f"Ошибка при получении статистики сбора данных: {str(e)}", exc_info=True)
            return {
                'suppliers_count': 0,
                'requests_active': 0,
                'requests_received': 0,
                'requests_pending': 0,
            }
    
    @staticmethod
    def get_suppliers(filters=None, page=1, per_page=20):
        """
        Получить поставщиков с фильтрацией и пагинацией
        
        Args:
            filters: dict с фильтрами:
                - status: статус поставщика (has_data, waiting, no_response, new)
                - category_id: ID категории
                - search: поисковый запрос
            page: номер страницы
            per_page: количество на странице
        
        Returns:
            dict: {
                'items': список поставщиков,
                'total': общее количество,
                'page': текущая страница,
                'per_page': количество на странице,
                'pages': всего страниц
            }
        """
        try:
            filters = filters or {}
            
            # Базовый запрос
            query = Supplier.query.filter_by(is_active=True)
            
            # Фильтр по поиску
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Supplier.name.ilike(search),
                        Supplier.code.ilike(search)
                    )
                )
            
            # Фильтр по категории
            if filters.get('category_id'):
                category_id = filters['category_id']
                query = query.join(Supplier.categories).filter(
                    Supplier.categories.any(id=category_id)
                )
            
            # Получить всех поставщиков для фильтрации по статусу
            all_suppliers = query.order_by(Supplier.name).all()
            
            # Фильтр по статусу (требует расчета статистики для каждого поставщика)
            if filters.get('status'):
                status_filter = filters['status']
                filtered_suppliers = []
                
                for supplier in all_suppliers:
                    supplier_stats = DataRequestService.get_supplier_stats(supplier.id)
                    
                    # Определить статус поставщика
                    if supplier_stats['data_received'] > 0:
                        overall_status = 'has_data'
                    elif supplier_stats['request_sent'] > 0 or supplier_stats['overdue'] > 0:
                        overall_status = 'waiting'
                    elif supplier_stats['no_response'] > 0:
                        overall_status = 'no_response'
                    else:
                        overall_status = 'new'
                    
                    if overall_status == status_filter:
                        filtered_suppliers.append(supplier)
                
                all_suppliers = filtered_suppliers
            
            # Пагинация
            total = len(all_suppliers)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_suppliers = all_suppliers[start:end]
            
            # Подготовить данные для каждого поставщика
            suppliers_data = []
            for supplier in paginated_suppliers:
                supplier_stats = DataRequestService.get_supplier_stats(supplier.id)
                
                # Определить общий статус поставщика
                if supplier_stats['data_received'] > 0:
                    overall_status = 'has_data'
                elif supplier_stats['request_sent'] > 0 or supplier_stats['overdue'] > 0:
                    overall_status = 'waiting'
                elif supplier_stats['no_response'] > 0:
                    overall_status = 'no_response'
                else:
                    overall_status = 'new'
                
                suppliers_data.append({
                    'supplier': supplier,
                    'stats': supplier_stats,
                    'overall_status': overall_status,
                })
            
            return {
                'items': suppliers_data,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page if total > 0 else 0,
            }
        except Exception as e:
            current_app.logger.error(f"Ошибка при получении поставщиков: {str(e)}", exc_info=True)
            return {
                'items': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'pages': 0,
            }
    
    @staticmethod
    def get_data_requests(filters=None, page=1, per_page=20):
        """
        Получить запросы данных с фильтрацией и пагинацией
        
        Args:
            filters: dict с фильтрами:
                - supplier_id: ID поставщика
                - category_id: ID категории
                - status: статус запроса
                - search: поисковый запрос
            page: номер страницы
            per_page: количество на странице
        
        Returns:
            dict: {
                'items': список запросов,
                'total': общее количество,
                'page': текущая страница,
                'per_page': количество на странице,
                'pages': всего страниц
            }
        """
        try:
            filters = filters or {}
            
            # Базовый запрос
            query = DataRequest.query
            
            # Фильтр по поставщику
            if filters.get('supplier_id'):
                query = query.filter_by(supplier_id=filters['supplier_id'])
            
            # Фильтр по категории
            if filters.get('category_id'):
                query = query.filter_by(category_id=filters['category_id'])
            
            # Фильтр по статусу
            if filters.get('status'):
                try:
                    status = DataRequestStatus[filters['status'].upper()]
                    query = query.filter_by(status=status)
                except (KeyError, AttributeError):
                    pass
            
            # Фильтр по поиску
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.join(Supplier).filter(
                    or_(
                        Supplier.name.ilike(search),
                        Supplier.code.ilike(search)
                    )
                )
            
            # Пагинация
            pagination = query.order_by(DataRequest.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'items': pagination.items,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages,
            }
        except Exception as e:
            current_app.logger.error(f"Ошибка при получении запросов данных: {str(e)}", exc_info=True)
            return {
                'items': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'pages': 0,
            }

