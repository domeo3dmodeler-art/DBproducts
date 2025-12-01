"""
API endpoints для workflow этапов
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.services.workflow import (
    DataCollectionService,
    ProcessingService,
    CatalogService,
    ExportService
)
from app.viewmodels.data_collection_viewmodel import DataCollectionViewModel
from flask import current_app

bp = Blueprint('workflow_api', __name__, url_prefix='/api/workflow')


@bp.route('/data-collection', methods=['GET'])
@login_required
def api_data_collection():
    """API для загрузки данных этапа 'Сбор данных'"""
    try:
        # Получить фильтры из запроса
        filters = {
            'supplier_status': request.args.get('supplier_status'),
            'category_id': request.args.get('category_id', type=int),
            'supplier_id': request.args.get('supplier_id', type=int),
            'request_status': request.args.get('request_status'),
            'search': request.args.get('search', ''),
        }
        
        # Удалить None значения
        filters = {k: v for k, v in filters.items() if v is not None and v != ''}
        
        # Пагинация
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Получить данные через сервисы
        suppliers_result = DataCollectionService.get_suppliers(
            filters={'status': filters.get('supplier_status'), 
                    'category_id': filters.get('category_id'),
                    'search': filters.get('search', '')},
            page=page,
            per_page=per_page
        )
        
        requests_result = DataCollectionService.get_data_requests(
            filters={'supplier_id': filters.get('supplier_id'),
                    'category_id': filters.get('category_id'),
                    'status': filters.get('request_status'),
                    'search': filters.get('search', '')},
            page=page,
            per_page=per_page
        )
        
        stats = DataCollectionService.get_stats()
        
        # Создать ViewModel
        viewmodel = DataCollectionViewModel(
            suppliers_data=suppliers_result['items'],
            data_requests=requests_result['items'],
            stats=stats
        )
        
        return jsonify({
            'success': True,
            'data': viewmodel.to_dict(),
            'pagination': {
                'suppliers': {
                    'page': suppliers_result['page'],
                    'per_page': suppliers_result['per_page'],
                    'total': suppliers_result['total'],
                    'pages': suppliers_result['pages'],
                },
                'requests': {
                    'page': requests_result['page'],
                    'per_page': requests_result['per_page'],
                    'total': requests_result['total'],
                    'pages': requests_result['pages'],
                },
            }
        })
    except Exception as e:
        current_app.logger.error(f"Ошибка в API data-collection: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Ошибка при загрузке данных',
            'message': str(e)
        }), 500


@bp.route('/processing', methods=['GET'])
@login_required
def api_processing():
    """API для загрузки данных этапа 'В обработке'"""
    try:
        # Получить фильтры из запроса
        filters = {
            'supplier_id': request.args.get('supplier_id', type=int),
            'data_request_id': request.args.get('data_request_id', type=int),
            'search': request.args.get('search', ''),
        }
        
        # Удалить None значения
        filters = {k: v for k, v in filters.items() if v is not None and v != ''}
        
        # Пагинация
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Получить данные через сервис
        files_result = ProcessingService.get_files(filters, page, per_page)
        stats = ProcessingService.get_stats()
        
        # Преобразовать файлы в словари
        files_data = []
        for file in files_result['items']:
            files_data.append({
                'id': file.id,
                'filename': file.filename,
                'file_path': file.file_path,
                'supplier': {
                    'id': file.data_request.supplier.id if file.data_request and file.data_request.supplier else None,
                    'name': file.data_request.supplier.name if file.data_request and file.data_request.supplier else None,
                } if file.data_request else None,
                'data_request_id': file.data_request_id,
                'total_rows': file.total_rows,
                'imported_count': file.imported_count,
                'progress': (file.imported_count / file.total_rows * 100) if file.total_rows > 0 else 0,
                'imported_at': file.imported_at.isoformat() if file.imported_at else None,
            })
        
        return jsonify({
            'success': True,
            'data': {
                'files': files_data,
                'stats': stats,
            },
            'pagination': {
                'page': files_result['page'],
                'per_page': files_result['per_page'],
                'total': files_result['total'],
                'pages': files_result['pages'],
            }
        })
    except Exception as e:
        current_app.logger.error(f"Ошибка в API processing: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Ошибка при загрузке данных',
            'message': str(e)
        }), 500


@bp.route('/catalog', methods=['GET'])
@login_required
def api_catalog():
    """API для загрузки данных этапа 'В каталоге'"""
    try:
        # Получить фильтры из запроса
        filters = {
            'supplier_id': request.args.get('supplier_id', type=int),
            'data_request_id': request.args.get('data_request_id', type=int),
            'min_score': request.args.get('min_score', type=float),
            'product_status': request.args.get('product_status'),
            'search': request.args.get('search', ''),
        }
        
        # Удалить None значения
        filters = {k: v for k, v in filters.items() if v is not None and v != ''}
        
        # Пагинация
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Получить данные через сервис
        imports_result = CatalogService.get_imports(filters, page, per_page)
        stats = CatalogService.get_stats()
        
        # Преобразовать импорты в словари
        imports_data = []
        for imp in imports_result['items']:
            imports_data.append({
                'id': imp.id,
                'filename': imp.filename,
                'file_path': imp.file_path,
                'supplier': {
                    'id': imp.data_request.supplier.id if imp.data_request and imp.data_request.supplier else None,
                    'name': imp.data_request.supplier.name if imp.data_request and imp.data_request.supplier else None,
                } if imp.data_request else None,
                'data_request_id': imp.data_request_id,
                'total_rows': imp.total_rows,
                'imported_count': imp.imported_count,
                'imported_at': imp.imported_at.isoformat() if imp.imported_at else None,
            })
        
        return jsonify({
            'success': True,
            'data': {
                'imports': imports_data,
                'stats': stats,
            },
            'pagination': {
                'page': imports_result['page'],
                'per_page': imports_result['per_page'],
                'total': imports_result['total'],
                'pages': imports_result['pages'],
            }
        })
    except Exception as e:
        current_app.logger.error(f"Ошибка в API catalog: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Ошибка при загрузке данных',
            'message': str(e)
        }), 500


@bp.route('/export', methods=['GET'])
@login_required
def api_export():
    """API для загрузки данных этапа 'Экспортировано'"""
    try:
        # Получить фильтры из запроса
        filters = {
            'supplier_id': request.args.get('supplier_id', type=int),
            'data_request_id': request.args.get('data_request_id', type=int),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'search': request.args.get('search', ''),
        }
        
        # Удалить None значения
        filters = {k: v for k, v in filters.items() if v is not None and v != ''}
        
        # Пагинация
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Получить данные через сервис
        exports_result = ExportService.get_exports(filters, page, per_page)
        stats = ExportService.get_stats()
        
        # Преобразовать экспорты в словари
        exports_data = []
        for exp in exports_result['items']:
            exports_data.append({
                'id': exp.id,
                'filename': exp.filename,
                'file_path': exp.file_path,
                'supplier': {
                    'id': exp.data_request.supplier.id if exp.data_request and exp.data_request.supplier else None,
                    'name': exp.data_request.supplier.name if exp.data_request and exp.data_request.supplier else None,
                } if exp.data_request else None,
                'data_request_id': exp.data_request_id,
                'total_rows': exp.total_rows,
                'imported_count': exp.imported_count,
                'exported_at': exp.exported_at.isoformat() if exp.exported_at else None,
            })
        
        return jsonify({
            'success': True,
            'data': {
                'exports': exports_data,
                'stats': stats,
            },
            'pagination': {
                'page': exports_result['page'],
                'per_page': exports_result['per_page'],
                'total': exports_result['total'],
                'pages': exports_result['pages'],
            }
        })
    except Exception as e:
        current_app.logger.error(f"Ошибка в API export: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Ошибка при загрузке данных',
            'message': str(e)
        }), 500

