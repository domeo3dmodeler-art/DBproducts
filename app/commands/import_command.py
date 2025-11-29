"""
CLI команда для импорта данных
"""
import click
from flask.cli import with_appcontext
from app.services.import_service import ImportService
from app.models.subcategory import Subcategory
from app.models.supplier import Supplier

@click.command()
@click.argument('file_path')
@click.option('--supplier-id', type=int, required=True, help='ID поставщика')
@click.option('--subcategory-id', type=int, required=True, help='ID подкатегории')
@click.option('--no-verify', is_flag=True, help='Не выполнять автоматическую верификацию')
@with_appcontext
def import_products(file_path, supplier_id, subcategory_id, no_verify):
    """Импортировать товары из файла"""
    try:
        # Проверить существование поставщика и подкатегории
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            click.echo(f'Ошибка: Поставщик с ID {supplier_id} не найден', err=True)
            return
        
        subcategory = Subcategory.query.get(subcategory_id)
        if not subcategory:
            click.echo(f'Ошибка: Подкатегория с ID {subcategory_id} не найдена', err=True)
            return
        
        if subcategory.supplier_id != supplier_id:
            click.echo(f'Ошибка: Подкатегория не принадлежит выбранному поставщику', err=True)
            return
        
        click.echo(f'Импорт товаров из файла: {file_path}')
        click.echo(f'Поставщик: {supplier.name}')
        click.echo(f'Подкатегория: {subcategory.name}')
        
        # Выполнить импорт
        result = ImportService.import_from_file(
            file_path,
            subcategory_id,
            supplier_id,
            user=None,
            auto_verify=not no_verify
        )
        
        # Вывести результаты
        click.echo(f'\nРезультаты импорта:')
        click.echo(f'  Импортировано товаров: {result["imported"]}')
        
        if result['errors']:
            click.echo(f'\nОшибки ({len(result["errors"])}):')
            for error in result['errors'][:20]:  # Показать первые 20
                click.echo(f'  - {error}')
        
        if result['warnings']:
            click.echo(f'\nПредупреждения ({len(result["warnings"])}):')
            for warning in result['warnings'][:20]:  # Показать первые 20
                click.echo(f'  - {warning}')
        
        if result['imported'] > 0:
            click.echo(f'\n✓ Импорт завершен успешно!')
        else:
            click.echo(f'\n⚠ Товары не были импортированы')
            
    except Exception as e:
        click.echo(f'Ошибка при импорте: {str(e)}', err=True)
        raise

