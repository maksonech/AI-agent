#!/usr/bin/env python
"""
Тестовый скрипт для проверки функции analyze_single_alert с различными алертами
"""
import os
import sys
import logging
import argparse

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_custom_alert')

# Добавляем директорию проекта в пути поиска модулей
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Импортируем функцию для анализа алерта
try:
    from Source.tools import analyze_single_alert, analyze_file_alert
    logger.info("Функции анализа алертов успешно импортированы")
except ImportError as e:
    logger.error(f"Ошибка импорта: {str(e)}")
    print(f"❌ Ошибка импорта: {str(e)}")
    sys.exit(1)

def test_single_alert(alert_file=None):
    """
    Тестирует функцию analyze_single_alert с выбранным алертом
    
    Args:
        alert_file: Путь к файлу с алертом. Если None, предлагает выбор.
    """
    print("=====================================")
    print("Тестирование анализа алерта")
    print("=====================================")
    
    # Список доступных файлов алертов
    alert_files = {
        '1': {
            'name': 'Стандартный алерт',
            'path': os.path.join(project_dir, 'TestAlerts/one_line_alert.txt')
        },
        '2': {
            'name': 'Множественные алерты',
            'path': os.path.join(project_dir, 'TestAlerts/multiple_alerts.txt')
        },
        '3': {
            'name': 'Проблемный алерт',
            'path': os.path.join(project_dir, 'TestAlerts/one_line_problematic_alert.txt')
        }
    }
    
    # Если файл не указан, предлагаем выбрать
    if not alert_file:
        print("Выберите файл с алертом для анализа:")
        for key, file_info in alert_files.items():
            print(f"{key}. {file_info['name']} ({os.path.basename(file_info['path'])})")
        
        choice = input("\nВведите номер файла (1-3): ")
        if choice in alert_files:
            alert_file = alert_files[choice]['path']
        else:
            print("❌ Некорректный выбор. Используем стандартный алерт.")
            alert_file = alert_files['1']['path']
    
    if not os.path.exists(alert_file):
        print(f"❌ Файл не найден: {alert_file}")
        return
    
    # Читаем содержимое файла
    try:
        with open(alert_file, 'r', encoding='utf-8') as f:
            alert_text = f.read()
        print(f"\n📄 Прочитан файл: {alert_file}")
        print(f"   Размер: {len(alert_text)} символов")
        print(f"   Первые 100 символов: {alert_text[:100]}...")
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {str(e)}")
        return
    
    # Анализируем алерт
    print("\n🔍 Выполняем анализ алерта с функцией analyze_single_alert...")
    try:
        result = analyze_single_alert(alert_text)
        print("\n✅ Анализ успешно выполнен!\n")
        print(result)
    except Exception as e:
        print(f"\n❌ Ошибка при анализе алерта: {str(e)}")
        import traceback
        traceback.print_exc()

def test_file_alert(alert_file=None):
    """
    Тестирует функцию analyze_file_alert с выбранным файлом
    
    Args:
        alert_file: Путь к файлу с алертом. Если None, предлагает выбор.
    """
    print("=====================================")
    print("Тестирование анализа файла с алертами")
    print("=====================================")
    
    # Список доступных файлов алертов
    alert_files = {
        '1': {
            'name': 'Стандартный алерт',
            'path': os.path.join(project_dir, 'TestAlerts/one_line_alert.txt')
        },
        '2': {
            'name': 'Множественные алерты',
            'path': os.path.join(project_dir, 'TestAlerts/multiple_alerts.txt')
        },
        '3': {
            'name': 'Проблемный алерт',
            'path': os.path.join(project_dir, 'TestAlerts/one_line_problematic_alert.txt')
        }
    }
    
    # Если файл не указан, предлагаем выбрать
    if not alert_file:
        print("Выберите файл с алертом для анализа:")
        for key, file_info in alert_files.items():
            print(f"{key}. {file_info['name']} ({os.path.basename(file_info['path'])})")
        
        choice = input("\nВведите номер файла (1-3): ")
        if choice in alert_files:
            alert_file = alert_files[choice]['path']
        else:
            print("❌ Некорректный выбор. Используем стандартный алерт.")
            alert_file = alert_files['1']['path']
    
    if not os.path.exists(alert_file):
        print(f"❌ Файл не найден: {alert_file}")
        return
    
    # Анализируем алерт
    print(f"\n🔍 Выполняем анализ файла {os.path.basename(alert_file)} с функцией analyze_file_alert...")
    try:
        result = analyze_file_alert(alert_file)
        print("\n✅ Анализ успешно выполнен!\n")
        print(result)
    except Exception as e:
        print(f"\n❌ Ошибка при анализе файла: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """
    Основная функция с парсингом аргументов
    """
    parser = argparse.ArgumentParser(description='Тестирование анализа алертов')
    parser.add_argument('-f', '--file', choices=['one_line', 'multiple', 'problematic'], 
                        help='Файл для анализа: one_line, multiple или problematic')
    parser.add_argument('-m', '--method', choices=['single', 'file'], default='single',
                        help='Метод анализа: single (analyze_single_alert) или file (analyze_file_alert)')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Интерактивный режим с выбором файла и метода')
    
    args = parser.parse_args()
    
    # Определяем путь к файлу, если указан
    alert_file = None
    if args.file:
        file_mapping = {
            'one_line': os.path.join(project_dir, 'TestAlerts/one_line_alert.txt'),
            'multiple': os.path.join(project_dir, 'TestAlerts/multiple_alerts.txt'),
            'problematic': os.path.join(project_dir, 'TestAlerts/one_line_problematic_alert.txt')
        }
        alert_file = file_mapping.get(args.file)
    
    # Если включен интерактивный режим
    if args.interactive:
        print("Выберите метод анализа:")
        print("1. Анализ одиночного алерта (analyze_single_alert)")
        print("2. Анализ файла с алертами (analyze_file_alert)")
        
        method_choice = input("\nВведите номер метода (1-2): ")
        
        if method_choice == '1':
            test_single_alert(alert_file)
        elif method_choice == '2':
            test_file_alert(alert_file)
        else:
            print("❌ Некорректный выбор метода. Используем анализ одиночного алерта.")
            test_single_alert(alert_file)
    else:
        # Используем метод, указанный в аргументах
        if args.method == 'single':
            test_single_alert(alert_file)
        else:
            test_file_alert(alert_file)

if __name__ == "__main__":
    # Если нет аргументов, запускаем в интерактивном режиме
    if len(sys.argv) == 1:
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        sys.argv.append('-i')  # Добавляем флаг интерактивного режима
    
    main() 