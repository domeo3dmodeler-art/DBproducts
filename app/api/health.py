"""
Health check endpoints для мониторинга
"""
from flask import jsonify
from app.api import bp
from app import db
from datetime import datetime
import os

@bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint для мониторинга состояния системы
    
    Returns:
        JSON с информацией о состоянии системы
    """
    health_status = {
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'checks': {}
    }
    
    # Проверка базы данных
    try:
        db.session.execute(db.text('SELECT 1'))
        health_status['checks']['database'] = {
            'status': 'ok',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['database'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Проверка файловой системы
    try:
        from config import Config
        import os
        
        # Проверить доступность папок
        folders_to_check = [
            Config.UPLOAD_FOLDER,
            Config.MEDIA_FOLDER,
            Config.IMAGES_FOLDER,
            Config.MODELS_FOLDER
        ]
        
        for folder in folders_to_check:
            if not folder.exists():
                folder.mkdir(parents=True, exist_ok=True)
        
        health_status['checks']['filesystem'] = {
            'status': 'ok',
            'message': 'File system accessible'
        }
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['filesystem'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # HTTP статус код
    http_status = 200 if health_status['status'] == 'ok' else 503
    
    return jsonify(health_status), http_status

@bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check - проверка готовности к обработке запросов
    
    Returns:
        200 если готов, 503 если не готов
    """
    try:
        # Проверить БД
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'ready'}), 200
    except Exception:
        return jsonify({'status': 'not ready'}), 503

@bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check - проверка что приложение работает
    
    Returns:
        Всегда 200
    """
    return jsonify({'status': 'alive'}), 200

