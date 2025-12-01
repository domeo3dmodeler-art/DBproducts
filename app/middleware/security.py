"""
Middleware для безопасности
"""
from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
import time

# Простой rate limiter (в production лучше использовать Flask-Limiter)
_rate_limit_store = {}

def rate_limit(max_requests=100, window=60):
    """
    Простой rate limiter
    
    Args:
        max_requests: Максимальное количество запросов
        window: Окно времени в секундах
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Получить IP адрес
            if request.headers.getlist("X-Forwarded-For"):
                ip = request.headers.getlist("X-Forwarded-For")[0]
            else:
                ip = request.remote_addr
            
            # Получить текущее время
            now = time.time()
            
            # Очистить старые записи
            if ip in _rate_limit_store:
                _rate_limit_store[ip] = [
                    timestamp for timestamp in _rate_limit_store[ip]
                    if now - timestamp < window
                ]
            else:
                _rate_limit_store[ip] = []
            
            # Проверить лимит
            if len(_rate_limit_store[ip]) >= max_requests:
                return jsonify({
                    'error': 'Too many requests',
                    'message': f'Превышен лимит запросов: {max_requests} в {window} секунд'
                }), 429
            
            # Добавить текущий запрос
            _rate_limit_store[ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def security_headers(f):
    """Добавить security headers к ответу"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Добавить security headers
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    return decorated_function

