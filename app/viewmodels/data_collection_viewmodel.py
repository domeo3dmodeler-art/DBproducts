"""
ViewModel для этапа "Сбор данных"
"""
from app.viewmodels.supplier_viewmodel import SupplierViewModel
from app.viewmodels.data_request_viewmodel import DataRequestViewModel


class DataCollectionViewModel:
    """ViewModel для представления этапа 'Сбор данных'"""
    
    def __init__(self, suppliers_data, data_requests, stats):
        """
        Инициализация ViewModel
        
        Args:
            suppliers_data: список словарей с данными поставщиков
            data_requests: список объектов DataRequest
            stats: статистика этапа
        """
        # Преобразовать поставщиков в ViewModels
        self.suppliers = [
            SupplierViewModel(item['supplier'], item.get('stats'))
            for item in suppliers_data
        ]
        
        # Преобразовать запросы в ViewModels
        self.data_requests = [
            DataRequestViewModel(req)
            for req in data_requests
        ]
        
        # Статистика
        self.stats = stats
    
    def to_dict(self):
        """Сериализация в словарь для JSON"""
        return {
            'suppliers': [s.to_dict() for s in self.suppliers],
            'data_requests': [r.to_dict() for r in self.data_requests],
            'stats': self.stats,
        }

