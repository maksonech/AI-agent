"""
Комплексный тест для проверки всей цепочки обработки команды "2 алерт".
Имитирует действия пользователя от загрузки файла до анализа конкретного алерта.
"""
import os
import sys
import re
from langchain_gigachat.chat_models import GigaChat
from src.core.agent import agent, get_bot_response
from src.tools.alert_tools import analyze_file_alert as analyze_file_alert_func
from config import get_settings
from config.logging_config import setup_chat_logger
from config.exceptions import AIAgentError, FileOperationError

# Настройка логгера
logger = setup_chat_logger()
logger.info("=== Комплексный тест обработки команды '2 алерт' ===")

def main():
    """
    Основная тестовая функция.
    """
    print("=== Комплексный тест обработки команды '2 алерт' ===")
    thread_id = "test_end_to_end_session"
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Шаг 1: Выбираем файл с несколькими алертами
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests', 'fixtures', 'multiple_alerts.txt')
        print(f"Шаг 1: Выбран файл {os.path.basename(file_path)}")
        
        if not os.path.exists(file_path):
            print(f"❌ Ошибка: Файл не найден: {file_path}")
            return
        
        # Шаг 2: Загружаем содержимое файла
        print("Шаг 2: Загрузка содержимого файла...")
        with open(file_path, 'r', encoding='utf-8') as f:
            all_alerts_text = f.read()
        
        print(f"Файл успешно загружен: {len(all_alerts_text)} символов")
        
        # Шаг 3: Разделяем текст на алерты
        print("Шаг 3: Разделение на отдельные алерты...")
        alert_starts = re.finditer(r'(?:^|\n)(?:ПРОМ|PROM|DEV) \|', all_alerts_text)
        alert_positions = [match.start() for match in alert_starts]
        
        if not alert_positions:
            alt_alert_starts = re.finditer(r'(?:^|\n)АС Рефлекс', all_alerts_text)
            alert_positions = [match.start() for match in alt_alert_starts]
        
        alerts = []
        for i in range(len(alert_positions)):
            start = alert_positions[i]
            end = alert_positions[i+1] if i < len(alert_positions) - 1 else len(all_alerts_text)
            alert_content = all_alerts_text[start:end].strip()
            alerts.append(alert_content)
        
        print(f"Найдено {len(alerts)} алертов в файле")
        
        # Шаг 4: Сохраняем информацию о файле в контексте диалога
        print("Шаг 4: Сохранение информации о файле в контексте...")
        basename = os.path.basename(file_path)
        save_to_context = f"""Я проанализировал алерты из файла {basename}. 

В файле содержится {len(alerts)} алертов.
"""
        agent.invoke({"messages": [("user", "Сохрани информацию о проанализированных алертах:"), ("assistant", save_to_context)]}, config=config)
        print("Информация успешно сохранена в контексте")
        
        # Шаг 5: Имитируем выбор алерта #2 (как в команде "2 алерт")
        print("\nШаг 5: Имитация команды '2 алерт'...")
        alert_number = 2
        last_alert_file = file_path
        
        try:
            # Прямой вызов функции для анализа конкретного алерта
            print(f"Вызов analyze_file_alert_func с параметрами: file_path={last_alert_file}, alert_number={alert_number}")
            analysis_result = analyze_file_alert_func(file_path=last_alert_file, alert_number=alert_number)
            
            print(f"✅ Результат успешно получен: {len(analysis_result)} символов")
            
            # Проверка результата
            if "Алерт #2" in analysis_result and "Основная информация" in analysis_result:
                print("✅ Результат содержит корректную информацию об алерте #2")
            else:
                print("❌ Результат не содержит ожидаемой информации")
            
            # Сохранение контекста в истории
            print("\nШаг 6: Сохранение информации о выбранном алерте...")
            specific_alert_text = alerts[alert_number - 1]
            
            save_context = f"""Я проанализировал алерт #{alert_number} из файла {basename}. 

Оригинальный текст алерта:
```
{specific_alert_text}
```
"""
            agent.invoke({"messages": [("user", "Сохрани информацию о выбранном алерте:"), ("assistant", save_context)]}, config=config)
            print("Контекст успешно сохранен")
            
            # Шаг 7: Проверка сохраненного контекста
            print("\nШаг 7: Проверка сохраненного контекста...")
            
            # Создаем запрос к агенту для проверки сохраненной информации
            check_request = "Расскажи кратко об алерте #2, который я недавно анализировал"
            print(f"Отправка запроса: '{check_request}'")
            
            response = agent.invoke({"messages": [("user", check_request)]}, config=config)
            
            # Извлекаем текст ответа
            bot_response = None
            if isinstance(response, dict) and "output" in response:
                bot_response = response["output"]
            elif isinstance(response, dict) and "messages" in response:
                # Извлекаем последнее сообщение от бота
                bot_messages = [msg for msg in response["messages"] if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content]
                if bot_messages:
                    bot_response = bot_messages[-1].content
            
            print("\nОтвет агента:")
            print("-" * 50)
            print(bot_response[:300] + "..." if bot_response and len(bot_response) > 300 else bot_response)
            print("-" * 50)
            
            # Финальное сообщение
            print("\n✅ Тест успешно завершен!")
            return True
            
        except Exception as e:
            print(f"\n❌ Ошибка: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"\n❌ Общая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = main()
    if result:
        print("\nТест пройден успешно!")
    else:
        print("\nТест завершился с ошибками.")
    
    print("\nТестирование завершено.") 