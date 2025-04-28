from Source.alert_parser import extract_alert_details, get_data_alert

# Пример алерта с дополнительной информацией
alert_text = """АС Рефлекс Stand: ПРОМ OPEN | Problem Status:P-250477683 | Уровень CUSTOM_ALERTCI05272529_skillflow_pod_failed for Environment Sber PROM2-----CI05272529_skillflow_pod_failed: OPEN Custom Alert P-250477683 in environment Sber PROM2 Problem detected at: 20:14 (MSK) 21.04.2025 Environment impactedEnvironmentSber PROM2CI05272529_skillflow_pod_failed MetricName: Kubernetes: Pod count (by workload)Service Name: SmartNLP.SmartApp навыки ЦКР.SmartApp SkillFlow Metric Event Name: Pod failedRequest: {dims}threshold: 0.8Root causeBased on our dependency analysis all incidents are part of the same overall problem.https://reflex-prom2.ca.sbrf.ru/e/c2be9ac2-9884-4120-973a-a7d485a8b497/#problems/problemdetails;pid=-3017423324473565072_1745255460000V2"""

print("=== Тестирование извлечения полей из алерта ===")
print(f"Исходный текст: {alert_text[:100]}...")

# Проверяем extract_alert_details
details = extract_alert_details(alert_text)
print("\nРезультат extract_alert_details:")
print(f"  timestamp: {details.get('timestamp')}")
print(f"  service: {details.get('service')}")
print(f"  metric_event: {details.get('metric_event')}")
print(f"  request: {details.get('request')}")
print(f"  threshold: {details.get('threshold')}")

# Проверяем get_data_alert
data = get_data_alert(alert_text)
print("\nРезультат get_data_alert:")
for k, v in data.items():
    print(f"  {k}: {v}")

# Проверяем поиск Service Name напрямую
import re
print("\nПроверка поиска Service Name напрямую:")
service_name_match = re.search(r'Service Name:\s*(.*?)(?:(?=Metric Event Name)|(?=Request:)|(?=threshold:))', alert_text, re.IGNORECASE | re.DOTALL)
if service_name_match:
    print(f"Найдено Service Name: {service_name_match.group(1).strip()}")
else:
    print("Service Name не найдено")

# Проверяем поиск Metric Event Name напрямую
metric_event_match = re.search(r'Metric Event Name:\s*([^\.]+?)(?:[\n\.]|Request:|threshold:)', alert_text, re.IGNORECASE)
if metric_event_match:
    print(f"Найдено Metric Event Name: {metric_event_match.group(1).strip()}")
else:
    print("Metric Event Name не найдено") 