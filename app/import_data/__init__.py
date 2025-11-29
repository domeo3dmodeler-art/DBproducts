"""
Blueprint для импорта данных
"""
from flask import Blueprint

bp = Blueprint('import_data', __name__)

from app.import_data import routes

