from Source.tools import analyze_single_alert

# Тестовый алерт с форматом времени "20:14 (MSK) 21.04.2025"
test_alert = """АС Рефлекс Stand: ПРОМ OPEN | Problem Status:P-250477683 | Уровень CUSTOM_ALERTCI05272529_skillflow_pod_failed for Environment Sber PROM2-----CI05272529_skillflow_pod_failed: OPEN Custom Alert P-250477683 in environment Sber PROM2 Problem detected at: 20:14 (MSK) 21.04.2025 Environment impactedEnvir"""

# Анализируем алерт
result = analyze_single_alert(test_alert, include_bot_analysis=False)

# Выводим результат
print("Результат анализа алерта:")
print(result)

# Проверяем, что время правильно распознано
if "Время не указано" in result:
    print("\nОШИБКА: Время не было распознано!")
else:
    print("\nУСПЕХ: Время успешно распознано в алерте!") 