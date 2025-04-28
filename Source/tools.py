from langchain.tools import Tool
import re
import os
import logging
from datetime import datetime, timedelta
from Source.utils import courses_database  # Импортируем обработанный JSON с эндпоинтами
# Импортируем функции парсинга алертов из нового модуля
from Source.alert_parser import (
    parse_alert,
    get_data_alert as parse_get_data_alert,
    extract_additional_alert_info,
    get_icon_for_key
)

# Настройка логирования для инструментов
tool_logger = logging.getLogger('tool_logger')
tool_logger.setLevel(logging.DEBUG)

# Создание директории для логов, если она не существует
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Logs')
os.makedirs(log_dir, exist_ok=True)

# Настройка обработчика для вывода в файл
tool_log_file = os.path.join(log_dir, f'tools_debug_{datetime.now().strftime("%Y-%m-%d")}.log')
file_handler = logging.FileHandler(tool_log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавление обработчика к логгеру
tool_logger.addHandler(file_handler)

# Функция-заглушка на случай, если импорт get_bot_response не удастся
def fallback_bot_response(prompt, max_tokens=1000, alert_data=None):
    return f"Невозможно получить анализ от бота из-за проблемы с импортом функции get_bot_response. Проверьте структуру проекта и импорты."

# Функция get_data_alert теперь является оберткой для функции из alert_parser
def get_data_alert(alert_text: str) -> dict:
    """
    Получив текст алерта, разбери его на части, сообщи когда был алерт,
    на каком сервисе, какая ошибка и интерпретируй код HTTP ошибки,
    укажи на каких проектах OpenShift возникло отклонение и укажи период,
    за который следует проверить логи.
    """
    # Используем функцию из модуля alert_parser
    return parse_get_data_alert(alert_text)

def find_endpoint_info(query: str) -> str:
    """
    Поиск информации об API эндпоинтах по запросу пользователя.
    Использует данные из integration_endpoints.json для формирования ответа.
    """
    matching_endpoints = []
    
    # Очистка запроса от лишних символов и приведение к нижнему регистру
    query = query.lower().strip()
    
    # Поиск по эндпоинтам
    for endpoint in courses_database:
        # Проверка по URL пути
        if query in endpoint.get("request", "").lower():
            matching_endpoints.append(endpoint)
            continue
            
        # Проверка по описанию
        if query in endpoint.get("description", "").lower():
            matching_endpoints.append(endpoint)
            continue
            
        # Проверка по хосту
        if query in endpoint.get("host", "").lower():
            matching_endpoints.append(endpoint)
            continue
    
    # Если найдены подходящие эндпоинты, формируем ответ
    if matching_endpoints:
        result = "Найдены следующие API эндпоинты, соответствующие запросу:\n\n"
        
        for i, endpoint in enumerate(matching_endpoints, 1):
            result += f"{i}. Запрос: {endpoint.get('request', 'Нет данных')}\n"
            result += f"   Описание: {endpoint.get('description', 'Нет описания')}\n"
            result += f"   Хост: {endpoint.get('host', 'Не указан')}\n"
            result += f"   Направление: {endpoint.get('direction', 'Не указано')}\n\n"
            
        return result
    else:
        return "По вашему запросу не найдено API эндпоинтов. Попробуйте уточнить запрос или использовать другие ключевые слова."


def analyze_file_alert(file_path: str = None) -> str:
    """
    Анализ алерта из файла one_line_alert.txt или указанного пути.
    Читает содержимое файла и анализирует его.
    """
    try:
        tool_logger.info("Вызов функции analyze_file_alert")
        
        # Если путь не указан, используем файл по умолчанию
        if not file_path:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            file_path = os.path.join(root_dir, 'TestAlerts/one_line_alert.txt')
            tool_logger.info(f"Используем путь по умолчанию: {file_path}")
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            error_msg = f"Файл не найден: {file_path}"
            tool_logger.error(error_msg)
            return error_msg
        
        # Читаем содержимое файла
        tool_logger.info(f"Чтение файла: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                alert_text = f.read()
        except UnicodeDecodeError:
            # Если возникла ошибка чтения в UTF-8, пробуем альтернативную кодировку
            with open(file_path, 'r', encoding='cp1251') as f:
                alert_text = f.read()
        
        tool_logger.info(f"Прочитано {len(alert_text)} символов из файла")
        
        # Используем более точный паттерн для разделения алертов
        # Ищем строки, которые начинаются с ПРОМ, PROM или DEV, затем |
        alert_starts = re.finditer(r'(?:^|\n)(?:ПРОМ|PROM|DEV) \|', alert_text)
        alert_positions = [match.start() for match in alert_starts]
        
        # Если не найдено ни одного алерта с префиксом, проверяем альтернативные паттерны
        if not alert_positions:
            # Альтернативный паттерн - ищем строки, начинающиеся с "АС Рефлекс"
            alt_alert_starts = re.finditer(r'(?:^|\n)АС Рефлекс', alert_text)
            alert_positions = [match.start() for match in alt_alert_starts]
            
            # Если все еще нет совпадений, просто анализируем весь текст как один алерт
            if not alert_positions:
                tool_logger.info("Не найдены стандартные паттерны алертов, анализируем весь текст как один алерт")
                return analyze_single_alert(alert_text, include_bot_analysis=True)
        
        # Разделяем текст на отдельные алерты
        alerts = []
        for i in range(len(alert_positions)):
            start = alert_positions[i]
            # Если это последний алерт, берем текст до конца файла
            end = alert_positions[i+1] if i < len(alert_positions) - 1 else len(alert_text)
            alert_content = alert_text[start:end].strip()
            alerts.append(alert_content)
        
        tool_logger.info(f"Найдено {len(alerts)} алертов в файле")
        
        # Анализируем каждый алерт отдельно
        results = []
        open_count = 0
        resolved_count = 0
        unknown_count = 0
        
        for i, alert in enumerate(alerts, 1):
            tool_logger.info(f"Анализ алерта #{i}")
            
            # Определяем статус алерта
            status = "UNKNOWN"
            if re.search(r'(?:OPEN|ACTIVE)', alert, re.IGNORECASE):
                status = "OPEN"
                open_count += 1
            elif re.search(r'(?:RESOLVED|CLOSED)', alert, re.IGNORECASE):
                status = "RESOLVED"
                resolved_count += 1
            else:
                unknown_count += 1
            
            # Выполняем расширенный анализ для первых 2 алертов, для остальных - базовый анализ
            if i <= 2:
                result = analyze_single_alert(alert, include_bot_analysis=True)
            else:
                result = analyze_single_alert(alert, include_bot_analysis=False)
            
            results.append(f"### Алерт #{i}\n\n{result}")
        
        # Формируем общую сводку по алертам
        summary = f"# 📊 Сводка по алертам в файле `{os.path.basename(file_path)}`\n\n"
        summary += f"| **Статистика** | **Значение** |\n"
        summary += f"|:---------:|:----------:|\n"
        summary += f"| **Всего алертов** | {len(alerts)} |\n"
        summary += f"| **Активных** 🔴 | {open_count} |\n"
        summary += f"| **Решенных** 🟢 | {resolved_count} |\n"
        summary += f"| **Неизвестных** ⚪ | {unknown_count} |\n\n"
        
        if open_count > 0:
            summary += f"⚠️ **Внимание:** В файле обнаружено {open_count} активных алертов, требующих внимания.\n\n"
            
        if resolved_count > 0:
            summary += f"✅ **Информация:** {resolved_count} алертов уже разрешены и не требуют действий.\n\n"
        
        # Добавляем общие рекомендации на основе анализа алертов
        summary += add_general_recommendations(open_count, resolved_count, unknown_count)
        
        # Объединяем результаты для формирования финального отчета
        combined_result = f"{summary}\n## Детальный анализ алертов\n\n" + "\n\n".join(results)
        
        tool_logger.info(f"Успешно завершен анализ {len(alerts)} алертов")
        
        return combined_result
            
    except Exception as e:
        error_message = f"Ошибка анализа файла: {str(e)}"
        tool_logger.error(error_message, exc_info=True)
        return f"⚠️ **Ошибка анализа файла:** {str(e)}"


def add_general_recommendations(open_count, resolved_count, unknown_count):
    """
    Добавляет общие рекомендации на основе анализа алертов
    
    Args:
        open_count: Количество открытых алертов
        resolved_count: Количество решенных алертов
        unknown_count: Количество алертов с неизвестным статусом
        
    Returns:
        str: Строка с общими рекомендациями
    """
    recommendations = "## 📋 Общие рекомендации\n\n"
    
    if open_count > 0:
        recommendations += "### 🔴 По активным алертам\n\n"
        recommendations += "1. **Приоритизация:** Сначала обработайте алерты с высоким уровнем приоритета (ERROR, AVAILABILITY)\n"
        recommendations += "2. **Группировка:** Проверьте, могут ли несколько алертов быть связаны с одной первопричиной\n"
        recommendations += "3. **Мониторинг:** Продолжайте отслеживать метрики после устранения проблемы\n\n"
    
    if resolved_count > 0:
        recommendations += "### 🟢 По решенным алертам\n\n"
        recommendations += "1. **Анализ:** Изучите историю решенных алертов для выявления повторяющихся проблем\n"
        recommendations += "2. **Документирование:** Запишите предпринятые действия для решения проблем\n"
        recommendations += "3. **Превентивные меры:** Разработайте меры для предотвращения повторения проблем\n\n"
    
    if unknown_count > 0:
        recommendations += "### ⚪ По алертам с неизвестным статусом\n\n"
        recommendations += "1. **Проверка:** Уточните статус этих алертов в системе мониторинга\n"
        recommendations += "2. **Классификация:** Определите приоритет и тип этих алертов\n"
        recommendations += "3. **Обновление:** Обновите информацию о статусе в системе\n\n"
    
    # Общие рекомендации для любого количества алертов
    recommendations += "### 🔧 Общие действия\n\n"
    recommendations += "1. **Регулярно проверяйте** системы мониторинга на наличие новых алертов\n"
    recommendations += "2. **Настройте оповещения** для критических систем и сервисов\n"
    recommendations += "3. **Документируйте** все предпринятые действия по устранению проблем\n"
    recommendations += "4. **Анализируйте тренды** по возникновению алертов для выявления системных проблем\n\n"
    
    return recommendations


def analyze_single_alert(alert_text, include_bot_analysis=True):
    """
    Анализ отдельного алерта.
    Извлекает детали алерта и генерирует структурированный вывод.
    """
    tool_logger.info("Анализ одиночного алерта")
    
    try:
        # Извлечение деталей алерта с использованием функций из alert_parser
        http_code_match = re.search(r'HTTP (?:ERROR )?(\d{3})|(\d{3}) POST', alert_text, re.IGNORECASE)
        http_code = http_code_match.group(1) if http_code_match and http_code_match.group(1) else http_code_match.group(2) if http_code_match else "Неизвестно"
        
        # Извлекаем детали о сервисе и типе алерта, используя функции из alert_parser
        from Source.alert_parser import extract_service_name
        service = extract_service_name(alert_text)
        
        # Извлекаем тип алерта и проверяем содержит ли он в себе информацию о статусе
        alert_type_match = re.search(r'\| ([^|]+) \|', alert_text)
        alert_type = alert_type_match.group(1).strip() if alert_type_match else "Неизвестный тип"
        
        # Извлекаем информацию о времени из алерта - упрощенный вариант
        timestamp_match = re.search(r'(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2})', alert_text)
        if not timestamp_match:
            # Проверяем другие форматы, как в функции extract_alert_details
            time_patterns = [
                # Format: 20:14 (MSK) 21.04.2025
                r'Problem detected at:\s*(\d{1,2}:\d{2}\s*\([A-Z]+\)\s*\d{1,2}\.\d{1,2}\.\d{4})',
                # Format: 10:15 AM 25.04.2023
                r'Problem detected at:\s*(\d{1,2}:\d{2}\s*(?:AM|PM)\s*\d{1,2}\.\d{1,2}\.\d{4})',
                # Format with dash: 21.04.2025 - 15:30
                r'Problem detected at:\s*(\d{1,2}\.\d{1,2}\.\d{4}\s*-\s*\d{1,2}:\d{2})',
                # Format with date first: 21.04.2025 15:30 (with or without timezone)
                r'Problem detected at:\s*(\d{1,2}\.\d{1,2}\.\d{4}\s+\d{1,2}:\d{2}(?:\s*\([A-Z]+\))?)',
                # General format with any timezone
                r'Problem detected at:\s*(\d{1,2}:\d{2}(?:\s*\([A-Z]+\))?\s*\d{1,2}\.\d{1,2}\.\d{4})'
            ]
            
            for pattern in time_patterns:
                timestamp_match = re.search(pattern, alert_text, re.IGNORECASE)
                if timestamp_match:
                    break
                    
        timestamp = timestamp_match.group(1) if timestamp_match else "Время не указано"
        
        # Определение статуса алерта
        status = "UNKNOWN"
        if re.search(r'(?:OPEN|ACTIVE)', alert_text, re.IGNORECASE):
            status = "OPEN"
        elif re.search(r'(?:RESOLVED|CLOSED)', alert_text, re.IGNORECASE):
            status = "RESOLVED"
        
        # Извлекаем ID алерта
        alert_id_match = re.search(r'P-(\d+)', alert_text)
        alert_id = alert_id_match.group(1) if alert_id_match else "Unknown"
        
        # Извлечение дополнительной информации об алерте используя функцию из alert_parser
        additional_info = extract_additional_alert_info(alert_text)
        
        # Улучшенные цветовые индикаторы и статус-метки в зависимости от статуса
        status_info = {
            "OPEN": {
                "icon": "🔴",
                "badge": "🚨 ОТКРЫТ",
                "color": "**",
                "border": "---"
            },
            "ACTIVE": {
                "icon": "🔴",
                "badge": "⚡ АКТИВЕН",
                "color": "**",
                "border": "---"
            },
            "RESOLVED": {
                "icon": "🟢",
                "badge": "✅ РЕШЕН",
                "color": "**",
                "border": "---"
            },
            "CLOSED": {
                "icon": "🟢",
                "badge": "✅ ЗАКРЫТ",
                "color": "**",
                "border": "---"
            },
            "UNKNOWN": {
                "icon": "⚪",
                "badge": "❓ НЕИЗВЕСТЕН",
                "color": "**",
                "border": "---"
            }
        }
        
        status_data = status_info.get(status, status_info["UNKNOWN"])
        
        # Определяем HTTP код и его значение (расширенная версия)
        http_code_info = {
            "200": {"icon": "✅", "text": "OK", "description": "Запрос успешно выполнен"},
            "201": {"icon": "✅", "text": "Created", "description": "Ресурс успешно создан"},
            "204": {"icon": "✅", "text": "No Content", "description": "Запрос выполнен, но нет данных для возврата"},
            "400": {"icon": "⚠️", "text": "Bad Request", "description": "Некорректный запрос, обычно из-за неправильного формата данных"},
            "401": {"icon": "🔒", "text": "Unauthorized", "description": "Отсутствует или неверная аутентификация"},
            "403": {"icon": "🚫", "text": "Forbidden", "description": "Доступ запрещен несмотря на успешную аутентификацию"},
            "404": {"icon": "🔍", "text": "Not Found", "description": "Запрашиваемый ресурс не найден"},
            "405": {"icon": "⛔", "text": "Method Not Allowed", "description": "Метод запроса не разрешен для данного ресурса"},
            "408": {"icon": "⏱️", "text": "Request Timeout", "description": "Сервер не дождался полного запроса от клиента"},
            "429": {"icon": "🔄", "text": "Too Many Requests", "description": "Слишком много запросов, превышен лимит"},
            "500": {"icon": "💥", "text": "Internal Server Error", "description": "Внутренняя ошибка сервера"},
            "501": {"icon": "🚧", "text": "Not Implemented", "description": "Сервер не поддерживает функциональность, необходимую для выполнения запроса"},
            "502": {"icon": "🔄", "text": "Bad Gateway", "description": "Ошибка шлюза или прокси при передаче запроса"},
            "503": {"icon": "🛑", "text": "Service Unavailable", "description": "Сервис временно недоступен из-за перегрузки или обслуживания"},
            "504": {"icon": "⏱️", "text": "Gateway Timeout", "description": "Шлюз или прокси не получил своевременный ответ от вышестоящего сервера"}
        }
        
        http_display = f"**{http_code}**"
        # Convert http_code to string to ensure it works as a dictionary key
        http_code_str = str(http_code)
        if http_code_str in http_code_info:
            http_icon = http_code_info[http_code_str]['icon']
            http_text = http_code_info[http_code_str]['text']
            http_desc = http_code_info[http_code_str]['description']
            http_display = f"{http_icon} **{http_code}** ({http_text})\n> *{http_desc}*"
        
        # Форматирование времени, если оно доступно
        time_display = "Не указано"
        if timestamp != "Время не указано":
            try:
                dt = datetime.strptime(timestamp, "%d.%m.%Y %H:%M:%S")
                time_display = f"{dt.strftime('%d.%m.%Y')} {dt.strftime('%H:%M:%S')}"
            except:
                time_display = timestamp
        
        # ВРЕМЕННОЕ ИЗМЕНЕНИЕ: Компактный вывод информации об алерте
        alert_info = f"# Алерт ID: {alert_id} - {status}\n\n"
        
        # Основные параметры в более компактном формате
        alert_info += f"**Сервис:** {service}\n"
        alert_info += f"**Тип:** {alert_type}\n"
        alert_info += f"**HTTP код:** {http_code}\n"
        alert_info += f"**Время:** {time_display}\n"
        
        # Добавляем только основную дополнительную информацию (без иконок)
        for key, value in additional_info.items():
            if value and key in ["Длительность", "Начало проблемы", "Окончание проблемы"]:
                alert_info += f"**{key}:** {value}\n"
        
        # Текст алерта
        alert_info += "\n**Исходный текст алерта:**\n"
        
        # Форматирование текста алерта для лучшей читаемости
        formatted_text = alert_text.replace("\n\n", "\n")
        if len(formatted_text) > 300:
            # Показываем только первые 300 символов с многоточием
            formatted_text = formatted_text[:300] + "...\n[Текст обрезан для краткости]"
        
        alert_info += f"```\n{formatted_text}\n```\n"
        
        # Если полный анализ с ботом не требуется, возвращаем только структурированную информацию
        if not include_bot_analysis:
            return alert_info
        
        # Создаем улучшенный промпт для бота с учетом статуса алерта и дополнительной информации
        bot_prompt = f"""
Статус алерта: {status}, 
Сервис: {service}, 
Тип: {alert_type},
HTTP код: {http_code}.
"""

        # Добавляем дополнительную информацию в промпт
        for key, value in additional_info.items():
            if value:
                bot_prompt += f"{key}: {value},\n"

        bot_prompt += "\nПроведи детальный анализ алерта и предложи рекомендации:\n"
        bot_prompt += "1. Объясни суть проблемы простым языком\n"
        bot_prompt += "2. Определи возможные причины проблемы\n"
        bot_prompt += "3. Предложи конкретные шаги для решения\n"
        bot_prompt += "4. Дай рекомендации по предотвращению подобных проблем в будущем\n"
        
        # Получаем ответ от бота
        tool_logger.info(f"Запрашиваем детальный анализ у бота для алерта со статусом {status}")
        
        # Создаем структурированные данные для анализа (расширенная версия)
        structured_data = {
            'status': status,
            'service': service,
            'alert_type': alert_type,
            'http_code': http_code if http_code != "Неизвестно" else None,
            'timestamp': timestamp if timestamp != "Время не указано" else None
        }
        
        # Добавляем дополнительную информацию в структурированные данные
        structured_data.update(additional_info)
        
        # Безопасный импорт get_bot_response
        try:
            from Source.agent import get_bot_response
        except ImportError as e:
            tool_logger.error(f"Не удалось импортировать get_bot_response: {str(e)}")
            get_bot_response = fallback_bot_response
            
        # Передаем структурированные данные в get_bot_response с увеличенным количеством токенов
        bot_response = get_bot_response(bot_prompt, max_tokens=800, alert_data=structured_data)
        
        # ВРЕМЕННОЕ ИЗМЕНЕНИЕ: Возвращаем только основную информацию об алерте
        # без детального анализа, рекомендаций и дополнительной информации
        return alert_info
        
    except Exception as e:
        error_message = f"Ошибка при анализе алерта: {str(e)}"
        tool_logger.error(error_message, exc_info=True)
        return f"❌ **Ошибка анализа:** {str(e)}"


def get_related_alert_info(alert_data):
    """
    Получает дополнительную информацию по алерту на основе его данных.
    
    Args:
        alert_data: Словарь с данными алерта
        
    Returns:
        str: Строка с дополнительной информацией
    """
    result = ""
    
    # Добавляем информацию о HTTP кодах, если указан HTTP код
    if alert_data.get('http_code') and alert_data['http_code'] not in ["Неизвестно", None]:
        http_code = str(alert_data['http_code'])
        
        http_code_descriptions = {
            "4xx": "Клиентские ошибки обычно указывают на проблемы с запросом от клиента. "
                  "Возможно, требуется проверить формат данных, аутентификацию или права доступа.",
            "5xx": "Серверные ошибки указывают на внутренние проблемы сервера. "
                  "Требуется проверить логи сервера, статус сервисов и доступность ресурсов."
        }
        
        if http_code.startswith("4"):
            result += f"**🔍 Информация о клиентской ошибке (4xx):**\n\n"
            result += f"{http_code_descriptions['4xx']}\n\n"
        elif http_code.startswith("5"):
            result += f"**🔍 Информация о серверной ошибке (5xx):**\n\n"
            result += f"{http_code_descriptions['5xx']}\n\n"
    
    # Добавляем информацию о Kubernetes, если это связано с Kubernetes
    if "Kubernetes" in alert_data.get("alert_type", "") or alert_data.get("Kubernetes Workload"):
        result += f"**☸️ Информация о Kubernetes:**\n\n"
        result += f"- Проверьте состояние подов: `kubectl get pods`\n"
        result += f"- Просмотрите логи: `kubectl logs <pod-name>`\n"
        result += f"- Проверьте события: `kubectl get events`\n\n"
    
    # Добавляем рекомендации по мониторингу на основе типа алерта
    if alert_data.get("alert_type"):
        if "AVAILABILITY" in alert_data["alert_type"]:
            result += f"**📊 Рекомендации по мониторингу доступности:**\n\n"
            result += f"- Проверьте метрики доступности сервиса\n"
            result += f"- Мониторьте время отклика и процент успешных запросов\n"
            result += f"- Настройте оповещения при падении доступности ниже 99.9%\n\n"
        elif "ERROR" in alert_data["alert_type"]:
            result += f"**⚠️ Рекомендации по работе с ошибками:**\n\n"
            result += f"- Анализируйте логи на предмет частых ошибок\n"
            result += f"- Отслеживайте количество ошибок в единицу времени\n"
            result += f"- Настройте группировку однотипных ошибок для облегчения анализа\n\n"
    
    return result


# Создаем инструмент на основе функции get_data_alert
get_data_alert_tool = Tool(
    name="Data Alert Parser",
    func=get_data_alert,
    description="Получаю текст алерта и возвращаю разбор данных."
)

# Создаем инструмент для поиска информации об API эндпоинтах
find_endpoint_info_tool = Tool(
    name="API Endpoint Info",
    func=find_endpoint_info,
    description="Ищу информацию об API эндпоинтах по запросу пользователя."
)

# Создаем инструмент для анализа алерта из файла
analyze_file_alert_tool = Tool(
    name="File Alert Analyzer",
    func=analyze_file_alert,
    description="Анализирую алерт из файла one_line_alert.txt и предоставляю результаты анализа."
)

# Создаем инструмент для проверки токена GigaChat
def check_gigachat_token_status(input_text: str = "") -> str:
    """
    Проверяет состояние токена GigaChat и возвращает информацию о количестве оставшихся токенов.
    
    Args:
        input_text: Любой текстовый ввод (игнорируется)
        
    Returns:
        str: Информация о состоянии токена и оставшихся токенах
    """
    try:
        tool_logger.info("Проверка состояния токена GigaChat")
        
        # Отключаем предупреждения о небезопасных запросах
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Импортируем модель GigaChat
        from langchain_gigachat.chat_models import GigaChat
        from langchain_core.messages import HumanMessage
        import requests
        import json
        import base64
        
        # Получаем креды из модели agent.py
        try:
            from Source.agent import model as gigachat_model
            credentials = gigachat_model.credentials
            scope = gigachat_model.scope
        except ImportError:
            tool_logger.error("Не удалось импортировать модель GigaChat из agent.py")
            return "❌ Ошибка: Не удалось получить данные о токене из настроек приложения"
        
        # Базовый URL для API GigaChat
        base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        
        # Поскольку credentials может быть в формате Base64, мы попробуем его декодировать
        try:
            # Пробуем декодировать base64 и получить client_id:client_secret
            decoded_credentials = base64.b64decode(credentials).decode('utf-8')
            if ':' in decoded_credentials:
                client_id, client_secret = decoded_credentials.split(':', 1)
            else:
                # Если не удалось найти разделитель, используем исходные креды
                client_id = credentials
                client_secret = ""
        except Exception as e:
            tool_logger.warning(f"Не удалось декодировать учетные данные: {str(e)}")
            # Пробуем разделить исходные креды, если они в формате id:secret
            if ':' in credentials:
                client_id, client_secret = credentials.split(':', 1)
            else:
                # Если не удалось найти разделитель, используем исходные креды в качестве ID
                client_id = credentials
                client_secret = ""
        
        # Получаем токен авторизации
        auth_url = f"{base_url}/oauth/token"
        auth_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": "e1895bdc-de6f-46f0-89f6-65df5ed71b61"
        }
        auth_data = {
            "scope": scope,
            "grant_type": "client_credentials"
        }
        
        tool_logger.info(f"Выполняем запрос к {auth_url}")
        try:
            # Проверяем модель авторизации
            if hasattr(gigachat_model, 'auth_url') and gigachat_model.auth_url:
                tool_logger.info(f"Используем кастомный URL авторизации: {gigachat_model.auth_url}")
                auth_url = gigachat_model.auth_url
                
            # Выполняем запрос на авторизацию
            auth_response = requests.post(
                auth_url,
                headers=auth_headers,
                data=auth_data,
                auth=(client_id, client_secret) if client_secret else None,
                timeout=10,
                verify=False  # Отключаем проверку SSL сертификата
            )
        except Exception as e:
            tool_logger.error(f"Ошибка при запросе авторизации: {str(e)}")
            return f"❌ Ошибка запроса авторизации: {str(e)}"
        
        if auth_response.status_code != 200:
            tool_logger.error(f"Ошибка аутентификации: {auth_response.status_code}, {auth_response.text}")
            return f"❌ Ошибка аутентификации: {auth_response.status_code}\n\nТекст ошибки: {auth_response.text}"
        
        token_data = auth_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            tool_logger.error("Токен доступа не найден в ответе")
            return "❌ Ошибка: Токен доступа не найден в ответе"
        
        # Получаем информацию о лимитах токенов
        info_url = f"{base_url}/accounts/info"
        info_headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        try:
            info_response = requests.get(info_url, headers=info_headers, timeout=10, verify=False)  # Отключаем проверку SSL сертификата
        except Exception as e:
            tool_logger.error(f"Ошибка при запросе информации: {str(e)}")
            return f"❌ Ошибка запроса информации: {str(e)}"
        
        if info_response.status_code != 200:
            tool_logger.error(f"Ошибка получения информации: {info_response.status_code}, {info_response.text}")
            return f"❌ Ошибка получения информации о токенах: {info_response.status_code}\n\nТекст ошибки: {info_response.text}"
        
        try:
            account_info = info_response.json()
        except Exception as e:
            tool_logger.error(f"Ошибка при разборе JSON ответа: {str(e)}")
            return f"❌ Ошибка при разборе ответа: {str(e)}"
        
        # Формируем информацию о токене и лимитах
        result = f"## 🔑 Информация о токене GigaChat\n\n"
        
        # Выводим информацию о токене
        if token_data.get("expires_in"):
            expires_in = token_data.get("expires_in")
            result += f"**Токен действителен:** {expires_in} секунд\n\n"
        
        # Выводим информацию о лимитах
        if "limits" in account_info and account_info["limits"]:
            limits = account_info["limits"]
            result += "### Текущие лимиты:\n\n"
            result += "| 📊 Тип | ✅ Использовано | 🔄 Лимит | 💯 Осталось |\n"
            result += "|:------|:--------------|:--------|:-----------|\n"
            
            for limit in limits:
                limit_type = limit.get("intervalType", "Неизвестно")
                current_usage = limit.get("currentUsage", 0)
                max_limit = limit.get("maxLimit", 0)
                remaining = max_limit - current_usage if max_limit > current_usage else 0
                percent = round((current_usage / max_limit) * 100, 2) if max_limit > 0 else 0
                
                result += f"| **{limit_type}** | {current_usage} | {max_limit} | {remaining} ({percent}%) |\n"
        else:
            result += "❓ Информация о лимитах недоступна\n\n"
        
        # Добавляем информацию о статусе токена
        if "status" in account_info:
            status = account_info["status"]
            result += f"\n### Статус аккаунта: **{status}**\n\n"
        
        # Дополнительная информация о токене
        result += "\n### Информация об использовании:\n\n"
        result += "- Используйте токены экономно, распределяя их равномерно\n"
        result += "- При приближении к лимиту, система может начать отклонять запросы\n"
        result += "- Рекомендуется обновлять токен при необходимости\n"
        
        # Выводим всю полученную информацию для отладки
        tool_logger.debug(f"Полученная информация о токене: {json.dumps(account_info, indent=2)}")
        
        return result
        
    except Exception as e:
        error_message = f"Ошибка при проверке токена: {str(e)}"
        tool_logger.error(error_message, exc_info=True)
        return f"❌ **Ошибка при проверке токена GigaChat:** {str(e)}"

# Создаем инструмент для проверки токена GigaChat
check_gigachat_token_status_tool = Tool(
    name="GigaChat Token Status",
    func=check_gigachat_token_status,
    description="Проверяю состояние токена GigaChat и информацию о лимитах токенов."
)

# Инструменты для экспорта
get_data_alert = get_data_alert_tool
find_endpoint_info = find_endpoint_info_tool
analyze_file_alert = analyze_file_alert_tool
check_token_status = check_gigachat_token_status_tool

# Функция для тестирования нашего инструмента
if __name__ == "__main__":
    # Читаем алерт из файла вместо использования захардкоженного текста
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    alert_file_path = os.path.join(root_dir, 'TestAlerts/one_line_alert.txt')
    
    try:
        if os.path.exists(alert_file_path):
            with open(alert_file_path, 'r', encoding='utf-8') as f:
                alert_text = f.read()
                print(f"Прочитан алерт из файла {alert_file_path}, длина: {len(alert_text)} символов")
        else:
            print(f"Файл не найден: {alert_file_path}")
            print("Используем резервный вариант алерта для тестирования")

            
            # Создадим директорию и файл для будущих запусков
            os.makedirs(os.path.dirname(alert_file_path), exist_ok=True)
            with open(alert_file_path, 'w', encoding='utf-8') as f:
                f.write(alert_text)
                print(f"Создан тестовый файл алерта: {alert_file_path}")
                
    except Exception as e:
        print(f"Ошибка при чтении файла: {str(e)}")

    
    # Вызов инструмента
    try:
        print("\nТестирование инструмента get_data_alert:")
        result = get_data_alert.invoke(alert_text)
        print(result)
    except Exception as e:
        print(f"Ошибка при вызове get_data_alert: {str(e)}")
    
    # Тестирование анализа файла
    try:
        print("\nТестирование функции analyze_file_alert:")
        file_result = analyze_file_alert()
        print("\nАнализ файла:")
        print(file_result)
    except Exception as e:
        print(f"Ошибка при вызове analyze_file_alert: {str(e)}")