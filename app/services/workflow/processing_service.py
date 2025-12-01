"""
Сервис для этапа "В обработке"
"""
from app import db
from app.models.import_history import ImportHistory, ImportFileStatus
from flask import current_app
from sqlalchemy import func, or_


class ProcessingService:
    """Сервис для управления этапом 'В обработке'"""
    
    @staticmethod
    def get_stats():
        """
        Получить статистику этапа 'В обработке'
        
        Returns:
            dict: Статистика
        """
        try:
            stats = {
                'files_count': ImportHistory.query.filter_by(file_status=ImportFileStatus.PROCESSING).count(),
                'total_rows': db.session.query(func.sum(ImportHistory.total_rows)).filter_by(
                    file_status=ImportFileStatus.PROCESSING
                ).scalar() or 0,
            }
            return stats
        except Exception as e:
            current_app.logger.error(f"Ошибка при получении статистики обработки: {str(e)}", exc_info=True)
            return {
                'files_count': 0,
                'total_rows': 0,
            }
    
    @staticmethod
    def get_files(filters=None, page=1, per_page=20):
        """
        Получить файлы в обработке с фильтрацией и пагинацией
        
        Args:
            filters: dict с фильтрами:
                - supplier_id: ID поставщика
                - data_request_id: ID запроса данных
                - search: поисковый запрос
            page: номер страницы
            per_page: количество на странице
        
        Returns:
            dict: {
                'items': список файлов,
                'total': общее количество,
                'page': текущая страница,
                'per_page': количество на странице,
                'pages': всего страниц
            }
        """
        try:
            filters = filters or {}
            
            # Базовый запрос
            query = ImportHistory.query.filter_by(file_status=ImportFileStatus.PROCESSING)
            
            # Фильтр по поставщику
            if filters.get('supplier_id'):
                query = query.join('data_request').filter(
                    ImportHistory.data_request.has(supplier_id=filters['supplier_id'])
                )
            
            # Фильтр по запросу данных
            if filters.get('data_request_id'):
                query = query.filter_by(data_request_id=filters['data_request_id'])
            
            # Фильтр по поиску
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        ImportHistory.filename.ilike(search),
                        ImportHistory.file_path.ilike(search)
                    )
                )
            
            # Пагинация
            pagination = query.order_by(ImportHistory.imported_at.desc()).paginate(
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
            current_app.logger.error(f"Ошибка при получении файлов в обработке: {str(e)}", exc_info=True)
            return {
                'items': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'pages': 0,
            }

