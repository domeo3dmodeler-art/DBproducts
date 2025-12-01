"""
Обработчики ошибок для API
"""
from flask import jsonify, current_app
from app.api import bp

@bp.errorhandler(400)
def bad_request(error):
    """Обработка ошибок 400"""
    return jsonify({'error': 'Неверный запрос', 'message': str(error)}), 400

@bp.errorhandler(401)
def unauthorized(error):
    """Обработка ошибок 401"""
    return jsonify({'error': 'Требуется аутентификация'}), 401

@bp.errorhandler(403)
def forbidden(error):
    """Обработка ошибок 403"""
    return jsonify({'error': 'Доступ запрещен'}), 403

@bp.errorhandler(404)
def not_found(error):
    """Обработка ошибок 404"""
    return jsonify({'error': 'Ресурс не найден'}), 404

@bp.errorhandler(500)
def internal_error(error):
    """Обработка ошибок 500"""
    current_app.logger.error(f'Internal server error: {str(error)}')
    return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@bp.errorhandler(Exception)
def handle_exception(e):
    """Обработка всех необработанных исключений"""
    current_app.logger.error(f'Unhandled exception: {str(e)}', exc_info=True)
    return jsonify({'error': 'Произошла ошибка при обработке запроса'}), 500

