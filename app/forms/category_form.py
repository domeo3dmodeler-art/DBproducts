"""
Форма для категории товаров
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

class CategoryForm(FlaskForm):
    """Форма создания/редактирования категории"""
    code = StringField('Код', validators=[
        Length(max=100, message='Код должен быть не более 100 символов'),
        Regexp(r'^[a-zA-Z0-9_-]*$', message='Код может содержать только буквы, цифры, дефисы и подчеркивания')
    ])
    name = StringField('Название', validators=[
        DataRequired(message='Название обязательно для заполнения'),
        Length(min=1, max=255, message='Название должно быть от 1 до 255 символов')
    ])
    description = TextAreaField('Описание', validators=[
        Length(max=1000, message='Описание не должно превышать 1000 символов')
    ])
    is_active = BooleanField('Активна', default=True)
    submit = SubmitField('Сохранить')

