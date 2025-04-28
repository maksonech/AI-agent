from Source.alert_parser import extract_alert_details, get_data_alert

# Тестовые алерты с разными форматами времени
test_alerts = [
    # Формат MSK (основной)
    """АС Рефлекс Stand: ПРОМ OPEN | Problem Status:P-250477683 | Уровень CUSTOM_ALERTCI05272529_skillflow_pod_failed for Environment Sber PROM2-----CI05272529_skillflow_pod_failed: OPEN Custom Alert P-250477683 in environment Sber PROM2 Problem detected at: 20:14 (MSK) 21.04.2025 Environment impactedEnvir""",
    
    # Формат AM/PM
    """ПРОМ | Сервис веб-мониторинга | OPEN Custom Alert P-12345 in environment Production Problem detected at: 10:15 AM 25.04.2023 - 11:30 AM 25.04.2023 (was open for 75 minutes) 1 impacted service Web Monitoring System HTTP ERROR 503 - Service unavailable.""",
    
    # Другой формат с датой
    """CI02858346_cccore_общий_main_metric: RESOLVED Custom Alert P-250433353 in environment Sber PROM2 Problem detected at: 13:47 (MSK) 10.04.2025 1 impacted service Web request service default web request""",
    
    # Формат без часового пояса
    """test alert Problem detected at: 15:30 10.05.2023 - example alert with time but no timezone"""
]

# Тестируем каждый алерт
for i, alert in enumerate(test_alerts):
    print(f"\n=== Тест #{i+1} ===")
    print(f"Текст алерта (начало): {alert[:70]}...")
    
    # Тестируем extract_alert_details
    details = extract_alert_details(alert)
    print(f"extract_alert_details -> timestamp: {details.get('timestamp')}")
    
    # Тестируем get_data_alert
    extended = get_data_alert(alert)
    print(f"get_data_alert -> timestamp: {extended.get('timestamp')}")
    
    # Проверяем соответствие
    if details.get('timestamp') == extended.get('timestamp'):
        print("✅ Значения совпадают")
    else:
        print("❌ Значения отличаются!")

print("\nВсе тесты выполнены.") 