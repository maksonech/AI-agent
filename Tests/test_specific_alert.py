from Source.alert_parser import extract_alert_details, get_data_alert

# Конкретный алерт из бота
alert_text = """АС Рефлекс Stand: ПРОМ OPEN | Problem Status:P-250477683 | Уровень CUSTOM_ALERTCI05272529_skillflow_pod_failed for Environment Sber PROM2-----CI05272529_skillflow_pod_failed: OPEN Custom Alert P-250477683 in environment Sber PROM2 Problem detected at: 20:14 (MSK) 21.04.2025 Environment impactedEnvir"""

print("=== Тестирование конкретного алерта из бота ===")
print(f"Исходный текст: {alert_text[:100]}...")

# Проверяем extract_alert_details
details = extract_alert_details(alert_text)
print("\nРезультат extract_alert_details:")
print(f"  timestamp: {details.get('timestamp')}")
print(f"  service: {details.get('service')}")
print(f"  status: {details.get('status')}")

# Проверяем get_data_alert
extended = get_data_alert(alert_text)
print("\nРезультат get_data_alert:")
for k, v in extended.items():
    if k != 'raw_text' and k != 'additional_info':
        print(f"  {k}: {v}")

# Проверяем извлечение времени другими способами
import re
print("\nПроверка регулярных выражений напрямую:")
patterns = [
    # Format: 20:14 (MSK) 21.04.2025
    r'Problem detected at:\s*(\d{1,2}:\d{2}\s*\(MSK\)\s*\d{1,2}\.\d{1,2}\.\d{4})',
    # Format: 10:15 AM 25.04.2023
    r'Problem detected at:\s*(\d{1,2}:\d{2}\s*(?:AM|PM)\s*\d{1,2}\.\d{1,2}\.\d{4})',
    # Format with dash: 21.04.2025 - 15:30
    r'Problem detected at:\s*(\d{1,2}\.\d{1,2}\.\d{4}\s*-\s*\d{1,2}:\d{2})',
    # Format with date first: 21.04.2025 15:30 (with or without timezone)
    r'Problem detected at:\s*(\d{1,2}\.\d{1,2}\.\d{4}\s+\d{1,2}:\d{2}(?:\s*\([A-Z]+\))?)',
    # General format with any timezone
    r'Problem detected at:\s*(\d{1,2}:\d{2}(?:\s*\([A-Z]+\))?\s*\d{1,2}\.\d{1,2}\.\d{4})'
]

for i, pattern in enumerate(patterns):
    match = re.search(pattern, alert_text, re.IGNORECASE)
    if match:
        print(f"Паттерн #{i+1} сработал: {match.group(1)}")

print("\nПоиск любого упоминания Problem detected at:")
detected_at = re.search(r'Problem detected at:.*', alert_text)
if detected_at:
    print(f"Найдено: {detected_at.group(0)}") 