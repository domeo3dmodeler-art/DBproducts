"""
Точка входа в приложение
"""
from app import create_app, db
from app.models.user import User
from flask_migrate import upgrade

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Контекст для Flask shell"""
    return {
        'db': db,
        'User': User,
    }

@app.cli.command()
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
        print('Создан администратор: admin / admin')

# Регистрация CLI команд
from app.commands.import_command import import_products
app.cli.add_command(import_products)

if __name__ == '__main__':
    app.run(debug=True)

