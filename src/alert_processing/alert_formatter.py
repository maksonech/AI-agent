#!/usr/bin/env python
"""
Скрипт для преобразования многострочного формата алерта в однострочный.
Читает данные из TestAlerts/sample_alert.txt и записывает в TestAlerts/one_line_alert.txt
"""
import os
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('alert_formatter')

def format_alert_to_one_line(input_file_path, output_file_path):
    """
    Преобразует алерт из многострочного формата в однострочный
    
    Args:
        input_file_path: Путь к входному файлу с многострочным алертом
        output_file_path: Путь к выходному файлу для записи однострочного алерта
    
    Returns:
        bool: True, если преобразование прошло успешно, иначе False
    """
    try:
        # Проверяем существование входного файла
        if not os.path.exists(input_file_path):
            logger.error(f"Входной файл не найден: {input_file_path}")
            return False
        
        # Читаем содержимое входного файла как список строк
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()
        
        logger.info(f"Прочитано {len(lines)} строк из файла {input_file_path}")
        
        # Объединяем все строки в одну, заменяя переносы строк на пробелы
        # Игнорируем пустые строки и строки, содержащие только пробельные символы
        one_line_alert = ' '.join([line.strip() for line in lines if line.strip()])
        
        # Удаляем последовательности из нескольких пробелов
        while '  ' in one_line_alert:
            one_line_alert = one_line_alert.replace('  ', ' ')
        
        logger.info(f"Создан однострочный алерт длиной {len(one_line_alert)} символов")
        
        # Создаем директорию для выходного файла, если она не существует
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        
        # Записываем преобразованный алерт в выходной файл
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(one_line_alert)
        
        logger.info(f"Преобразованный алерт успешно записан в файл {output_file_path}")
        logger.info(f"Размер выходного файла: {os.path.getsize(output_file_path)} байт")
        
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при преобразовании алерта: {str(e)}", exc_info=True)
        return False

def main():
    """
    Основная функция скрипта
    """
    # Определяем путь к директории проекта
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Формируем пути к файлам
    input_file_path = os.path.join(project_dir, 'TestAlerts/sample_alert.txt')
    output_file_path = os.path.join(project_dir, 'TestAlerts/one_line_alert.txt')
    
    print(f"Исходный файл: {input_file_path}")
    print(f"Целевой файл: {output_file_path}")
    
    # Выполняем преобразование
    success = format_alert_to_one_line(input_file_path, output_file_path)
    
    if success:
        print(f"✅ Алерт успешно преобразован из файла {input_file_path} в файл {output_file_path}")
        
        # Показываем содержимое преобразованного файла
        try:
            with open(output_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print("\nСодержимое файла one_line_alert.txt:")
                print(f"{content[:100]}..." if len(content) > 100 else content)
        except Exception as e:
            print(f"Ошибка при чтении файла: {str(e)}")
    else:
        print(f"❌ Не удалось преобразовать алерт")

if __name__ == "__main__":
    main() 