import re
import os
import logging
from datetime import datetime, timedelta

# Настройка логирования для парсера алертов
alert_parser_logger = logging.getLogger('alert_parser_logger')
alert_parser_logger.setLevel(logging.DEBUG)

# Создание директории для логов, если она не существует
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Logs')
os.makedirs(log_dir, exist_ok=True)

# Настройка обработчика для вывода в файл
parser_log_file = os.path.join(log_dir, f'alert_parser_debug_{datetime.now().strftime("%Y-%m-%d")}.log')
file_handler = logging.FileHandler(parser_log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавление обработчика к логгеру
alert_parser_logger.addHandler(file_handler)

def parse_alert(alert_text: str) -> dict:
    """
    Разбираем текст алерта на составляющие части.
    
    Args:
        alert_text: Текст алерта для парсинга
        
    Returns:
        dict: Словарь с данными алерта
    """
    alert_parser_logger.info("Начало парсинга алерта")
    
    # Очищаем текст алерта от лишних пробелов
    alert_text = alert_text.strip()
    
    try:
        # Пытаемся использовать стандартный формат
        # Используем стандартные разделители для разделения текста на секции
        sections = alert_text.split('Problem detected at:')
        if len(sections) == 2:
            # Парсим первую секцию (данные об алерте)
            first_section = sections[0]
            # Обновленный шаблон, учитывающий разные статусы
            alert_data_pattern = r'(.*?): (?P<status>RESOLVED|OPEN|open|resolved) Custom Alert P-(?P<alert_id>\d+) in environment (.*?)$'
            match = re.match(alert_data_pattern, first_section.strip(), re.IGNORECASE)
            if match:
                alert_id = match.group('alert_id')
                alert_status = match.group('status').upper()  # Преобразуем в верхний регистр для унификации
                
                # Парсим вторую секцию (детали проблемы)
                second_section = sections[1].strip()
                problem_detected_pattern = r'\s*(?P<start_time>\d{1,2}:\d{2}\s+\w+)\s+$(?P<start_date>\d{2}\.\d{2}\.\d{4})$\s*-\s*(?P<end_time>\d{1,2}:\d{2}\s+\w+)\s+$(?P<end_date>\d{2}\.\d{2}\.\d{4})$\s*$was\s+open\s+for\s+(?P<duration>\d+\s\w+)$\n*(?P<services_impacted>\d+)\s*impacted\sservice\n*([\w\s]+)\n*(?P<error_message>.*?\.)'
                match = re.match(problem_detected_pattern, second_section, flags=re.DOTALL)
                if match:
                    # Собираем результат
                    result = {
                        'alert_id': alert_id,
                        'status': alert_status,
                        'start_time': match.group('start_time'),
                        'start_date': match.group('start_date'),
                        'end_time': match.group('end_time'),
                        'end_date': match.group('end_date'),
                        'duration': match.group('duration'),
                        'services_impacted': int(match.group('services_impacted')),
                        'error_message': match.group('error_message').strip(),
                    }
                    
                    alert_parser_logger.info(f"Успешно распарсен алерт ID: {alert_id}, Статус: {alert_status}")
                    return result
    except Exception as e:
        alert_parser_logger.error(f"Ошибка при парсинге стандартного формата: {str(e)}")
    
    # Если не удалось распарсить стандартный формат, пробуем альтернативные форматы
    try:
        # Альтернативный формат 1: ПРОМ | Сервис | OPEN/RESOLVED P-12345 in environment
        alternative_pattern = r'(?:ПРОМ|PROM|DEV) \| ([^|]+) \| (?P<status>OPEN|RESOLVED|open|resolved) Custom Alert P-(?P<alert_id>\d+) in environment'
        alt_match = re.search(alternative_pattern, alert_text, re.IGNORECASE)
        if alt_match:
            service_name = alt_match.group(1).strip()
            alert_id = alt_match.group('alert_id')
            alert_status = alt_match.group('status').upper()
            
            # Ищем время в тексте
            time_pattern = r'(\d{1,2}:\d{2}\s+\w+)\s+(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{1,2}:\d{2}\s+\w+)\s+(\d{2}\.\d{2}\.\d{4})'
            time_match = re.search(time_pattern, alert_text)
            if time_match:
                start_time = time_match.group(1)
                start_date = time_match.group(2)
                end_time = time_match.group(3)
                end_date = time_match.group(4)
                
                # Ищем информацию о длительности
                duration_match = re.search(r'was open for (\d+\s\w+)', alert_text)
                duration = duration_match.group(1) if duration_match else "Неизвестно"
                
                # Ищем информацию о затронутых сервисах
                services_match = re.search(r'(\d+) impacted service', alert_text)
                services_impacted = int(services_match.group(1)) if services_match else 0
                
                # Ищем сообщение об ошибке
                error_match = re.search(r'HTTP ERROR (\d{3}) - (.*?)(?:$|\n)', alert_text)
                error_message = ""
                if error_match:
                    error_code = error_match.group(1)
                    error_text = error_match.group(2)
                    error_message = f"HTTP ERROR {error_code} - {error_text}"
                
                # Собираем результат
                result = {
                    'alert_id': alert_id,
                    'status': alert_status,
                    'service_name': service_name,
                    'start_time': start_time,
                    'start_date': start_date,
                    'end_time': end_time,
                    'end_date': end_date,
                    'duration': duration,
                    'services_impacted': services_impacted,
                    'error_message': error_message
                }
                
                alert_parser_logger.info(f"Успешно распарсен алерт (альтернативный формат) ID: {alert_id}, Статус: {alert_status}")
                return result
    except Exception as e:
        alert_parser_logger.error(f"Ошибка при парсинге альтернативного формата: {str(e)}")
    
    # Если ничего не сработало, создаем минимальный набор данных на основе любой доступной информации
    try:
        # Ищем статус алерта
        status_match = re.search(r'(?P<status>OPEN|RESOLVED|ACTIVE|CLOSED)', alert_text, re.IGNORECASE)
        status = status_match.group('status').upper() if status_match else "UNKNOWN"
        
        # Ищем ID алерта
        alert_id_match = re.search(r'P-(\d+)', alert_text)
        alert_id = alert_id_match.group(1) if alert_id_match else "Unknown"
        
        # Ищем сервис
        service_name = extract_service_name(alert_text)
        
        # Ищем сообщение об ошибке, даже если оно не стандартное
        error_message = "Информация об ошибке недоступна"
        http_error_match = re.search(r'HTTP (?:ERROR )?(\d{3}).*?([^\.]+)', alert_text)
        if http_error_match:
            error_code = http_error_match.group(1)
            error_desc = http_error_match.group(2).strip()
            error_message = f"HTTP ERROR {error_code} - {error_desc}"
        
        # Создаем минимальный результат
        result = {
            'alert_id': alert_id,
            'status': status,
            'service_name': service_name,
            'error_message': error_message,
            # Добавляем пустые или дефолтные значения для остальных полей
            'start_time': 'Неизвестно',
            'start_date': 'Неизвестно',
            'end_time': 'Неизвестно',
            'end_date': 'Неизвестно',
            'duration': 'Неизвестно',
            'services_impacted': 0
        }
        
        alert_parser_logger.warning(f"Создан минимальный набор данных для алерта, ID: {alert_id}, Статус: {status}")
        return result
        
    except Exception as e:
        alert_parser_logger.error(f"Не удалось распарсить алерт ни одним из доступных способов: {str(e)}")
        raise ValueError(f"Невозможно распарсить алерт: {str(e)}")


def get_data_alert(alert_text: str) -> dict:
    """
    Получив текст алерта, разбери его на части, сообщи когда был алерт,
    на каком сервисе, какая ошибка и интерпретируй код HTTP ошибки,
    укажи на каких проектах OpenShift возникло отклонение и укажи период,
    за который следует проверить логи.
    
    Args:
        alert_text: Текст алерта для анализа
        
    Returns:
        dict: Словарь с детальной информацией об алерте
    """
    alert_parser_logger.info("Получение расширенных данных алерта")
    
    # СПЕЦИАЛЬНЫЙ ПАТЧ ДЛЯ БОТА: Прямое извлечение времени из текста алерта
    time_direct_match = re.search(r'Problem detected at:\s*(\d{1,2}:\d{2}(?:\s*\([A-Z]+\))?\s*\d{1,2}\.\d{1,2}\.\d{4})', alert_text, re.IGNORECASE)
    direct_timestamp = time_direct_match.group(1) if time_direct_match else None
    
    # Разбиваем текст алерта на составляющие
    alert_parts = parse_alert(alert_text)
    
    # Дополнительно получаем детали с помощью new function
    alert_details = extract_alert_details(alert_text)
    alert_parser_logger.info(f"Извлеченный timestamp: {alert_details.get('timestamp', 'Не было найдено')}")
    
    # Преобразуем временные метки в удобные для чтения строки
    try:
        if alert_parts['start_date'] != 'Неизвестно' and alert_parts['start_time'] != 'Неизвестно':
            start_datetime = datetime.strptime(f"{alert_parts['start_date']} {alert_parts['start_time']}", "%d.%m.%Y %H:%M %p")
            end_datetime = datetime.strptime(f"{alert_parts['end_date']} {alert_parts['end_time']}", "%d.%m.%Y %H:%M %p")
            
            # Определяем период для проверки логов
            log_check_period = f"{start_datetime - timedelta(minutes=30)} - {end_datetime + timedelta(minutes=30)}"
        else:
            # Если даты неизвестны, берем текущее время с запасом
            current_time = datetime.now()
            log_check_period = f"{current_time - timedelta(hours=2)} - {current_time}"
    
    except ValueError as e:
        alert_parser_logger.error(f"Ошибка преобразования времени: {str(e)}")
        # Если преобразование не удалось, используем исходные строки или текущее время
        if alert_parts['start_date'] != 'Неизвестно' and alert_parts['start_time'] != 'Неизвестно':
            log_check_period = f"{alert_parts['start_date']} {alert_parts['start_time']} - {alert_parts['end_date']} {alert_parts['end_time']}"
        else:
            current_time = datetime.now()
            log_check_period = f"{current_time - timedelta(hours=2)} - {current_time}"
    
    # Извлекаем HTTP код из сообщения об ошибке
    http_code = extract_http_code(alert_parts.get('error_message', ''))
    
    # Используем timestamp из detailed extraction
    timestamp = alert_details.get('timestamp', 'Не указано')
    # Используем прямой результат в приоритете, если он есть
    if direct_timestamp:
        timestamp = direct_timestamp
        
    alert_parser_logger.info(f"Итоговый timestamp для ответа: {timestamp}")
    
    # Получаем имя сервиса - предпочитаем значение из alert_details, затем из alert_parts
    service_name = alert_details.get('service')
    if service_name == "Неизвестный сервис" and 'service_name' in alert_parts:
        service_name = alert_parts.get('service_name')
    
    # Формируем результат
    result = {
        'alert_id': alert_parts.get('alert_id', 'Unknown'),
        'status': alert_parts.get('status', 'UNKNOWN'),
        'timestamp': timestamp,
        'service': service_name,
        'error_message': alert_parts.get('error_message', 'Нет информации об ошибке'),
        'http_code': http_code,
        'openshift_projects': extract_openshift_projects(alert_text),
        'log_check_period': log_check_period
    }
    
    # Защита от "Не указано" - если получили "Не указано" и в тексте есть упоминание времени
    if result['timestamp'] == 'Не указано' and 'Problem detected at:' in alert_text:
        time_direct = re.search(r'Problem detected at:\s*([^E]+)', alert_text)
        if time_direct:
            time_str = time_direct.group(1).strip()
            # Удаляем все кроме времени, даты и часового пояса
            time_str = re.sub(r'[^0-9.:() A-Za-z]', '', time_str)
            result['timestamp'] = time_str
    
    # Добавляем метрику, если она есть
    if alert_details.get('metric'):
        result['metric'] = alert_details.get('metric')
    
    # Добавляем Metric Event Name, если есть
    if alert_details.get('metric_event'):
        result['metric_event'] = alert_details.get('metric_event')
    
    # Добавляем Request, если есть
    if alert_details.get('request'):
        result['request'] = alert_details.get('request')
    
    # Добавляем пороговое значение, если есть
    if alert_details.get('threshold'):
        result['threshold'] = alert_details.get('threshold')
    
    # Добавляем текущее значение, если есть
    if alert_details.get('current_value'):
        result['current_value'] = alert_details.get('current_value')
    
    # Добавляем длительность, если есть
    if 'duration' in alert_parts and alert_parts['duration'] != 'Неизвестно':
        result['duration'] = alert_parts['duration']
    elif alert_details.get('duration'):
        result['duration'] = alert_details.get('duration')
    
    # Добавляем информацию о затронутых сервисах
    if 'services_impacted' in alert_parts and alert_parts['services_impacted'] > 0:
        result['services_impacted'] = alert_parts['services_impacted']
    
    alert_parser_logger.info(f"Сформированы расширенные данные для алерта ID: {result['alert_id']}")
    return result


def extract_http_code(error_message: str) -> str:
    """
    Извлекает HTTP код ошибки из сообщения.
    
    Args:
        error_message: Сообщение об ошибке
        
    Returns:
        str: HTTP код или "Неизвестно"
    """
    http_code_match = re.search(r'HTTP (?:ERROR )?(\d{3})|(\d{3}) POST', error_message, re.IGNORECASE)
    if http_code_match:
        return http_code_match.group(1) if http_code_match.group(1) else http_code_match.group(2)
    return "Неизвестно"


def extract_service_name(alert_text: str) -> str:
    """
    Извлекает название сервиса из текста алерта.
    
    Args:
        alert_text: Текст алерта
        
    Returns:
        str: Название сервиса или "Неизвестный сервис"
    """
    # Проверяем несколько паттернов для извлечения имени сервиса
    
    # Паттерн 1: Service Name: Сервис до Metric Event Name или другого ключевого слова
    service_name_match = re.search(r'Service Name:\s*(.*?)(?:(?=Metric Event Name)|(?=Request:)|(?=threshold:))', alert_text, re.IGNORECASE | re.DOTALL)
    if service_name_match:
        return service_name_match.group(1).strip()
    
    # Паттерн 2: ПРОМ/PROM/DEV | Сервис |
    service_match = re.search(r'(?:ПРОМ|PROM|DEV)\s*\|\s*([^|]+?)\s*\|', alert_text)
    if service_match and 'Status' not in service_match.group(1) and not service_match.group(1).strip().startswith('Problem'):
        return service_match.group(1).strip()
    
    # Паттерн 3: Имя сервиса между разделителями
    service_pattern = re.search(r'\|\s*([^|]+?)\s*\|', alert_text)
    if service_pattern and 'Status' not in service_pattern.group(1) and 'OPEN' not in service_pattern.group(1) and 'ПРОМ' not in service_pattern.group(1):
        return service_pattern.group(1).strip()
    
    # Паттерн 4: ищем после "impacted service"
    impacted_service = re.search(r'impacted service\s+([^\n]+)', alert_text, re.IGNORECASE)
    if impacted_service:
        # Берем только первую строку или до первого служебного слова
        service_text = impacted_service.group(1).strip()
        service_name = re.split(r'(Metric Event|Request:|threshold:|default)', service_text)[0].strip()
        return service_name
    
    # Ищем Pattern CI*_skillflow_pod_failed, но с другим приоритетом
    # теперь только если другие методы не сработали
    ci_match = re.search(r'CI\d+_([a-zA-Z0-9_]+)', alert_text)
    if ci_match:
        # Извлекаем имя без преобразования в Title Case
        service_from_ci = ci_match.group(1)
        return service_from_ci
    
    # Если все паттерны не сработали, ищем упоминание сервиса в тексте
    service_candidates = ["app", "service", "system", "application", "pod", "сервис", "система", "приложение"]
    for candidate in service_candidates:
        candidate_match = re.search(r'\b(\w+\s+' + candidate + r')\b', alert_text, re.IGNORECASE)
        if candidate_match:
            return candidate_match.group(1)
    
    return "Неизвестный сервис"


def extract_openshift_projects(alert_text: str) -> list:
    """
    Извлекает названия проектов OpenShift из текста алерта.
    
    Args:
        alert_text: Текст алерта
        
    Returns:
        list: Список названий проектов OpenShift
    """
    # Ищем упоминания консолей OpenShift
    openshift_match = re.findall(r'console\.([a-z0-9]+)\.k8s\.ca\.sbrf\.ru', alert_text)
    if openshift_match:
        return [f"console.{project}.k8s.ca.sbrf.ru" for project in openshift_match]
    
    # Ищем упоминания namespace в Kubernetes
    namespace_match = re.findall(r'namespace[: ]([a-z0-9-]+)', alert_text, re.IGNORECASE)
    if namespace_match:
        return namespace_match
    
    # Если проекты не найдены, возвращаем пустой список
    return []


def extract_additional_alert_info(alert_text: str) -> dict:
    """
    Извлекает дополнительную информацию из текста алерта.
    
    Args:
        alert_text: Текст алерта для анализа
        
    Returns:
        dict: Словарь с дополнительной информацией
    """
    additional_info = {}
    
    # Извлечение информации о компонентах инфраструктуры
    infra_match = re.search(r'(\d+) impacted infrastructure component', alert_text)
    if infra_match:
        additional_info["Затронутые компоненты"] = f"{infra_match.group(1)} инфраструктурных компонентов"
    
    # Извлечение информации о приложениях
    app_match = re.search(r'(\d+) impacted application', alert_text)
    if app_match:
        additional_info["Затронутые приложения"] = f"{app_match.group(1)} приложений"
    
    # Извлечение информации о времени начала и окончания проблемы
    time_match = re.search(r'Problem detected at: (.*?) - (.*?) \(was open for (.*?)\)', alert_text)
    if time_match:
        additional_info["Начало проблемы"] = time_match.group(1)
        additional_info["Окончание проблемы"] = time_match.group(2)
        additional_info["Длительность"] = time_match.group(3)
    
    # Извлечение информации о сервисе
    service_name_match = re.search(r'Service Name: (.*?)(?:\n|$)', alert_text)
    if service_name_match:
        additional_info["Название сервиса"] = service_name_match.group(1).strip()
    
    # Извлечение информации о метрике
    metric_name_match = re.search(r'MetricName: (.*?)(?:\n|$)', alert_text)
    if metric_name_match:
        additional_info["Название метрики"] = metric_name_match.group(1).strip()
    
    # Извлечение информации о событии метрики
    metric_event_match = re.search(r'Metric Event Name: (.*?)(?:\n|$)', alert_text)
    if metric_event_match:
        additional_info["Событие метрики"] = metric_event_match.group(1).strip()
    
    # Извлечение информации о пороговом значении
    threshold_match = re.search(r'threshold: (.*?)(?:\n|$)', alert_text)
    if threshold_match:
        additional_info["Пороговое значение"] = threshold_match.group(1).strip()
    
    # Извлечение URL для просмотра деталей проблемы
    url_match = re.search(r'(https?://[^\s]+)', alert_text)
    if url_match:
        additional_info["URL для просмотра"] = url_match.group(1).strip()
    
    # Извлечение информации о Kubernetes
    kubernetes_match = re.search(r'Kubernetes workload\s*\n\s*(.*?)(?:\n|$)', alert_text)
    if kubernetes_match:
        additional_info["Kubernetes Workload"] = kubernetes_match.group(1).strip()
    
    return additional_info


def get_icon_for_key(key: str) -> str:
    """
    Возвращает иконку для ключа дополнительной информации.
    
    Args:
        key: Ключ дополнительной информации
        
    Returns:
        str: Иконка для ключа
    """
    icon_map = {
        "Затронутые компоненты": "🔌",
        "Затронутые приложения": "📱",
        "Начало проблемы": "🕒",
        "Окончание проблемы": "🕕",
        "Длительность": "⏱️",
        "Название сервиса": "🔧",
        "Название метрики": "📊",
        "Событие метрики": "📈",
        "Пороговое значение": "🔍",
        "URL для просмотра": "🔗",
        "Kubernetes Workload": "☸️"
    }
    
    return icon_map.get(key, "ℹ️")


def extract_alert_details(alert_text):
    """
    Extract detailed components from an alert message.
    
    Args:
        alert_text (str): The alert text to parse
        
    Returns:
        dict: A dictionary containing all extracted alert components
    """
    details = {
        'timestamp': None,
        'severity': None,
        'service': None,
        'metric': None,
        'metric_event': None,
        'request': None,
        'threshold': None,
        'current_value': None,
        'duration': None,
        'status': None,
        'http_code': None,
        'host': None,
        'additional_info': {},
        'raw_text': alert_text
    }
    
    # Extract timestamp (if available)
    timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\]', alert_text)
    if timestamp_match:
        details['timestamp'] = timestamp_match.group(1)
        alert_parser_logger.debug(f"Найден timestamp формата ISO: {timestamp_match.group(1)}")
    else:
        # Try multiple patterns for "Problem detected at:" format
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
                details['timestamp'] = match.group(1)
                alert_parser_logger.debug(f"Найден timestamp по паттерну {i+1}: {match.group(1)}")
                break
        
        if details['timestamp'] is None:
            alert_parser_logger.warning(f"Не удалось найти timestamp в тексте алерта. Проверяемый текст: '{alert_text[:100]}...'")
    
    # Extract severity
    severity_patterns = [
        r'\b(CRITICAL|WARNING|ERROR|INFO)\b',
        r'\b(critical|warning|error|info)\b'
    ]
    
    for pattern in severity_patterns:
        severity_match = re.search(pattern, alert_text, re.IGNORECASE)
        if severity_match:
            details['severity'] = severity_match.group(1).upper()
            break
    
    # Extract service name
    details['service'] = extract_service_name(alert_text)
    
    # Extract HTTP code
    http_code = extract_http_code(alert_text)
    if http_code:
        details['http_code'] = http_code
    
    # Extract host information
    host_match = re.search(r'host[:\s]+([^\s,]+)', alert_text, re.IGNORECASE)
    if host_match:
        details['host'] = host_match.group(1)
    
    # Extract metric information - ищем MetricName или просто metric
    metric_name_match = re.search(r'MetricName:\s*([^\.]+?)(?:[\n\.]|Service Name:|Metric Event Name:|Request:|threshold:)', alert_text, re.IGNORECASE)
    if metric_name_match:
        details['metric'] = metric_name_match.group(1).strip()
    else:
        # Если нет MetricName, ищем просто metric:
        metric_match = re.search(r'metric[:\s]+["\']?([^"\',]+)["\']?', alert_text, re.IGNORECASE)
        if metric_match:
            details['metric'] = metric_match.group(1).strip()
    
    # Extract Metric Event Name
    metric_event_match = re.search(r'Metric Event Name:\s*([^\.]+?)(?:[\n\.]|Request:|threshold:)', alert_text, re.IGNORECASE)
    if metric_event_match:
        details['metric_event'] = metric_event_match.group(1).strip()
    
    # Extract Request information
    request_match = re.search(r'Request:\s*([^\.]+?)(?:[\n\.]|threshold:)', alert_text, re.IGNORECASE)
    if request_match:
        details['request'] = request_match.group(1).strip()
    
    # Extract threshold values
    threshold_match = re.search(r'threshold[:\s]+([0-9.]+)', alert_text, re.IGNORECASE)
    if threshold_match:
        details['threshold'] = float(threshold_match.group(1))
    
    # Extract current value
    current_value_patterns = [
        r'current(?:\s+value)?[:\s]+([0-9.]+)',
        r'value[:\s]+([0-9.]+)'
    ]
    
    for pattern in current_value_patterns:
        current_match = re.search(pattern, alert_text, re.IGNORECASE)
        if current_match:
            details['current_value'] = float(current_match.group(1))
            break
    
    # Extract duration
    duration_match = re.search(r'(?:for|duration)[:\s]+(\d+\s*(?:second|minute|hour|day|s|m|h|d)s?)', alert_text, re.IGNORECASE)
    if duration_match:
        details['duration'] = duration_match.group(1)
    
    # Extract status
    status_match = re.search(r'status[:\s]+(\w+)', alert_text, re.IGNORECASE)
    if status_match:
        details['status'] = status_match.group(1)
    
    # Extract any key-value pairs as additional info
    kv_pairs = re.findall(r'(\w+)[:\s]+([^,]+)', alert_text)
    for key, value in kv_pairs:
        key = key.lower()
        # Skip keys we've already processed
        if key not in ['host', 'metric', 'threshold', 'current', 'value', 'status', 'duration', 'service', 'request']:
            details['additional_info'][key] = value.strip()
    
    return details


