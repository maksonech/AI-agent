"""
Тестовый скрипт для отладки команд бота
"""
import os
import sys
import re
import logging
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('debug_commands')

def main():
    # Создаем уникальный ID для сессии
    thread_id = "debug_session_123"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Шаг 1: Анализируем файл с несколькими алертами для создания контекста
    print("Шаг 1: Анализ файла с несколькими алертами...")
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fixtures', 'multiple_alerts.txt')
    
    # Читаем содержимое файла
    with open(file_path, 'r', encoding='utf-8') as f:
        all_alerts_text = f.read()
    
    # Разделяем на алерты
    alert_starts = re.finditer(r'(?:^|\n)(?:ПРОМ|PROM|DEV) \|', all_alerts_text)
    alert_positions = [match.start() for match in alert_starts]
    
    if not alert_positions:
        alt_alert_starts = re.finditer(r'(?:^|\n)АС Рефлекс', all_alerts_text)
        alert_positions = [match.start() for match in alt_alert_starts]
    
    # Делим текст на отдельные алерты
    alerts = []
    for i in range(len(alert_positions)):
        start = alert_positions[i]
        end = alert_positions[i+1] if i < len(alert_positions) - 1 else len(all_alerts_text)
        alert_content = all_alerts_text[start:end].strip()
        alerts.append(alert_content)
    
    print(f"Найдено {len(alerts)} алертов в файле {os.path.basename(file_path)}")
    
    # Шаг 2: Сохраняем информацию о файле в контексте диалога
    print("Шаг 2: Сохранение информации о файле в контексте...")
    basename = os.path.basename(file_path)
    save_to_context = f"""Я проанализировал алерты из файла {basename}. 

В файле содержится {len(alerts)} алертов.
"""
    try:
        agent.invoke({"messages": [("user", "Сохрани информацию о проанализированных алертах:"), ("assistant", save_to_context)]}, config=config)
        print("Информация успешно сохранена в контексте диалога.")
    except Exception as e:
        print(f"Ошибка при сохранении контекста: {str(e)}")
        return
    
    # Шаг 3: Используем прямой вызов analyze_file_alert с указанием номера алерта
    print("\nШаг 3: Тестирование функции analyze_file_alert с номером алерта...")
    alert_number = 2
    try:
        print(f"Вызов analyze_file_alert с номером алерта {alert_number}")
        analysis_result = analyze_file_alert_func(file_path=file_path, alert_number=alert_number)
        print(f"Результат успешно получен, длина: {len(analysis_result)}")
        print("\n=== Результат анализа алерта через analyze_file_alert ===")
        print(analysis_result[:500] + "..." if len(analysis_result) > 500 else analysis_result)
    except Exception as e:
        print(f"Ошибка при вызове analyze_file_alert: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Шаг 4: Сохраняем контекст для последующих запросов
    print("\nШаг 4: Сохранение информации о конкретном алерте в контексте...")
    try:
        # Выбираем алерт
        specific_alert_text = alerts[alert_number - 1] if alert_number <= len(alerts) else ""
        
        # Контекст для бота
        context_message = f"""Я проанализировал алерт #{alert_number} из файла {basename}. 

Оригинальный текст алерта:
```
{specific_alert_text}
```
"""
        
        # Сохраняем контекст
        agent.invoke({"messages": [("user", "Сохрани информацию о выбранном алерте:"), ("assistant", context_message)]}, config=config)
        print("Контекст для алерта №2 успешно сохранен.")
    except Exception as e:
        print(f"Ошибка при сохранении контекста: {str(e)}")
    
    # Шаг 5: Отправка запроса "2 алерт" через invoke
    print("\nШаг 5: Отправка запроса '2 алерт' через invoke...")
    try:
        # Прямое использование invoke для запроса "2 алерт"
        query = "2 алерт"
        print(f"Отправка запроса: '{query}'")
        response = agent.invoke({"messages": [("user", query)]}, config=config)
        
        # Вывод информации о полученном ответе
        print(f"Тип ответа: {type(response)}")
        if hasattr(response, 'keys'):
            print(f"Структура ответа: {list(response.keys())}")
            
            # Проверка наличия ключевых полей
            if "messages" in response:
                print(f"Количество сообщений: {len(response['messages'])}")
                for i, msg in enumerate(response["messages"]):
                    print(f"Сообщение {i+1}:")
                    if hasattr(msg, 'content'):
                        print(f"  Тип контента: {type(msg.content)}")
                        print(f"  Длина контента: {len(msg.content) if isinstance(msg.content, str) else 'не строка'}")
                        print(f"  Начало контента: {msg.content[:50] if isinstance(msg.content, str) else 'не строка'}")
                    else:
                        print(f"  Нет атрибута 'content'")
                        print(f"  Атрибуты: {dir(msg)}")
            
            elif "output" in response:
                print(f"Поле 'output' содержит текст длиной {len(response['output'])}")
                print(f"Начало текста: {response['output'][:100]}")
        
        print("\nОбработка ответа...")
        # Пытаемся получить последнее сообщение
        bot_response = None
        
        if isinstance(response, str):
            bot_response = response
        elif isinstance(response, dict):
            if "output" in response:
                bot_response = response["output"]
            elif "messages" in response:
                # Извлекаем последнее сообщение от бота
                bot_messages = [msg for msg in response["messages"] if hasattr(msg, "content") and isinstance(msg.content, str) and len(msg.content.strip()) > 0]
                if bot_messages:
                    bot_response = bot_messages[-1].content
                else:
                    bot_response = "Не найдено текстовых сообщений в ответе"
            else:
                # Пробуем найти любое текстовое поле
                text_fields = {}
                for key, value in response.items():
                    if isinstance(value, str) and len(value) > 10:
                        text_fields[key] = value
                        
                if text_fields:
                    # Берем самое длинное текстовое поле
                    field_key = max(text_fields.items(), key=lambda x: len(x[1]))[0]
                    bot_response = text_fields[field_key]
                else:
                    bot_response = str(response)
        else:
            bot_response = str(response)
            
        print("\nИтоговый ответ от agent.invoke с запросом '2 алерт':")
        print(bot_response[:500] + "..." if len(bot_response) > 500 else bot_response)
        
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    print("\nОтладка завершена.") 