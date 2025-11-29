"""
Маршруты аутентификации
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from app.auth import bp
from app.models.user import User
from app import db

class LoginForm(FlaskForm):
    """Форма входа"""
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в систему"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=True)
            # Обновить время последнего входа
            from datetime import datetime
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            flash('Добро пожаловать!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    return redirect(url_for('main.index'))

