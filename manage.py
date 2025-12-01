"""
Утилита для управления приложением
"""
import os
import click
from flask.cli import FlaskGroup
from app import create_app, db
from app.models.user import User
from config import config

# Определить конфигурацию
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config.get(config_name, config['default']))

cli = FlaskGroup(app)

@cli.command()
def init_db():
    """Инициализация базы данных"""
    db.create_all()
    
    # Создать администратора по умолчанию
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            full_name='Администратор',
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        click.echo('✅ Создан администратор: admin / admin')
        click.echo('⚠️  ВАЖНО: Измените пароль после первого входа!')
    else:
        click.echo('ℹ️  Администратор уже существует')

@cli.command()
@click.argument('username')
@click.argument('email')
@click.argument('password')
def create_user(username, email, password):
    """Создать нового пользователя"""
    if User.query.filter_by(username=username).first():
        click.echo(f'❌ Пользователь {username} уже существует')
        return
    
    user = User(
        username=username,
        email=email,
        is_admin=False,
        is_active=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f'✅ Пользователь {username} создан')

@cli.command()
@click.argument('username')
def make_admin(username):
    """Сделать пользователя администратором"""
    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f'❌ Пользователь {username} не найден')
        return
    
    user.is_admin = True
    db.session.commit()
    click.echo(f'✅ Пользователь {username} теперь администратор')

@cli.command()
def backup():
    """Создать резервную копию базы данных и медиа-файлов"""
    import subprocess
    result = subprocess.run(['python', 'backup.py'], capture_output=True, text=True)
    click.echo(result.stdout)
    if result.returncode != 0:
        click.echo(result.stderr)

@cli.command()
def test():
    """Запустить тесты"""
    import subprocess
    result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v'], capture_output=True, text=True)
    click.echo(result.stdout)
    if result.returncode != 0:
        click.echo(result.stderr)

@cli.command()
def shell():
    """Открыть Flask shell"""
    from flask import current_app
    import IPython
    
    context = {
        'app': current_app,
        'db': db,
        'User': User,
    }
    
    IPython.embed(user_ns=context)

@cli.command()
@click.confirmation_option(prompt='Вы уверены, что хотите удалить всех поставщиков? Это действие нельзя отменить!')
def clear_suppliers():
    """Удалить всех поставщиков из базы данных"""
    from app.models.supplier import Supplier
    
    count = Supplier.query.count()
    if count == 0:
        click.echo('ℹ️  В базе данных нет поставщиков')
        return
    
    # Удалить всех поставщиков
    Supplier.query.delete()
    db.session.commit()
    
    click.echo(f'✅ Удалено поставщиков: {count}')

if __name__ == '__main__':
    cli()

