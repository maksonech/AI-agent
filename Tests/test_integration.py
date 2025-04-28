from Source.alert_parser import get_data_alert
from Source.format_alert_response import format_alert_response

# Пример алерта
alert_text = """АС Рефлекс Stand: ПРОМ OPEN | Problem Status:P-250477683 | Уровень CUSTOM_ALERT CI05272529_skillflow_pod_failed for Environment Sber PROM2-----CI05272529_skillflow_pod_failed: OPEN Custom Alert P-250477683 in environment Sber PROM2 Problem detected at: 20:14 (MSK) 21.04.2025 Environment impactedEnvi"""

print("=== НАЧАЛО ТЕСТА ===")

# Шаг 1: Получаем данные алерта
print("Шаг 1: Получение данных алерта")
alert_data = get_data_alert(alert_text)
alert_data['raw_text'] = alert_text
print(f"Данные алерта получены: ID={alert_data.get('alert_id')}, Время={alert_data.get('timestamp')}")

# Шаг 2: Форматируем ответ БЕЗ исходного текста
print("\nШаг 2: Форматирование ответа БЕЗ исходного текста")
response_without_raw = format_alert_response(alert_data, include_raw_text=False)
print("Ответ бота БЕЗ исходного текста:")
print("-" * 50)
print(response_without_raw)
print("-" * 50)

# Шаг 3: Форматируем ответ С исходным текстом для сравнения
print("\nШаг 3: Форматирование ответа С исходным текстом (для сравнения)")
response_with_raw = format_alert_response(alert_data, include_raw_text=True)
print("Ответ бота С исходным текстом:")
print("-" * 50)
print(response_with_raw)
print("-" * 50)

print("\n=== ТЕСТ ЗАВЕРШЕН ===")

# Инструкция для бота
print("""
ИНСТРУКЦИЯ ПО ИНТЕГРАЦИИ:
1. В коде бота при форматировании ответа всегда используйте параметр include_raw_text=False:
   response = format_alert_response(alert_data, include_raw_text=False)

2. Убедитесь, что этот параметр явно указан во всех местах, где вызывается форматирование.

3. Если исходный текст все равно отображается, проверьте, нет ли в коде бота прямого вывода 
   текста алерта, независимо от функции форматирования.
""") 