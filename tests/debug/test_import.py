#!/usr/bin/env python3

with open('test_results.txt', 'w', encoding='utf-8') as f:
    f.write("Проверка импорта\n")
    try:
        from src.tools.alert_tools import get_data_alert, analyze_file_alert
        f.write("Импорт успешен!\n")
        
        # Проверка типов
        f.write(f"Тип get_data_alert: {type(get_data_alert)}\n")
        f.write(f"Тип analyze_file_alert: {type(analyze_file_alert)}\n")
        
    except ImportError as e:
        f.write(f"Ошибка импорта: {e}\n")
    except Exception as e:
        f.write(f"Другая ошибка: {e}\n") 