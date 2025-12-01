"""
Маршруты аутентификации
"""
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from app.auth import bp
from app.models.user import User
from app import db, csrf
from datetime import datetime

class LoginForm(FlaskForm):
    """Форма входа"""
    class Meta:
        csrf = False  # Отключить CSRF для этой формы
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

@bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt  # Временно отключить CSRF для этого endpoint
def login():
    """Вход в систему"""
    if request.method == 'POST':
        # Получить данные из любого источника (JSON или form)
        username = ''
        password = ''
        
        # Попробовать получить из JSON
        if request.is_json or (request.content_type and 'application/json' in request.content_type):
            try:
                json_data = request.get_json(force=True)
                if json_data:
                    username = json_data.get('username', '').strip()
                    password = json_data.get('password', '').strip()
            except:
                pass
        
        # Если не получили из JSON, попробовать form data
        if not username and not password:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
        
        # Если есть данные, обработать как JSON API запрос
        if username and password:
            try:
                user = User.query.filter_by(username=username).first()
                
                # Проверить всех пользователей в БД для отладки
                all_users = User.query.all()
                current_app.logger.info(f"Всего пользователей в БД: {len(all_users)}")
                
                if not user:
                    current_app.logger.warning(f"Пользователь не найден: '{username}'. Всего пользователей: {len(all_users)}")
                    return jsonify({
                        'success': False, 
                        'error': 'Неверное имя пользователя или пароль',
                        'debug': {
                            'total_users': len(all_users),
                            'usernames': [u.username for u in all_users]
                        }
                    }), 401
                
                password_check = user.check_password(password)
                current_app.logger.info(f"Проверка пароля для '{username}': {password_check}")
                
                if not password_check:
                    current_app.logger.warning(f"Неверный пароль для пользователя: '{username}'")
                    return jsonify({'success': False, 'error': 'Неверное имя пользователя или пароль'}), 401
                
                if not user.is_active:
                    current_app.logger.warning(f"Пользователь неактивен: '{username}'")
                    return jsonify({'success': False, 'error': 'Пользователь неактивен'}), 403
                
                # Все проверки пройдены - вход успешен
                login_user(user, remember=True)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                current_app.logger.info(f"Успешный вход: '{username}'")
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_admin': user.is_admin,
                    }
                })
            except Exception as e:
                current_app.logger.error(f"Ошибка при входе: {str(e)}", exc_info=True)
                return jsonify({'success': False, 'error': 'Ошибка при входе в систему'}), 500
    
    # Обычная HTML форма (для обратной совместимости)
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data.strip() if form.username.data else ''
        password = form.password.data if form.password.data else ''
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            flash('Добро пожаловать!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/check', methods=['GET'])
def check_auth():
    """API endpoint для проверки аутентификации"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'is_admin': current_user.is_admin,
            }
        })
    return jsonify({'authenticated': False}), 401

@bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    return redirect(url_for('main.index'))
