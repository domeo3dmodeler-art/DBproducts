"""
Форма для подкатегории
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

class SubcategoryForm(FlaskForm):
    """Форма создания/редактирования подкатегории"""
    code = StringField('Код', validators=[
        Length(max=100, message='Код должен быть не более 100 символов'),
        Regexp(r'^[a-zA-Z0-9_-]*$', message='Код может содержать только буквы, цифры, дефисы и подчеркивания')
    ])
    name = StringField('Название', validators=[
        DataRequired(message='Название обязательно для заполнения'),
        Length(min=1, max=255, message='Название должно быть от 1 до 255 символов')
    ])
    category_id = SelectField('Категория', coerce=int, validators=[
        DataRequired(message='Необходимо выбрать категорию')
    ])
    description = TextAreaField('Описание', validators=[
        Length(max=1000, message='Описание не должно превышать 1000 символов')
    ])
    is_active = BooleanField('Активна', default=True)
    submit = SubmitField('Сохранить')
    
    def __init__(self, *args, **kwargs):
        super(SubcategoryForm, self).__init__(*args, **kwargs)
        # Заполнить список категорий
        from app.models.category import ProductCategory
        self.category_id.choices = [(c.id, c.name) 
                                    for c in ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()]
