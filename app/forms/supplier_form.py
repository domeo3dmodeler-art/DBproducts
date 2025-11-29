"""
Форма для поставщика
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Optional, Regexp

class SupplierForm(FlaskForm):
    """Форма создания/редактирования поставщика"""
    code = StringField('Код', validators=[
        DataRequired(message='Код обязателен для заполнения'),
        Length(min=1, max=100, message='Код должен быть от 1 до 100 символов'),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Код может содержать только буквы, цифры, дефисы и подчеркивания')
    ])
    name = StringField('Название', validators=[
        DataRequired(message='Название обязательно для заполнения'),
        Length(min=1, max=255, message='Название должно быть от 1 до 255 символов')
    ])
    category_ids = SelectMultipleField('Категории', coerce=int, validators=[
        DataRequired(message='Необходимо выбрать хотя бы одну категорию')
    ])
    subcategory_ids = SelectMultipleField('Подкатегории', coerce=int, validators=[])
    contact_person = StringField('Контактное лицо', validators=[
        Length(max=255, message='Имя не должно превышать 255 символов')
    ])
    email = StringField('Email', validators=[
        Optional(),
        Email(message='Неверный формат email')
    ])
    phone = StringField('Телефон', validators=[
        Length(max=50, message='Телефон не должен превышать 50 символов')
    ])
    address = TextAreaField('Адрес', validators=[
        Length(max=500, message='Адрес не должен превышать 500 символов')
    ])
    is_active = BooleanField('Активен', default=True)
    submit = SubmitField('Сохранить')
    
    def __init__(self, *args, **kwargs):
        super(SupplierForm, self).__init__(*args, **kwargs)
        # Заполнить список категорий
        from app.models.category import ProductCategory
        self.category_ids.choices = [(c.id, c.name) 
                                    for c in ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()]
        
        # Заполнить список подкатегорий
        from app.models.subcategory import Subcategory
        self.subcategory_ids.choices = [(s.id, f"{s.name} ({s.category.name if s.category else ''})") 
                                        for s in Subcategory.query.filter_by(is_active=True).order_by(Subcategory.name).all()]
