from Source.alert_parser import extract_alert_details, get_data_alert
from Source.format_alert_response import format_alert_response, format_multiple_alerts

# Пример алерта
alert_text = """АС Рефлекс Stand: ПРОМ OPEN | Problem Status:P-250477683 | Уровень CUSTOM_ALERT CI05272529_skillflow_pod_failed for Environment Sber PROM2-----CI05272529_skillflow_pod_failed: OPEN Custom Alert P-250477683 in environment Sber PROM2 Problem detected at: 20:14 (MSK) 21.04.2025 Environment impactedEnvi"""

print("=== Тестирование форматирования ответа бота ===")

# Получаем данные алерта
alert_data = get_data_alert(alert_text)
alert_data['raw_text'] = alert_text  # Добавляем исходный текст для тестирования

print("\n=== Ответ бота БЕЗ исходного текста алерта ===")
response = format_alert_response(alert_data, include_raw_text=False)
print(response)

print("\n=== Ответ бота С исходным текстом алерта ===")
response_with_raw = format_alert_response(alert_data, include_raw_text=True)
print(response_with_raw)

# Демонстрация форматирования нескольких алертов
print("\n=== Форматирование нескольких алертов ===")

# Создаем имитацию данных для нескольких алертов
alerts_data = [
    alert_data,
    {
        'alert_id': '250477684',
        'status': 'RESOLVED',
        'timestamp': '21:30 (MSK) 21.04.2025',
        'service': 'Another Service',
        'http_code': '500',
        'raw_text': "Другой пример алерта"
    }
]

# Форматируем ответ для нескольких алертов
multiple_response = format_multiple_alerts(alerts_data, include_raw_text=False)
print(multiple_response) 