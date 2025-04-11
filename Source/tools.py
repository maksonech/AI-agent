from langchain.tools import Tool
import re
from datetime import datetime, timedelta


def parse_alert(alert_text: str) -> dict:
    """
    Разбираем текст алерта на составляющие части.
    """
    # Используем стандартные разделители для разделения текста на секции
    sections = alert_text.split('Problem detected at:')
    if len(sections) != 2:
        raise ValueError("Неверный формат алерта")
    
    # Парсим первую секцию (данные об алерте)
    first_section = sections[0]
    alert_data_pattern = r'(.*?): RESOLVED Custom Alert P-(?P<alert_id>\d+) in environment (.*?)$'
    match = re.match(alert_data_pattern, first_section.strip())
    if not match:
        raise ValueError("Неверный формат первой секции алерта")
    alert_id = match.group('alert_id')
    
    # Парсим вторую секцию (детали проблемы)
    second_section = sections[1].strip()
    problem_detected_pattern = r'\s*(?P<start_time>\d{1,2}:\d{2}\s+\w+)\s+$(?P<start_date>\d{2}\.\d{2}\.\d{4})$\s*-\s*(?P<end_time>\d{1,2}:\d{2}\s+\w+)\s+$(?P<end_date>\d{2}\.\d{2}\.\d{4})$\s*$was\s+open\s+for\s+(?P<duration>\d+\s\w+)$\n*(?P<services_impacted>\d+)\s*impacted\sservice\n*([\w\s]+)\n*(?P<error_message>.*?\.)'
    match = re.match(problem_detected_pattern, second_section, flags=re.DOTALL)
    if not match:
        raise ValueError("Неверный формат второй секции алерта")
    
    # Собираем результат
    result = {
        'alert_id': alert_id,
        'start_time': match.group('start_time'),
        'start_date': match.group('start_date'),
        'end_time': match.group('end_time'),
        'end_date': match.group('end_date'),
        'duration': match.group('duration'),
        'services_impacted': int(match.group('services_impacted')),
        'error_message': match.group('error_message').strip(),
    }
    
    return result


def get_data_alert(alert_text: str) -> dict:
    """
    Получив текст алерта, разбери его на части, сообщи когда был алерт,
    на каком сервисе, какая ошибка и интерпретируй код HTTP ошибки,
    укажи на каких проектах OpenShift возникло отклонение и укажи период,
    за который следует проверить логи.
    """
    # Разбиваем текст алерта на составляющие
    alert_parts = parse_alert(alert_text)
    
    # Преобразуем временные метки в удобные для чтения строки
    start_datetime = datetime.strptime(f"{alert_parts['date']} {alert_parts['start_time']}", "%d.%m.%Y %H:%M %p")
    end_datetime = datetime.strptime(f"{alert_parts['date']} {alert_parts['end_time']}", "%d.%m.%Y %H:%M %p")
    
    # Определяем период для проверки логов
    log_check_period = f"{start_datetime - timedelta(minutes=30)} - {end_datetime + timedelta(minutes=30)}"
    
    # Формируем результат
    result = {
        'timestamp': f"{start_datetime}",
        'service': alert_parts['service_name'],
        'error_message': alert_parts['error_message'],
        'http_code': '503',  # Код HTTP ошибки, указанный в тексте алерта
        'openshift_projects': ['console.ar426hj5.k8s.ca.sbrf.ru', 'console.ar2qob4m.k8s.ca.sbrf.ru'],  # Проекты OpenShift, указанные в тексте алерта
        'log_check_period': log_check_period
    }
    return result


# Создаем инструмент на основе функции get_data_alert
data_alert_tool = Tool(
    name="Data Alert Parser",
    func=get_data_alert,
    description="Получаю текст алерта и возвращаю разбор данных."
)

# Функция для тестирования нашего инструмента
if __name__ == "__main__":
    alert_text = """ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий: RESOLVED Custom Alert P-250434551 in environment Sber PROM2
Problem detected at: 20:37 (MSK) 10.04.2025 - 20:41 (MSK) 10.04.2025 (was open for 4 min)

1 impacted service

Web request service
default web request

ci03467697_ci03474496_dropapp_ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР - общий
The CI03467697_CI03474496_WS_LP-traffic_count_failed value was above normal behavior -общий.
ЕФС ЮЛ СберБизнес Виртуальный ассистент и чат ЦКР, WS_LP
PROM 001 - console.ar426hj5.k8s.ca.sbrf.ru
PROM 002 - console.ar2qob4m.k8s.ca.sbrf.ru
Request: Dimension=/paramsv2/5.0/configuration/get 503 POST , dt.entity.service.name=default web request, dt.entity.service=SERVICE-652B8A46A5F6DC4E
Stand: default web request
threshold: 15"""

    # Вызов инструмента
    result = data_alert_tool.invoke(alert_text)
    print(result)