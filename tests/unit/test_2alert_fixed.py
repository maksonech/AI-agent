"""
Простой тест для проверки исправленной команды "2 алерт".
"""
import os
from src.tools.alert_tools import analyze_file_alert as analyze_file_alert_func

def main():
    """
    Проверяет работу функции analyze_file_alert с параметром alert_number.
    """
    print("=== Тест исправленной команды '2 алерт' ===")
    
    # Путь к тестовому файлу с несколькими алертами
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests', 'fixtures', 'multiple_alerts.txt')
    
    if not os.path.exists(file_path):
        print(f"❌ Ошибка: Тестовый файл не найден: {file_path}")
        return
    
    print(f"Файл найден: {file_path}")
    
    # Тестируем с номером алерта 2
    alert_number = 2
    
    try:
        print(f"\nТест с номером алерта {alert_number}:")
        result = analyze_file_alert_func(file_path=file_path, alert_number=alert_number)
        print(f"✅ Успех! Получен результат длиной {len(result)} символов")
        print("\nПервые 200 символов результата:")
        print("-" * 50)
        print(result[:200] + "..." if len(result) > 200 else result)
        print("-" * 50)
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    print("\nТест завершен.") 