if __name__ == "__main__":
    # Тестирование функций парсера
    sample_alert = """ПРОМ | Сервис веб-мониторинга | OPEN Custom Alert P-12345 in environment Production
Problem detected at: 10:15 AM 25.04.2023 - 11:30 AM 25.04.2023 (was open for 75 minutes)
1 impacted service
Web Monitoring System
HTTP ERROR 503 - Service unavailable. The server is temporarily unable to handle this request."""
    
    try:
        parsed_data = parse_alert(sample_alert)
        print("Базовый парсинг алерта:")
        for key, value in parsed_data.items():
            print(f"{key}: {value}")
        
        print("\nРасширенные данные алерта:")
        extended_data = get_data_alert(sample_alert)
        for key, value in extended_data.items():
            print(f"{key}: {value}")
            
        print("\nДополнительная информация:")
        additional_info = extract_additional_alert_info(sample_alert)
        for key, value in additional_info.items():
            icon = get_icon_for_key(key)
            print(f"{icon} {key}: {value}")
        
        print("\nДетальный разбор алерта:")
        detailed_info = extract_alert_details(sample_alert)
        for key, value in detailed_info.items():
            if key != 'raw_text' and key != 'additional_info':
                print(f"{key}: {value}")
        if detailed_info['additional_info']:
            print("\nДополнительные поля:")
            for k, v in detailed_info['additional_info'].items():
                print(f"  {k}: {v}")
                
        # Test with different alert format
        new_alert = """[2023-05-10 14:30:45] CRITICAL: CPU Usage Alert
host: web-server-01
metric: cpu_usage
threshold: 85
current value: 92.5
duration: 15 minutes
The CPU usage has exceeded the threshold for the specified duration.
"""
        print("\n\n=== Тестирование с другим форматом алерта ===")
        detailed_info = extract_alert_details(new_alert)
        for key, value in detailed_info.items():
            if key != 'raw_text' and key != 'additional_info':
                if value is not None:
                    print(f"{key}: {value}")
        if detailed_info['additional_info']:
            print("\nДополнительные поля:")
            for k, v in detailed_info['additional_info'].items():
                print(f"  {k}: {v}")
            
    except Exception as e:
        print(f"Ошибка при тестировании: {str(e)}") 