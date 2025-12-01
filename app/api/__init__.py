"""
Blueprint для API
"""
from flask import Blueprint

bp = Blueprint('api', __name__)

# Импортировать обработчики ошибок
from app.api import error_handlers

from app.api import routes
from app.api import health

