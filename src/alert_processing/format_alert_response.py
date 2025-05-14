"""
Модуль для форматирования ответа бота на основе данных алерта.
"""

def format_alert_response(alert_data, include_raw_text=False):
    """
    Форматирует ответ бота на основе данных алерта.
    
    Args:
        alert_data (dict): Словарь с данными алерта
        include_raw_text (bool): Флаг, указывающий нужно ли включать исходный текст алерта
        
    Returns:
        str: Отформатированный ответ бота
    """
    response = []
    
    # Заголовок алерта
    response.append(f"# Алерт ID: {alert_data.get('alert_id', 'Unknown')} - {alert_data.get('status', 'UNKNOWN')}")
    response.append("")
    
    # Основная информация
    response.append(f"**Сервис:** {alert_data.get('service', 'Не указан')}")
    
    # Добавляем тип, если он есть
    if 'alert_id' in alert_data:
        response.append(f"**Тип:** Problem Status:P-{alert_data.get('alert_id')}")
    
    # Добавляем HTTP код, если он есть
    if 'http_code' in alert_data and alert_data.get('http_code') != 'Неизвестно':
        response.append(f"**HTTP код:** {alert_data.get('http_code')}")
    
    # Добавляем время, если оно есть
    if 'timestamp' in alert_data and alert_data.get('timestamp') != 'Не указано':
        response.append(f"**Время:** {alert_data.get('timestamp')}")
    
    # Добавляем метрику, если она есть
    if 'metric' in alert_data:
        response.append(f"**Метрика:** {alert_data.get('metric')}")
    
    # Добавляем Metric Event Name, если оно есть
    if 'metric_event' in alert_data:
        response.append(f"**Metric Event Name:** {alert_data.get('metric_event')}")
    
    # Добавляем Request, если он есть
    if 'request' in alert_data:
        response.append(f"**Request:** {alert_data.get('request')}")
    
    # Добавляем пороговое значение, если оно есть
    if 'threshold' in alert_data:
        response.append(f"**Пороговое значение:** {alert_data.get('threshold')}")
    
    # Добавляем текущее значение, если оно есть
    if 'current_value' in alert_data:
        response.append(f"**Текущее значение:** {alert_data.get('current_value')}")
    
    # Добавляем длительность, если она есть
    if 'duration' in alert_data:
        response.append(f"**Длительность:** {alert_data.get('duration')}")
    
    # Добавляем количество затронутых сервисов, если оно есть
    if 'services_impacted' in alert_data and alert_data.get('services_impacted') > 0:
        response.append(f"**Затронуто сервисов:** {alert_data.get('services_impacted')}")
    
    # Добавляем сообщение об ошибке, если оно есть и отличается от "Нет информации об ошибке"
    if 'error_message' in alert_data and alert_data.get('error_message') != 'Нет информации об ошибке':
        response.append(f"**Сообщение об ошибке:** {alert_data.get('error_message')}")
    
    # Опционально добавляем исходный текст алерта
    if include_raw_text and 'raw_text' in alert_data:
        response.append("")
        response.append("**Исходный текст алерта:**")
        response.append("```")
        response.append(alert_data.get('raw_text')[:150] + "...")
        response.append("```")
    
    return "\n".join(response)


def format_multiple_alerts(alerts_data, include_raw_text=False):
    """
    Форматирует ответ бота для нескольких алертов.
    
    Args:
        alerts_data (list): Список словарей с данными алертов
        include_raw_text (bool): Флаг, указывающий нужно ли включать исходный текст алерта
        
    Returns:
        str: Отформатированный ответ бота
    """
    if not alerts_data:
        return "Нет алертов для отображения."
    
    response = []
    
    for i, alert in enumerate(alerts_data):
        response.append(f"### Алерт #{i+1}")
        response.append("")
        formatted_alert = format_alert_response(alert, include_raw_text)
        response.append(formatted_alert)
        
        # Добавляем разделитель между алертами
        if i < len(alerts_data) - 1:
            response.append("")
            response.append("---")
            response.append("")
    
    return "\n".join(response)


# Пример использования
if __name__ == "__main__":
    from alert_parser import extract_alert_details, get_data_alert
    
    # Пример алерта
    alert_text = """АС Рефлекс Stand: ПРОМ OPEN | Problem Status:P-250477683 | Уровень CUSTOM_ALERT CI05272529_skillflow_pod_failed for Environment Sber PROM2-----CI05272529_skillflow_pod_failed: OPEN Custom Alert P-250477683 in environment Sber PROM2 Problem detected at: 20:14 (MSK) 21.04.2025 Environment impactedEnvi"""
    
    # Получаем данные алерта
    alert_data = get_data_alert(alert_text)
    
    # Форматируем ответ бота без исходного текста алерта
    response = format_alert_response(alert_data, include_raw_text=False)
    print(response)
    
    print("\n---\n")
    
    # Форматируем ответ бота с исходным текстом алерта
    response_with_raw = format_alert_response(alert_data, include_raw_text=True)
    print(response_with_raw) 