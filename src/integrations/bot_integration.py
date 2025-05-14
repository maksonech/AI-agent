"""
Модуль для интеграции функции форматирования в бота.
"""

from Source.alert_parser import extract_alert_details, get_data_alert
from Source.format_alert_response import format_alert_response, format_multiple_alerts

def process_alert(alert_text, show_raw_text=False):
    """
    Обрабатывает текст алерта и формирует ответ бота.
    
    Args:
        alert_text (str): Текст алерта для обработки
        show_raw_text (bool): Флаг, указывающий нужно ли включать исходный текст алерта
        
    Returns:
        str: Отформатированный ответ бота
    """
    # Получаем данные алерта
    alert_data = get_data_alert(alert_text)
    
    # Добавляем исходный текст для форматирования
    alert_data['raw_text'] = alert_text
    
    # Формируем ответ
    response = format_alert_response(alert_data, include_raw_text=show_raw_text)
    
    return response

def process_multiple_alerts(alerts_texts, show_raw_text=False):
    """
    Обрабатывает несколько текстов алертов и формирует ответ бота.
    
    Args:
        alerts_texts (list): Список текстов алертов для обработки
        show_raw_text (bool): Флаг, указывающий нужно ли включать исходный текст алерта
        
    Returns:
        str: Отформатированный ответ бота
    """
    alerts_data = []
    
    for alert_text in alerts_texts:
        # Получаем данные алерта
        alert_data = get_data_alert(alert_text)
        
        # Добавляем исходный текст для форматирования
        alert_data['raw_text'] = alert_text
        
        alerts_data.append(alert_data)
    
    # Формируем ответ
    response = format_multiple_alerts(alerts_data, include_raw_text=show_raw_text)
    
    return response

# ======================================================================
#     ИНСТРУКЦИЯ ПО ИНТЕГРАЦИИ В БОТА
# ======================================================================
"""
Для правильной интеграции в бота:

1. Импортируйте функции из этого модуля:
   from Source.bot_integration import process_alert, process_multiple_alerts

2. Для обработки одного алерта используйте:
   response = process_alert(alert_text, show_raw_text=False)
   
   ВАЖНО: Параметр show_raw_text должен быть False, чтобы не показывать исходный текст алерта.

3. Для обработки нескольких алертов используйте:
   response = process_multiple_alerts(alerts_texts, show_raw_text=False)

4. Отправьте полученный ответ пользователю вместо старого формата.

Пример:

def process_user_message(message):
    # Получение текста алерта из сообщения пользователя
    alert_text = extract_alert_from_message(message)
    
    # Обработка алерта с использованием новой функции
    response = process_alert(alert_text, show_raw_text=False)
    
    # Отправка ответа пользователю
    send_message_to_user(response)
"""

# Пример использования
if __name__ == "__main__":
    # Пример алерта
    alert_text = """АС Рефлекс Stand: ПРОМ OPEN | Problem Status:P-250477683 | Уровень CUSTOM_ALERT CI05272529_skillflow_pod_failed for Environment Sber PROM2-----CI05272529_skillflow_pod_failed: OPEN Custom Alert P-250477683 in environment Sber PROM2 Problem detected at: 20:14 (MSK) 21.04.2025 Environment impactedEnvi"""
    
    # Обработка алерта
    response = process_alert(alert_text, show_raw_text=False)
    print("=== Ответ бота БЕЗ исходного текста алерта ===")
    print(response)
    
    print("\n====================\n")
    
    # Обработка нескольких алертов
    alerts_texts = [
        alert_text,
        """АС Рефлекс Stand: ПРОМ RESOLVED | Problem Status:P-250477684 | Уровень CUSTOM_ALERT Другой пример алерта Problem detected at: 21:30 (MSK) 21.04.2025"""
    ]
    
    response = process_multiple_alerts(alerts_texts, show_raw_text=False)
    print("=== Ответ бота для нескольких алертов ===")
    print(response) 