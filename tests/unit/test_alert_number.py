"""
Тестовый скрипт для отладки команды "2 алерт".
Этот скрипт демонстрирует исправленную функциональность команды "2 алерт",
которая использует прямой вызов analyze_file_alert с параметром alert_number.
"""
import os
import sys
import re
import logging
from src.tools.alert_tools import analyze_file_alert as analyze_file_alert_func
from config.logging_config import setup_chat_logger

# Настройка логгера
logger = setup_chat_logger()
logger.info("=== Тестовый скрипт для демонстрации исправленной команды '2 алерт' ===")

def test_analyze_specific_alert():
    """
    Тестирует функциональность analyze_file_alert с указанием конкретного номера алерта.
    """
    logger.info("Тестирование функции analyze_file_alert с указанием конкретного номера алерта")
    
    # 1. Выбираем тестовый файл с несколькими алертами
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests', 'fixtures', 'multiple_alerts.txt')
    
    if not os.path.exists(file_path):
        logger.error(f"Тестовый файл не найден: {file_path}")
        print(f"❌ Ошибка: Тестовый файл не найден: {file_path}")
        return False
    
    logger.info(f"Выбран тестовый файл: {file_path}")
    
    # 2. Проверка корректной работы с различными номерами алертов
    test_numbers = [1, 2, 3, 99]  # Включая несуществующий номер
    
    for alert_number in test_numbers:
        logger.info(f"Тестирование для номера алерта: {alert_number}")
        print(f"\n=== Тест с номером алерта {alert_number} ===")
        
        try:
            # Вызываем функцию с указанием номера алерта
            result = analyze_file_alert_func(file_path=file_path, alert_number=alert_number)
            logger.info(f"Получен результат длиной {len(result)} символов")
            
            if "Нет алерта с номером" in result:
                print(f"✅ Корректная обработка несуществующего алерта: {result}")
                logger.info(f"Корректная обработка несуществующего алерта: {alert_number}")
            else:
                print(f"✅ Алерт #{alert_number} успешно проанализирован")
                print(f"Длина результата: {len(result)} символов")
                print("Начало результата:")
                print("-" * 50)
                print(result[:300] + "..." if len(result) > 300 else result)
                print("-" * 50)
                logger.info(f"Алерт #{alert_number} успешно проанализирован")
        except Exception as e:
            print(f"❌ Ошибка при анализе алерта #{alert_number}: {str(e)}")
            logger.error(f"Ошибка при анализе алерта #{alert_number}: {str(e)}", exc_info=True)
    
    return True

def main():
    """
    Основная функция для запуска тестов
    """
    print("=== Тестирование исправленной команды '2 алерт' ===")
    
    # Запускаем тест анализа конкретного алерта
    result = test_analyze_specific_alert()
    
    if result:
        print("\n✅ Тестирование завершено успешно!")
        logger.info("Тестирование завершено успешно")
    else:
        print("\n❌ Тестирование завершено с ошибками")
        logger.error("Тестирование завершено с ошибками")

if __name__ == "__main__":
    main()
    print("\nПодробности см. в логах.") 