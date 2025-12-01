"""
Скрипт для резервного копирования базы данных и медиа-файлов
"""
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from config import Config

def backup_database():
    """Создать резервную копию базы данных"""
    db_url = os.environ.get('DATABASE_URL', '')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    if 'postgresql' in db_url:
        # PostgreSQL backup
        backup_file = backup_dir / f'db_backup_{timestamp}.sql'
        try:
            # Извлечь параметры из URL
            # postgresql://user:password@host:port/dbname
            subprocess.run([
                'pg_dump',
                db_url,
                '-f', str(backup_file),
                '--no-owner',
                '--no-acl'
            ], check=True)
            print(f"✅ Резервная копия PostgreSQL создана: {backup_file}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка при создании резервной копии PostgreSQL: {e}")
        except FileNotFoundError:
            print("❌ pg_dump не найден. Установите PostgreSQL client tools.")
    else:
        # SQLite backup
        db_file = Path('app.db')
        if db_file.exists():
            backup_file = backup_dir / f'db_backup_{timestamp}.db'
            shutil.copy(db_file, backup_file)
            print(f"✅ Резервная копия SQLite создана: {backup_file}")
        else:
            print("❌ Файл базы данных не найден")

def backup_media():
    """Создать резервную копию медиа-файлов"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    media_folder = Config.MEDIA_FOLDER
    if media_folder.exists():
        backup_file = backup_dir / f'media_backup_{timestamp}.zip'
        try:
            shutil.make_archive(
                str(backup_dir / f'media_backup_{timestamp}'),
                'zip',
                media_folder
            )
            print(f"✅ Резервная копия медиа-файлов создана: {backup_file}")
        except Exception as e:
            print(f"❌ Ошибка при создании резервной копии медиа-файлов: {e}")
    else:
        print("⚠️ Папка с медиа-файлами не найдена")

def cleanup_old_backups(days=30):
    """Удалить старые резервные копии (старше указанного количества дней)"""
    backup_dir = Path('backups')
    if not backup_dir.exists():
        return
    
    cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
    
    for file in backup_dir.iterdir():
        if file.stat().st_mtime < cutoff_time:
            try:
                file.unlink()
                print(f"🗑️ Удален старый бэкап: {file.name}")
            except Exception as e:
                print(f"❌ Ошибка при удалении {file.name}: {e}")

if __name__ == '__main__':
    print("🔄 Начало резервного копирования...")
    backup_database()
    backup_media()
    cleanup_old_backups()
    print("✅ Резервное копирование завершено")

