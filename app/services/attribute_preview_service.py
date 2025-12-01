"""
Сервис для предпросмотра файлов с атрибутами
"""
import pandas as pd
import json
import csv
from pathlib import Path
from app.models.attribute import Attribute

class AttributePreviewService:
    """Сервис для предпросмотра файлов перед импортом"""
    
    @staticmethod
    def preview_file(file_path):
        """
        Предпросмотр файла - получить заголовки и примеры данных
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            dict: {
                'sheets': [
                    {
                        'name': 'Sheet1',
                        'columns': ['name', 'type', 'unit', ...],
                        'sample_rows': [...],
                        'total_rows': 10
                    }
                ],
                'file_type': 'excel' | 'csv' | 'json'
            }
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        if file_extension in ['.xlsx', '.xls']:
            return AttributePreviewService._preview_excel(file_path)
        elif file_extension == '.csv':
            return AttributePreviewService._preview_csv(file_path)
        elif file_extension == '.json':
            return AttributePreviewService._preview_json(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")
    
    @staticmethod
    def preview_clipboard_data(clipboard_text):
        """
        Предпросмотр данных из буфера обмена
        
        Args:
            clipboard_text: Текст из буфера обмена (обычно TSV - tab-separated values)
        
        Returns:
            dict: {
                'sheets': [
                    {
                        'name': 'Clipboard',
                        'columns': ['name', 'type', 'unit', ...],
                        'sample_rows': [...],
                        'total_rows': 10
                    }
                ],
                'file_type': 'clipboard'
            }
        """
        import io
        import re
        
        try:
            # Очистить данные от лишних символов
            original_text = clipboard_text
            clipboard_text = clipboard_text.strip()
            
            # Удалить HTML теги, если есть
            clipboard_text = re.sub(r'<[^>]+>', '', clipboard_text)
            
            if not clipboard_text:
                raise ValueError("Буфер обмена пуст. Убедитесь, что данные скопированы из таблицы.")
            
            # Логирование для отладки (только в DEBUG режиме)
            from flask import current_app
            if current_app and current_app.config.get('DEBUG'):
                current_app.logger.debug(f"preview_clipboard_data: длина={len(clipboard_text)}, табуляция={'\\t' in clipboard_text}, переносы={'\\n' in clipboard_text}, запятые={',' in clipboard_text}")
            
            # Разделить на строки (сохранить пустые строки для табличного формата)
            lines = clipboard_text.split('\n')
            
            # Определить, являются ли данные табличными
            # Признаки табличных данных:
            # 1. Наличие табуляции (Excel, Google Sheets)
            # 2. Наличие множественных пробелов между словами (выровненные колонки)
            # 3. Наличие запятых или точек с запятой (CSV формат)
            # 4. Одинаковое количество разделителей в строках
            
            has_tabs = '\t' in clipboard_text
            has_multiple_spaces = '  ' in clipboard_text  # Два или более пробела подряд
            has_commas = ',' in clipboard_text
            has_semicolons = ';' in clipboard_text
            
            # Подсчитать количество разделителей в каждой строке для определения табличной структуры
            is_table_data = False
            if has_tabs:
                # Если есть табуляция - это точно табличные данные
                is_table_data = True
            elif has_commas or has_semicolons:
                # Если есть запятые или точки с запятой, проверить регулярность
                delimiter = ',' if has_commas else ';'
                delimiter_counts = [line.count(delimiter) for line in lines if line.strip()]
                if delimiter_counts and len(set(delimiter_counts)) <= 2:  # Одинаковое или почти одинаковое количество
                    is_table_data = True
            elif has_multiple_spaces:
                # Если есть множественные пробелы, проверить регулярность
                space_counts = [len(re.findall(r'\s{2,}', line)) for line in lines if line.strip()]
                if space_counts and len(set(space_counts)) <= 2:  # Одинаковое или почти одинаковое количество
                    is_table_data = True
            
            # Если определено, что это табличные данные, обработать соответственно
            if is_table_data and has_tabs:
                # Использовать pandas для правильного парсинга TSV с переносами строк в ячейках
                try:
                    import pandas as pd
                    import io
                    
                    # pandas правильно обрабатывает TSV формат с переносами строк внутри ячеек
                    df = pd.read_csv(
                        io.StringIO(clipboard_text),
                        delimiter='\t',
                        header=0,
                        dtype=str,  # Все как строки для сохранения форматирования
                        keep_default_na=False,  # Не преобразовывать пустые значения в NaN
                        on_bad_lines='skip',
                        engine='python'
                    )
                    
                    # Получить заголовки
                    columns = [str(col).strip() for col in df.columns.tolist()]
                    
                    # Если заголовки пустые, использовать первую строку
                    if not columns or all(not col or col.startswith('Unnamed') for col in columns):
                        # Взять первую строку как заголовки
                        first_row = df.iloc[0].tolist() if len(df) > 0 else []
                        columns = [str(cell).strip() if pd.notna(cell) else f'Колонка {i+1}' 
                                  for i, cell in enumerate(first_row)]
                        # Удалить первую строку из данных
                        df = df.iloc[1:].reset_index(drop=True)
                    
                    # Заполнить пустые заголовки
                    for i, col in enumerate(columns):
                        if not col or col.startswith('Unnamed'):
                            columns[i] = f'Колонка {i+1}'
                    
                    # Преобразовать в список списков
                    data_rows = []
                    for idx, row in df.iterrows():
                        row_data = []
                        for col in columns:
                            value = row.get(col, '')
                            if pd.isna(value):
                                value = ''
                            else:
                                value = str(value)
                            row_data.append(value.strip())
                        data_rows.append(row_data)
                    
                    # Добавить первую строку как заголовки, если она не была использована
                    if len(data_rows) == 0 or not all(col.startswith('Колонка ') for col in columns):
                        # Первая строка уже обработана как заголовки
                        pass
                    
                except Exception as e:
                    from flask import current_app
                    if current_app:
                        current_app.logger.warning(f"Ошибка при парсинге через pandas: {e}")
                    # Fallback на ручной парсинг
                    data_rows = []
                    split_lines = clipboard_text.split('\n')
                    
                    # Определить количество табуляций в первой строке (эталон)
                    first_line = split_lines[0] if split_lines else ''
                    expected_tabs = first_line.count('\t')
                    
                    current_row_parts = []
                    i = 0
                    
                    while i < len(split_lines):
                        line = split_lines[i]
                        line_tabs = line.count('\t')
                        
                        # Если в строке ожидаемое количество табуляций - это новая строка таблицы
                        if line_tabs == expected_tabs and expected_tabs > 0:
                            # Завершить предыдущую строку
                            if current_row_parts:
                                data_rows.append(current_row_parts)
                            # Начать новую строку
                            parts = line.split('\t')
                            current_row_parts = [p.strip() for p in parts]
                        elif line_tabs < expected_tabs and current_row_parts:
                            # Меньше табуляций - это продолжение последней ячейки
                            current_row_parts[-1] = (current_row_parts[-1] + '\n' + line).strip()
                        elif line_tabs == 0 and current_row_parts:
                            # Нет табуляций - продолжение ячейки
                            current_row_parts[-1] = (current_row_parts[-1] + '\n' + line).strip()
                        else:
                            # Новая строка (первая или после пустой)
                            if current_row_parts:
                                data_rows.append(current_row_parts)
                            parts = line.split('\t') if '\t' in line else [line]
                            current_row_parts = [p.strip() for p in parts]
                        
                        i += 1
                    
                    # Добавить последнюю строку
                    if current_row_parts:
                        data_rows.append(current_row_parts)
                    
                    # Фильтровать пустые строки
                    data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
                
                if not data_rows:
                    raise ValueError("Нет данных для обработки")
                
                # Если использовался pandas, columns уже определены
                if 'columns' not in locals() or not columns:
                    # Определить максимальное количество колонок
                    max_cols = max(len(row) for row in data_rows) if data_rows else 0
                    
                    if max_cols == 0:
                        raise ValueError("Не удалось определить структуру данных")
                    
                    # Нормализовать строки (добавить пустые колонки если нужно)
                    normalized_rows = []
                    for row in data_rows:
                        while len(row) < max_cols:
                            row.append('')
                        normalized_rows.append(row)
                    
                    # Первая строка - заголовки
                    first_row = normalized_rows[0][:max_cols]
                    columns = []
                    for i, col in enumerate(first_row):
                        col_str = str(col).strip() if col else ''
                        if col_str:
                            columns.append(col_str)
                        else:
                            columns.append(f'Колонка {i+1}')
                    
                    # Если все заголовки пустые, создать автоматические
                    if all(col.startswith('Колонка ') for col in columns):
                        columns = [f'Колонка {i+1}' for i in range(max_cols)]
                        data_start = 0
                    else:
                        while len(columns) < max_cols:
                            columns.append(f'Колонка {len(columns) + 1}')
                        data_start = 1
                else:
                    # Использовались заголовки из pandas
                    max_cols = len(columns)
                    normalized_rows = data_rows
                    data_start = 0
                    
                    # Нормализовать строки
                    for row in normalized_rows:
                        while len(row) < max_cols:
                            row.append('')
                
                # Примеры строк
                sample_rows = []
                for row in normalized_rows[data_start:data_start+3]:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        if i < len(row):
                            value = str(row[i]).strip()
                            row_dict[col] = value[:100] if value else None
                        else:
                            row_dict[col] = None
                    sample_rows.append(row_dict)
                
                total_rows = len(normalized_rows) - data_start
                
                return {
                    'sheets': [{
                        'name': 'Буфер обмена',
                        'columns': columns,
                        'sample_rows': sample_rows,
                        'total_rows': total_rows
                    }],
                    'file_type': 'clipboard'
                }
            
            # Если нет табуляции, но есть другие признаки таблицы, обработать как таблицу
            if is_table_data and not has_tabs:
                # Определить разделитель
                if has_commas:
                    delimiter = ','
                elif has_semicolons:
                    delimiter = ';'
                elif has_multiple_spaces:
                    delimiter = r'\s{2,}'  # Множественные пробелы
                else:
                    delimiter = None
                
                if delimiter:
                    # Обработать как таблицу с этим разделителем
                    data_rows = []
                    for line in lines:
                        if line.strip():
                            if delimiter == r'\s{2,}':
                                parts = re.split(r'\s{2,}', line)
                            else:
                                parts = line.split(delimiter)
                            cleaned_parts = [p.strip() for p in parts]
                            data_rows.append(cleaned_parts)
                    
                    if data_rows:
                        max_cols = max(len(row) for row in data_rows) if data_rows else 0
                        if max_cols > 0:
                            # Нормализовать строки
                            normalized_rows = []
                            for row in data_rows:
                                while len(row) < max_cols:
                                    row.append('')
                                normalized_rows.append(row)
                            
                            # Первая строка - заголовки
                            first_row = normalized_rows[0][:max_cols]
                            columns = []
                            for i, col in enumerate(first_row):
                                col_str = str(col).strip() if col else ''
                                if col_str:
                                    columns.append(col_str)
                                else:
                                    columns.append(f'Колонка {i+1}')
                            
                            # Если все заголовки пустые, создать автоматические
                            if all(col.startswith('Колонка ') for col in columns):
                                columns = [f'Колонка {i+1}' for i in range(max_cols)]
                                data_start = 0
                            else:
                                while len(columns) < max_cols:
                                    columns.append(f'Колонка {len(columns) + 1}')
                                data_start = 1
                            
                            # Примеры строк
                            sample_rows = []
                            for row in normalized_rows[data_start:data_start+3]:
                                row_dict = {}
                                for i, col in enumerate(columns):
                                    if i < len(row):
                                        value = str(row[i]).strip()
                                        row_dict[col] = value[:100] if value else None
                                    else:
                                        row_dict[col] = None
                                sample_rows.append(row_dict)
                            
                            total_rows = len(normalized_rows) - data_start
                            
                            return {
                                'sheets': [{
                                    'name': 'Буфер обмена',
                                    'columns': columns,
                                    'sample_rows': sample_rows,
                                    'total_rows': total_rows
                                }],
                                'file_type': 'clipboard'
                            }
            
            # Если нет явных признаков таблицы, обработать как обычный текст
            # Сначала попробовать разделить по другим разделителям
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            if not non_empty_lines:
                raise ValueError("Нет данных для обработки. Убедитесь, что данные скопированы из таблицы.")
            
            lines = non_empty_lines
            
            # Если только одна строка, попробовать разделить по различным разделителям
            # Это может быть строка заголовков из таблицы
            if len(lines) == 1:
                first_line = lines[0]
                
                from flask import current_app
                if current_app and current_app.config.get('DEBUG'):
                    current_app.logger.debug(f"Обработка одной строки: {repr(first_line[:100])}")
                
                # Попробовать разделить по табуляции (приоритет для табличных данных)
                if '\t' in first_line:
                    parts = first_line.split('\t')
                    # Очистить и оставить все части, даже пустые (они могут быть важны)
                    cleaned_parts = [p.strip() for p in parts]
                    # Если есть хотя бы одна непустая часть, использовать
                    if any(p for p in cleaned_parts):
                        columns = [p if p else f'Колонка {i+1}' for i, p in enumerate(cleaned_parts)]
                        sample_rows = []
                        total_rows = 0
                        return {
                            'sheets': [{
                                'name': 'Буфер обмена',
                                'columns': columns,
                                'sample_rows': sample_rows,
                                'total_rows': total_rows
                            }],
                            'file_type': 'clipboard'
                        }
                
                # Попробовать разделить по запятым
                if ',' in first_line:
                    parts = [p.strip() for p in first_line.split(',') if p.strip()]
                    if len(parts) > 1:
                        columns = parts
                        sample_rows = []
                        total_rows = 0
                        return {
                            'sheets': [{
                                'name': 'Буфер обмена',
                                'columns': columns,
                                'sample_rows': sample_rows,
                                'total_rows': total_rows
                            }],
                            'file_type': 'clipboard'
                        }
                
                # Попробовать разделить по точкам с запятой
                if ';' in first_line:
                    parts = [p.strip() for p in first_line.split(';') if p.strip()]
                    if len(parts) > 1:
                        columns = parts
                        sample_rows = []
                        total_rows = 0
                        return {
                            'sheets': [{
                                'name': 'Буфер обмена',
                                'columns': columns,
                                'sample_rows': sample_rows,
                                'total_rows': total_rows
                            }],
                            'file_type': 'clipboard'
                        }
                
                # Попробовать разделить по множественным пробелам (2+ пробела подряд)
                if '  ' in first_line:
                    parts = [p.strip() for p in re.split(r'\s{2,}', first_line) if p.strip()]
                    if len(parts) > 1:
                        columns = parts
                        sample_rows = []
                        total_rows = 0
                        return {
                            'sheets': [{
                                'name': 'Буфер обмена',
                                'columns': columns,
                                'sample_rows': sample_rows,
                                'total_rows': total_rows
                            }],
                            'file_type': 'clipboard'
                        }
                
                # Если ничего не помогло, попробовать разделить по одиночным пробелам
                # но только если есть много слов (больше 3)
                # Сначала попробовать извлечь фразы в кавычках
                quoted_phrases = re.findall(r'"([^"]+)"', first_line)
                if quoted_phrases:
                    # Есть фразы в кавычках - использовать их как колонки
                    # Заменить фразы в кавычках на плейсхолдеры
                    temp_line = first_line
                    for i, phrase in enumerate(quoted_phrases):
                        temp_line = temp_line.replace(f'"{phrase}"', f'__QUOTE_{i}__', 1)
                    
                    # Разделить оставшееся по пробелам
                    parts = temp_line.split()
                    columns = []
                    quote_idx = 0
                    for part in parts:
                        if part.startswith('__QUOTE_') and part.endswith('__'):
                            # Заменить плейсхолдер на оригинальную фразу
                            idx = int(part.replace('__QUOTE_', '').replace('__', ''))
                            columns.append(quoted_phrases[idx])
                            quote_idx += 1
                        elif part.strip():
                            columns.append(part.strip())
                    
                    # Добавить оставшиеся фразы в кавычках
                    for i in range(quote_idx, len(quoted_phrases)):
                        columns.append(quoted_phrases[i])
                    
                    if len(columns) > 1:
                        sample_rows = []
                        total_rows = 0
                        return {
                            'sheets': [{
                                'name': 'Буфер обмена',
                                'columns': columns,
                                'sample_rows': sample_rows,
                                'total_rows': total_rows
                            }],
                            'file_type': 'clipboard'
                        }
                
                # Если нет кавычек, попробовать умное разделение по пробелам
                # Ищем паттерны: слова, за которыми идут запятые или точки с запятой в скобках
                # Например: "Высота, мм" или "Вес (кг)"
                words = [w.strip() for w in first_line.split() if w.strip()]
                if len(words) > 3:
                    # Попробовать объединить слова, которые выглядят как части одного названия
                    # Если слово начинается с маленькой буквы или является предлогом, объединить с предыдущим
                    columns = []
                    current_phrase = []
                    
                    for i, word in enumerate(words):
                        # Если слово начинается с маленькой буквы или это предлог/союз, объединить с предыдущим
                        if (word and word[0].islower()) or word.lower() in ['в', 'на', 'от', 'до', 'для', 'из', 'к', 'по', 'с', 'у', 'о', 'об', 'и', 'или', 'а', 'но']:
                            if current_phrase:
                                current_phrase.append(word)
                            else:
                                # Если это первое слово и оно маленькое, все равно добавить
                                current_phrase = [word]
                        else:
                            # Если накопилась фраза, добавить её
                            if current_phrase:
                                columns.append(' '.join(current_phrase))
                                current_phrase = []
                            # Начать новую фразу
                            current_phrase = [word]
                    
                    # Добавить последнюю фразу
                    if current_phrase:
                        columns.append(' '.join(current_phrase))
                    
                    # Если получилось больше 1 колонки, использовать
                    if len(columns) > 1:
                        sample_rows = []
                        total_rows = 0
                        return {
                            'sheets': [{
                                'name': 'Буфер обмена',
                                'columns': columns,
                                'sample_rows': sample_rows,
                                'total_rows': total_rows
                            }],
                            'file_type': 'clipboard'
                        }
                    else:
                        # Если не получилось объединить, использовать все слова как отдельные колонки
                        columns = words
                        sample_rows = []
                        total_rows = 0
                        return {
                            'sheets': [{
                                'name': 'Буфер обмена',
                                'columns': columns,
                                'sample_rows': sample_rows,
                                'total_rows': total_rows
                            }],
                            'file_type': 'clipboard'
                        }
            
            # Определить разделитель по первой строке
            first_line = lines[0]
            tab_count = first_line.count('\t')
            comma_count = first_line.count(',')
            semicolon_count = first_line.count(';')
            
            if tab_count > comma_count and tab_count > semicolon_count:
                delimiter = '\t'
            elif comma_count > semicolon_count:
                delimiter = ','
            elif semicolon_count > 0:
                delimiter = ';'
            else:
                # Если нет разделителя, попробовать пробелы (множественные)
                if '  ' in first_line:
                    delimiter = r'\s{2,}'  # Множественные пробелы
                else:
                    delimiter = '\t'  # По умолчанию табуляция
            
            # Создать DataFrame из строки
            try:
                if delimiter == r'\s{2,}':
                    # Для множественных пробелов используем другой подход
                    data_rows = []
                    for line in lines:
                        # Разделить по множественным пробелам
                        parts = re.split(r'\s{2,}', line)
                        data_rows.append(parts)
                    
                    # Определить максимальное количество колонок
                    max_cols = max(len(row) for row in data_rows) if data_rows else 0
                    
                    # Нормализовать строки (добавить пустые колонки если нужно)
                    normalized_rows = []
                    for row in data_rows:
                        while len(row) < max_cols:
                            row.append('')
                        normalized_rows.append(row)
                    
                    # Первая строка - заголовки
                    columns = [str(col).strip() for col in normalized_rows[0][:max_cols]]
                    if not columns or all(not col for col in columns):
                        # Если заголовков нет, создать автоматические
                        columns = [f'Колонка {i+1}' for i in range(max_cols)]
                        data_start = 0
                    else:
                        data_start = 1
                    
                    # Примеры строк
                    sample_rows = []
                    for row in normalized_rows[data_start:data_start+3]:
                        row_dict = {}
                        for i, col in enumerate(columns):
                            if i < len(row):
                                value = str(row[i]).strip()
                                row_dict[col] = value[:100] if value else None
                            else:
                                row_dict[col] = None
                        sample_rows.append(row_dict)
                    
                    total_rows = len(normalized_rows) - data_start
                else:
                    # Обычный разделитель
                    df = pd.read_csv(
                        io.StringIO(clipboard_text), 
                        delimiter=delimiter, 
                        nrows=100,
                        encoding='utf-8',
                        on_bad_lines='skip',
                        engine='python'
                    )
                    
                    # Получить заголовки
                    columns = [str(col).strip() for col in df.columns.tolist()]
                    
                    # Если заголовки пустые или нечитаемые, создать автоматические
                    if not columns or all(not col or col.startswith('Unnamed') for col in columns):
                        # Попробовать использовать первую строку как заголовки
                        first_line_parts = lines[0].split(delimiter)
                        columns = [str(part).strip() or f'Колонка {i+1}' for i, part in enumerate(first_line_parts)]
                        # Перечитать данные без первой строки
                        df = pd.read_csv(
                            io.StringIO('\n'.join(lines[1:])), 
                            delimiter=delimiter, 
                            nrows=100,
                            encoding='utf-8',
                            names=columns,
                            on_bad_lines='skip',
                            engine='python'
                        )
                    
                    # Получить примеры строк
                    sample_rows = []
                    for idx, row in df.head(3).iterrows():
                        row_dict = {}
                        for col in columns:
                            try:
                                value = row[col]
                                if pd.isna(value):
                                    row_dict[col] = None
                                else:
                                    row_dict[col] = str(value).strip()[:100]
                            except (KeyError, IndexError):
                                row_dict[col] = None
                        sample_rows.append(row_dict)
                    
                    total_rows = len(lines) - 1  # -1 для заголовка
                
                return {
                    'sheets': [{
                        'name': 'Буфер обмена',
                        'columns': columns,
                        'sample_rows': sample_rows,
                        'total_rows': max(total_rows, len(sample_rows))
                    }],
                    'file_type': 'clipboard'
                }
            except Exception as parse_error:
                # Если не удалось распарсить, попробовать более простой подход
                # Разделить на строки и колонки вручную
                data_rows = []
                for line in lines:
                    if delimiter == '\t':
                        parts = line.split('\t')
                    elif delimiter == ',':
                        parts = line.split(',')
                    elif delimiter == ';':
                        parts = line.split(';')
                    else:
                        parts = [line]
                    data_rows.append([p.strip() for p in parts])
                
                # Определить максимальное количество колонок
                max_cols = max(len(row) for row in data_rows) if data_rows else 0
                
                if max_cols == 0:
                    raise ValueError("Не удалось определить структуру данных")
                
                # Первая строка - заголовки
                columns = data_rows[0][:max_cols] if data_rows else []
                if not columns or all(not col for col in columns):
                    columns = [f'Колонка {i+1}' for i in range(max_cols)]
                    data_start = 0
                else:
                    data_start = 1
                
                # Примеры строк
                sample_rows = []
                for row in data_rows[data_start:data_start+3]:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        if i < len(row):
                            value = str(row[i]).strip()
                            row_dict[col] = value[:100] if value else None
                        else:
                            row_dict[col] = None
                    sample_rows.append(row_dict)
                
                total_rows = len(data_rows) - data_start
                
                return {
                    'sheets': [{
                        'name': 'Буфер обмена',
                        'columns': columns,
                        'sample_rows': sample_rows,
                        'total_rows': total_rows
                    }],
                    'file_type': 'clipboard'
                }
                
        except ValueError as ve:
            # Пробросить ValueError как есть, но с более понятным сообщением
            error_msg = str(ve)
            if "Не удалось определить структуру данных" in error_msg:
                error_msg += ". Убедитесь, что данные скопированы из таблицы и разделены табуляцией или запятыми."
            raise ValueError(error_msg)
        except Exception as e:
            # Для других ошибок добавить больше контекста
            import traceback
            error_details = traceback.format_exc()
            from flask import current_app
            if current_app:
                current_app.logger.error(f"preview_clipboard_data: Неожиданная ошибка = {str(e)}", exc_info=True)
            raise ValueError(f"Ошибка при обработке данных из буфера обмена: {str(e)}. Убедитесь, что данные скопированы из таблицы и разделены табуляцией или запятыми.")
    
    @staticmethod
    def _preview_excel(file_path):
        """Предпросмотр Excel файла (все листы)"""
        sheets = []
        
        try:
            if file_path.suffix == '.xlsx':
                excel_file = pd.ExcelFile(file_path, engine='openpyxl')
            else:
                excel_file = pd.ExcelFile(file_path, engine='xlrd')
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine=excel_file.engine)
                
                # Получить заголовки
                columns = [str(col).strip() for col in df.columns.tolist()]
                
                # Получить примеры строк (первые 3)
                sample_rows = []
                for idx, row in df.head(3).iterrows():
                    row_dict = {}
                    for col in columns:
                        value = row[col]
                        if pd.isna(value):
                            row_dict[col] = None
                        else:
                            row_dict[col] = str(value)[:100]  # Ограничить длину
                    sample_rows.append(row_dict)
                
                sheets.append({
                    'name': sheet_name,
                    'columns': columns,
                    'sample_rows': sample_rows,
                    'total_rows': len(df)
                })
            
            return {
                'sheets': sheets,
                'file_type': 'excel'
            }
        except Exception as e:
            raise ValueError(f"Ошибка при чтении Excel файла: {str(e)}")
    
    @staticmethod
    def _preview_csv(file_path):
        """Предпросмотр CSV файла"""
        try:
            encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin-1']
            df = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        sample = f.read(1024)
                        f.seek(0)
                        sniffer = csv.Sniffer()
                        delimiter = sniffer.sniff(sample).delimiter
                        df = pd.read_csv(f, delimiter=delimiter, encoding=encoding, nrows=100)
                        break
                except (UnicodeDecodeError, Exception):
                    continue
            
            if df is None:
                raise ValueError("Не удалось определить кодировку CSV файла")
            
            # Получить заголовки
            columns = [str(col).strip() for col in df.columns.tolist()]
            
            # Получить примеры строк
            sample_rows = []
            for idx, row in df.head(3).iterrows():
                row_dict = {}
                for col in columns:
                    value = row[col]
                    if pd.isna(value):
                        row_dict[col] = None
                    else:
                        row_dict[col] = str(value)[:100]
                sample_rows.append(row_dict)
            
            # Подсчитать общее количество строк
            total_rows = sum(1 for _ in open(file_path, 'r', encoding=encoding)) - 1  # -1 для заголовка
            
            return {
                'sheets': [{
                    'name': 'CSV',
                    'columns': columns,
                    'sample_rows': sample_rows,
                    'total_rows': total_rows
                }],
                'file_type': 'csv'
            }
        except Exception as e:
            raise ValueError(f"Ошибка при чтении CSV файла: {str(e)}")
    
    @staticmethod
    def _preview_json(file_path):
        """Предпросмотр JSON файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                # Массив объектов
                first_item = data[0]
                if isinstance(first_item, dict):
                    columns = list(first_item.keys())
                    sample_rows = data[:3]
                    total_rows = len(data)
                else:
                    raise ValueError("Неверный формат JSON: ожидается массив объектов")
            elif isinstance(data, dict):
                if 'attributes' in data and isinstance(data['attributes'], list):
                    # Объект с массивом attributes
                    first_item = data['attributes'][0] if data['attributes'] else {}
                    columns = list(first_item.keys()) if isinstance(first_item, dict) else []
                    sample_rows = data['attributes'][:3]
                    total_rows = len(data['attributes'])
                else:
                    # Один объект
                    columns = list(data.keys())
                    sample_rows = [data]
                    total_rows = 1
            else:
                raise ValueError("Неверный формат JSON файла")
            
            return {
                'sheets': [{
                    'name': 'JSON',
                    'columns': columns,
                    'sample_rows': sample_rows,
                    'total_rows': total_rows
                }],
                'file_type': 'json'
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка при парсинге JSON: {str(e)}")
    
    @staticmethod
    def suggest_mapping(file_columns, existing_attributes):
        """
        Предложить маппинг колонок файла с существующими атрибутами
        
        Args:
            file_columns: Список названий колонок в файле
            existing_attributes: Список существующих атрибутов (dict с code, name)
        
        Returns:
            dict: {column_name: {'attribute_code': '...', 'is_new': False, 'match_score': 0.9}}
        """
        mapping = {}
        
        # Нормализовать колонки
        normalized_columns = {}
        for col in file_columns:
            normalized = col.lower().strip().replace(' ', '_').replace('-', '_')
            normalized_columns[normalized] = col
        
        # Создать индекс существующих атрибутов
        attr_index = {}
        for attr in existing_attributes:
            # По коду
            code_norm = attr['code'].lower().strip()
            attr_index[code_norm] = {'code': attr['code'], 'name': attr['name'], 'type': 'code'}
            
            # По названию
            name_norm = attr['name'].lower().strip()
            attr_index[name_norm] = {'code': attr['code'], 'name': attr['name'], 'type': 'name'}
        
        # Маппинг стандартных полей
        standard_mapping = {
            'code': ['code', 'код', 'id', 'attribute_code', 'attribute_id'],
            'name': ['name', 'название', 'title', 'attribute_name', 'наименование'],
            'type': ['type', 'тип', 'attribute_type', 'тип_атрибута'],
            'description': ['description', 'описание', 'desc', 'комментарий'],
            'unit': ['unit', 'единица', 'единица_измерения', 'unit_of_measure', 'ед_изм'],
            'is_unique': ['is_unique', 'уникальный', 'unique', 'isunique', 'уникальность']
        }
        
        for col_normalized, col_original in normalized_columns.items():
            suggestion = {
                'attribute_code': None,
                'is_new': True,
                'match_score': 0.0,
                'suggested_unit': None
            }
            
            # Проверить стандартные поля
            for field_name, possible_names in standard_mapping.items():
                if col_normalized in [n.lower() for n in possible_names]:
                    suggestion['is_new'] = False
                    suggestion['attribute_code'] = field_name
                    suggestion['match_score'] = 1.0
                    break
            
            # Если не найдено в стандартных, искать в существующих атрибутах
            if suggestion['attribute_code'] is None:
                best_match = None
                best_score = 0.0
                
                for attr_norm, attr_info in attr_index.items():
                    # Простое сравнение строк
                    if col_normalized == attr_norm:
                        score = 1.0
                    elif col_normalized in attr_norm or attr_norm in col_normalized:
                        score = 0.7
                    elif col_normalized.startswith(attr_norm[:3]) or attr_norm.startswith(col_normalized[:3]):
                        score = 0.5
                    else:
                        score = 0.0
                    
                    if score > best_score:
                        best_score = score
                        best_match = attr_info
                
                if best_match and best_score >= 0.5:
                    suggestion['attribute_code'] = best_match['code']
                    suggestion['is_new'] = False
                    suggestion['match_score'] = best_score
            
            # Предложить единицу измерения на основе названия колонки
            if suggestion['is_new']:
                unit_keywords = {
                    'вес': 'кг', 'weight': 'кг',
                    'длина': 'м', 'length': 'м',
                    'ширина': 'м', 'width': 'м',
                    'высота': 'м', 'height': 'м',
                    'глубина': 'м', 'depth': 'м',
                    'объем': 'л', 'volume': 'л',
                    'площадь': 'м²', 'area': 'м²',
                    'диаметр': 'мм', 'diameter': 'мм',
                    'радиус': 'мм', 'radius': 'мм',
                    'мощность': 'Вт', 'power': 'Вт',
                    'напряжение': 'В', 'voltage': 'В',
                    'температура': '°C', 'temperature': '°C'
                }
                
                col_lower = col_normalized.lower()
                for keyword, unit in unit_keywords.items():
                    if keyword in col_lower:
                        suggestion['suggested_unit'] = unit
                        break
            
            mapping[col_original] = suggestion
        
        return mapping

