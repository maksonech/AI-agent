from Source.alert_parser import extract_alert_details, get_data_alert

# Алерт из бота
alert_text = """АС Рефлекс Stand: ПРОМ OPEN | Problem Status:P-250477683 | Уровень CUSTOM_ALERT CI05272529_skillflow_pod_failed for Environment Sber PROM2-----CI05272529_skillflow_pod_failed: OPEN Custom Alert P-250477683 in environment Sber PROM2 Problem detected at: 20:14 (MSK) 21.04.2025 Environment impactedEnvi"""

print("=== Тестирование алерта из бота ===")
print(f"Исходный текст: {alert_text}")

# Прямая проверка наличия даты в тексте
import re
print("\nПроверка наличия 'Problem detected at:' в тексте:")
time_match = re.search(r'Problem detected at:(.*)', alert_text)
if time_match:
    print(f"Найдено: '{time_match.group(0)}'")
else:
    print("Pattern 'Problem detected at:' не найден в тексте алерта!")

# Проверяем extract_alert_details
details = extract_alert_details(alert_text)
print("\nРезультат extract_alert_details:")
print(f"  timestamp: {details.get('timestamp')}")
print(f"  service: {details.get('service')}")

# Проверяем get_data_alert
data = get_data_alert(alert_text)
print("\nРезультат get_data_alert:")
for k, v in data.items():
    print(f"  {k}: {v}")

# Создаем вывод в формате бота
print("\nПример вывода бота:")
print("### Алерт #1")
print("")
print(f"# Алерт ID: {data.get('alert_id')} - {data.get('status')}")
print("")
print(f"**Сервис:** {data.get('service')}")
print(f"**Тип:** Problem Status:P-{data.get('alert_id')}")
print(f"**HTTP код:** {data.get('http_code')}")
print(f"**Время:** {data.get('timestamp')}")
print("")
print("**Исходный текст алерта:**")
print("```")
print(alert_text[:150] + "...")
print("```") 