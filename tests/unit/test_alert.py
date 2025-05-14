"""
Тестовый скрипт для отладки команды "2 алерт".
Этот скрипт выполняет шаги, аналогичные обработке команды "2 алерт" в main.py,
и отображает более подробную отладочную информацию.
"""
import os
import sys
import re
from langchain_gigachat.chat_models import GigaChat
from src.core.agent import agent, get_bot_response
from src.tools.alert_tools import analyze_file_alert as analyze_file_alert_func
from config import get_settings
from config.logging_config import setup_chat_logger
from config.settings import get_alert_file_path
from config.exceptions import (
    AIAgentError, FileOperationError, GigaChatAPIError, DataProcessingError,
    format_exception, safe_execute
)

# Настройка логгера
logger = setup_chat_logger()
logger.info("=== Тестовый скрипт для отладки команды '2 алерт' ===")

def main():
    try:
        # 1. Загружаем файл алерта
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests', 'fixtures', 'multiple_alerts.txt')
        logger.info(f"Выбран файл: {file_path}")
        
        # 2. Проверяем существование файла
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            return
            
        alert_number = 2
        
        # 3. Прямой вызов функции analyze_file_alert с указанием номера алерта
        logger.info(f"Прямой вызов analyze_file_alert с номером алерта {alert_number}")
        analysis_result = analyze_file_alert_func(file_path=file_path, alert_number=alert_number)
        
        logger.info(f"Получен результат анализа, длина: {len(analysis_result)}")
        print("\n=== Результат анализа алерта через analyze_file_alert ===")
        print(analysis_result)
        
        # 4. Для сравнения выполним тот же процесс вручную
        logger.info("Для сравнения выполняем тот же процесс вручную...")
        
        # 5. Загружаем содержимое файла
        with open(file_path, 'r', encoding='utf-8') as f:
            all_alerts_text = f.read()
        
        logger.info(f"Прочитано {len(all_alerts_text)} символов из файла")
        
        # 6. Разделяем файл на отдельные алерты
        alert_starts = re.finditer(r'(?:^|\n)(?:ПРОМ|PROM|DEV) \|', all_alerts_text)
        alert_positions = [match.start() for match in alert_starts]
        
        if not alert_positions:
            alt_alert_starts = re.finditer(r'(?:^|\n)АС Рефлекс', all_alerts_text)
            alert_positions = [match.start() for match in alt_alert_starts]
        
        # 7. Делим на алерты
        alerts = []
        for i in range(len(alert_positions)):
            start = alert_positions[i]
            end = alert_positions[i+1] if i < len(alert_positions) - 1 else len(all_alerts_text)
            alert_content = all_alerts_text[start:end].strip()
            alerts.append(alert_content)
        
        logger.info(f"Найдено {len(alerts)} алертов в файле")
        
        # 8. Выбираем второй алерт
        if alert_number > len(alerts):
            logger.error(f"В файле содержится только {len(alerts)} алертов. Нет алерта с номером {alert_number}.")
            return
        
        specific_alert_text = alerts[alert_number - 1]
        logger.info(f"Выбран алерт #{alert_number}, длина: {len(specific_alert_text)} символов")
        
        # 9. Создаем контекст для бота
        basename = os.path.basename(file_path)
        save_to_context = f"""Я проанализировал алерт #{alert_number} из файла {basename}. 

Оригинальный текст алерта:
```
{specific_alert_text}
```
"""
        logger.info("Создан контекст для бота")
        
        # 10. Настраиваем конфигурацию для вызова агента
        config = {"configurable": {"thread_id": "test_session"}}
        
        # 11. Сохраняем контекст в истории диалога
        try:
            logger.info("Сохраняем контекст в истории диалога...")
            agent.invoke({"messages": [("user", "Сохрани информацию о выбранном алерте:"), ("assistant", save_to_context)]}, config=config)
            logger.info("Контекст успешно сохранен")
        except Exception as e:
            logger.error(f"Ошибка при сохранении контекста: {str(e)}", exc_info=True)
            return
        
        # 12. Формируем запрос для анализа
        chat_request = f"""Проанализируй алерт #{alert_number} из файла и дай краткое описание проблемы (1-2 абзаца).
Укажи:
1. Суть проблемы
2. Возможные причины
3. Рекомендуемые действия

В конце обязательно спроси пользователя, нужна ли ему более подробная информация по какому-то аспекту алерта."""
        
        logger.info(f"Сформирован запрос для анализа: {chat_request[:50]}...")
        
        # 13. Делаем прямой вызов функции get_bot_response для тестирования
        try:
            logger.info("Тестируем прямой вызов get_bot_response...")
            bot_response_direct = get_bot_response(chat_request)
            logger.info(f"Прямой вызов get_bot_response успешен, длина ответа: {len(bot_response_direct)}")
            print("\n=== Результат прямого вызова get_bot_response ===")
            print(bot_response_direct)
        except Exception as e:
            logger.error(f"Ошибка при прямом вызове get_bot_response: {str(e)}", exc_info=True)
        
        # 14. Сравниваем результаты
        logger.info("Сравниваем результаты двух подходов...")
        print("\n=== Сравнение результатов ===")
        print(f"Длина analyze_file_alert: {len(analysis_result)} символов")
        if 'bot_response_direct' in locals():
            print(f"Длина get_bot_response: {len(bot_response_direct)} символов")
        else:
            print("Результат get_bot_response недоступен из-за ошибки")
    
    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}", exc_info=True)
        print(f"Общая ошибка: {str(e)}")

if __name__ == "__main__":
    main()
    print("\nТестовый скрипт завершен. Подробности см. в логах.") 