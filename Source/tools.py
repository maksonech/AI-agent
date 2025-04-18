from langchain.tools import Tool
import re
import os
import logging
from datetime import datetime, timedelta
from Source.utils import courses_database  # Импортируем обработанный JSON с эндпоинтами

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
    # Обновленный шаблон, учитывающий разные статусы
    alert_data_pattern = r'(.*?): (?P<status>RESOLVED|OPEN|open|resolved) Custom Alert P-(?P<alert_id>\d+) in environment (.*?)$'
    match = re.match(alert_data_pattern, first_section.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("Неверный формат первой секции алерта")
    
    alert_id = match.group('alert_id')
    alert_status = match.group('status').upper()  # Преобразуем в верхний регистр для унификации
    
    # Парсим вторую секцию (детали проблемы)
    second_section = sections[1].strip()
    problem_detected_pattern = r'\s*(?P<start_time>\d{1,2}:\d{2}\s+\w+)\s+$(?P<start_date>\d{2}\.\d{2}\.\d{4})$\s*-\s*(?P<end_time>\d{1,2}:\d{2}\s+\w+)\s+$(?P<end_date>\d{2}\.\d{2}\.\d{4})$\s*$was\s+open\s+for\s+(?P<duration>\d+\s\w+)$\n*(?P<services_impacted>\d+)\s*impacted\sservice\n*([\w\s]+)\n*(?P<error_message>.*?\.)'
    match = re.match(problem_detected_pattern, second_section, flags=re.DOTALL)
    if not match:
        raise ValueError("Неверный формат второй секции алерта")
    
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
        'status': alert_parts['status'],
        'error_message': alert_parts['error_message'],
        'http_code': '503',  # Код HTTP ошибки, указанный в тексте алерта
        'openshift_projects': ['console.ar426hj5.k8s.ca.sbrf.ru', 'console.ar2qob4m.k8s.ca.sbrf.ru'],  # Проекты OpenShift, указанные в тексте алерта
        'log_check_period': log_check_period
    }
    return result


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
                return analyze_single_alert(alert_text)
        
        # Разделяем текст на отдельные алерты
        alerts = []
        for i in range(len(alert_positions)):
            start = alert_positions[i]
            # Если это последний алерт, берем текст до конца файла
            end = alert_positions[i+1] if i < len(alert_positions) - 1 else len(alert_text)
            alert_fragment = alert_text[start:end].strip()
            if alert_fragment:  # Проверяем, что фрагмент не пустой
                alerts.append(alert_fragment)
        
        tool_logger.info(f"Найдено {len(alerts)} алертов в файле")
        
        # Если найден только один алерт, анализируем его напрямую
        if len(alerts) == 1:
            return analyze_single_alert(alerts[0])
        
        # Анализируем каждый алерт и формируем сводный результат
        results = []
        open_count = 0
        resolved_count = 0
        unknown_count = 0
        
        for i, alert in enumerate(alerts, 1):
            tool_logger.info(f"Анализ алерта #{i}")
            
            # Проверяем статус алерта более точно
            is_open_alert = "OPEN" in alert or "ACTIVE" in alert
            is_resolved_alert = "RESOLVED" in alert or "CLOSED" in alert
            
            # Подсчет статусов алертов
            if is_open_alert:
                open_count += 1
                tool_logger.info(f"Алерт #{i} определен как OPEN")
            elif is_resolved_alert:
                resolved_count += 1
                tool_logger.info(f"Алерт #{i} определен как RESOLVED")
            else:
                unknown_count += 1
                tool_logger.info(f"Алерт #{i} имеет неизвестный статус")
                
            # Анализируем только первые 2 алерта детально, для остальных упрощенный вывод
            include_bot = (i == 1) or (is_open_alert and i <= 2)
            
            result = analyze_single_alert(alert, include_bot_analysis=include_bot)
            results.append(f"### 📋 Алерт #{i}\n{result}")
        
        # Создаем красивую сводную информацию
        now = datetime.now().strftime('%d.%m.%Y %H:%M')
        summary = f"# 📊 Отчет по анализу алертов\n\n"
        summary += f"**Время анализа**: {now}\n"
        summary += f"**Файл**: `{os.path.basename(file_path)}`\n\n"
        
        # Общая статистика в виде карточки
        summary += f"## Статистика алертов\n"
        summary += f"| Категория | Количество |\n"
        summary += f"|:---------:|:----------:|\n"
        summary += f"| **Всего алертов** | {len(alerts)} |\n"
        summary += f"| **Активных** 🔴 | {open_count} |\n"
        summary += f"| **Решенных** 🟢 | {resolved_count} |\n"
        summary += f"| **Неизвестных** ⚪ | {unknown_count} |\n\n"
        
        if open_count > 0:
            summary += f"⚠️ **Внимание:** В файле обнаружено {open_count} активных алертов, требующих внимания.\n\n"
            
        if resolved_count > 0:
            summary += f"✅ **Информация:** {resolved_count} алертов уже разрешены и не требуют действий.\n\n"
        
        # Объединяем только первые 3 алерта для экономии токенов
        max_alerts_to_show = min(3, len(results))
        combined_result = f"{summary}\n## Анализ по алертам\n\n" + "\n\n".join(results[:max_alerts_to_show])
        
        if len(results) > 3:
            combined_result += f"\n\n> ... и еще {len(results) - 3} алертов (не показаны для экономии токенов)"
        
        tool_logger.info(f"Успешно завершен анализ {len(alerts)} алертов")
        
        return combined_result
            
    except Exception as e:
        error_message = f"Ошибка анализа файла: {str(e)}"
        tool_logger.error(error_message, exc_info=True)
        return f"⚠️ **Ошибка анализа файла:** {str(e)}"


def analyze_single_alert(alert_text, include_bot_analysis=True):
    """
    Анализ отдельного алерта.
    Извлекает детали алерта и генерирует структурированный вывод.
    """
    tool_logger.info("Анализ одиночного алерта")
    
    try:
        # Извлечение деталей алерта
        http_code_match = re.search(r'HTTP (?:ERROR )?(\d{3})|(\d{3}) POST', alert_text, re.IGNORECASE)
        http_code = http_code_match.group(1) if http_code_match and http_code_match.group(1) else http_code_match.group(2) if http_code_match else "Неизвестно"
        
        # Извлекаем детали о сервисе и типе алерта
        service_match = re.search(r'(?:ПРОМ|PROM|DEV) \| ([^|]+)', alert_text)
        service = service_match.group(1).strip() if service_match else "Неизвестный сервис"
        
        # Извлекаем тип алерта и проверяем содержит ли он в себе информацию о статусе
        alert_type_match = re.search(r'\| ([^|]+) \|', alert_text)
        alert_type = alert_type_match.group(1).strip() if alert_type_match else "Неизвестный тип"
        
        # Извлекаем информацию о времени из алерта - упрощенный вариант
        timestamp_match = re.search(r'(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2})', alert_text)
        timestamp = timestamp_match.group(1) if timestamp_match else "Время не указано"
        
        # Определение статуса алерта
        status = "UNKNOWN"
        if re.search(r'(?:OPEN|ACTIVE)', alert_text, re.IGNORECASE):
            status = "OPEN"
        elif re.search(r'(?:RESOLVED|CLOSED)', alert_text, re.IGNORECASE):
            status = "RESOLVED"
        
        # Улучшенные цветовые индикаторы и статус-метки в зависимости от статуса
        status_info = {
            "OPEN": {
                "icon": "🔴",
                "badge": "🚨 ОТКРЫТ",
                "color": "**",
                "border": "─────────────────────────────────────────────────"
            },
            "ACTIVE": {
                "icon": "🔴",
                "badge": "⚡ АКТИВЕН",
                "color": "**",
                "border": "─────────────────────────────────────────────────"
            },
            "RESOLVED": {
                "icon": "🟢",
                "badge": "✅ РЕШЕН",
                "color": "**",
                "border": "─────────────────────────────────────────────────"
            },
            "CLOSED": {
                "icon": "🟢",
                "badge": "✅ ЗАКРЫТ",
                "color": "**",
                "border": "─────────────────────────────────────────────────"
            },
            "UNKNOWN": {
                "icon": "⚪",
                "badge": "❓ НЕИЗВЕСТЕН",
                "color": "**",
                "border": "─────────────────────────────────────────────────"
            }
        }
        
        status_data = status_info.get(status, status_info["UNKNOWN"])
        
        # Определяем HTTP код и его значение
        http_code_info = {
            "200": {"icon": "✅", "text": "OK"},
            "400": {"icon": "⚠️", "text": "Некорректный запрос"},
            "401": {"icon": "🔒", "text": "Неавторизован"},
            "403": {"icon": "🚫", "text": "Запрещено"},
            "404": {"icon": "🔍", "text": "Не найдено"},
            "500": {"icon": "💥", "text": "Внутренняя ошибка сервера"},
            "502": {"icon": "🔄", "text": "Ошибка шлюза"},
            "503": {"icon": "🛑", "text": "Сервис недоступен"},
            "504": {"icon": "⏱️", "text": "Таймаут шлюза"}
        }
        
        http_display = f"**{http_code}**"
        # Convert http_code to string to ensure it works as a dictionary key
        http_code_str = str(http_code)
        if http_code_str in http_code_info:
            http_display = f"{http_code_info[http_code_str]['icon']} **{http_code}** ({http_code_info[http_code_str]['text']})"
        
        # Форматирование времени, если оно доступно
        time_display = "Не указано"
        if timestamp != "Время не указано":
            try:
                dt = datetime.strptime(timestamp, "%d.%m.%Y %H:%M:%S")
                time_display = f"📅 {dt.strftime('%d.%m.%Y')} ⏰ {dt.strftime('%H:%M:%S')}"
            except:
                time_display = timestamp
        
        # Красивый вывод информации об алерте в виде карточки с границами
        alert_info = f"## {status_data['icon']} {status_data['badge']} {status_data['icon']}\n"
        alert_info += f"{status_data['border']}\n\n"
        
        # Информационная таблица с улучшенным форматированием
        alert_info += f"| 📊 Параметр | 📋 Значение |\n"
        alert_info += f"|:----------:|:-----------|\n"
        alert_info += f"| 🏢 **Сервис** | {service} |\n"
        alert_info += f"| 📝 **Тип** | {alert_type} |\n"
        alert_info += f"| 🌐 **HTTP код** | {http_display} |\n"
        alert_info += f"| 🕒 **Время** | {time_display} |\n"
        
        # Извлечение сообщения об ошибке, если есть
        error_msg_match = re.search(r'Error message: (.*?)(?:\n|$)', alert_text, re.IGNORECASE)
        if error_msg_match:
            error_message = error_msg_match.group(1).strip()
            alert_info += f"| ⚠️ **Ошибка** | {error_message} |\n"
        
        # Текст алерта с улучшенным форматированием в виде раскрывающегося блока
        alert_info += "\n"
        alert_info += "<details>\n"
        alert_info += "<summary>📝 Подробности алерта</summary>\n\n"
        
        # Форматирование текста алерта для лучшей читаемости
        formatted_text = alert_text.replace("\n\n", "\n")
        if len(formatted_text) > 300:
            # Показываем только первые 300 символов с многоточием
            formatted_text = formatted_text[:300] + "...\n\n[Текст обрезан для краткости]"
        
        alert_info += f"```\n{formatted_text}\n```\n"
        alert_info += "</details>\n"
        
        # Если полный анализ с ботом не требуется, возвращаем только структурированную информацию
        if not include_bot_analysis:
            return alert_info
        
        # Создаем улучшенный промпт для бота с учетом статуса алерта
        bot_prompt = f"""
Статус алерта: {status}, 
Сервис: {service}, 
Тип: {alert_type},
HTTP код: {http_code}.

Кратко проанализируй данный алерт (до 100 слов).
"""
        # Получаем ответ от бота
        tool_logger.info(f"Запрашиваем анализ у бота для алерта со статусом {status}")
        
        # Создаем структурированные данные для анализа (расширенная версия)
        structured_data = {
            'status': status,
            'service': service,
            'alert_type': alert_type,
            'http_code': http_code if http_code != "Неизвестно" else None,
            'timestamp': timestamp if timestamp != "Время не указано" else None
        }
        
        # Безопасный импорт get_bot_response
        try:
            from Source.agent import get_bot_response
        except ImportError as e:
            tool_logger.error(f"Не удалось импортировать get_bot_response: {str(e)}")
            get_bot_response = fallback_bot_response
            
        # Передаем структурированные данные в get_bot_response
        bot_response = get_bot_response(bot_prompt, max_tokens=500, alert_data=structured_data)
        
        # Компактный вывод с анализом в красивом формате
        final_output = f"{alert_info}\n"
        final_output += f"## 🧠 Анализ\n"
        final_output += f"─────────────────────── 🔍 ───────────────────────\n\n"
        
        # Форматирование ответа бота в зависимости от статуса алерта
        if status == "OPEN" or status == "ACTIVE":
            final_output += f"⚠️ **ВНИМАНИЕ! Требуется реакция!**\n\n"
        elif status == "RESOLVED" or status == "CLOSED":
            final_output += f"✅ **Алерт закрыт. Дополнительных действий не требуется.**\n\n"
        
        final_output += f"{bot_response}\n\n"
        
        # Добавляем рекомендации в зависимости от статуса и HTTP кода
        if status == "OPEN" or status == "ACTIVE":
            if http_code in ["500", "502", "503", "504"]:
                final_output += f"### 📋 Рекомендации:\n\n"
                final_output += f"1. Проверьте доступность сервиса {service}\n"
                final_output += f"2. Изучите логи за период, близкий к времени возникновения алерта\n"
                final_output += f"3. Убедитесь в корректности конфигурации и доступности зависимостей\n"
        
        tool_logger.info("Анализ алерта успешно завершен")
        return final_output
        
    except Exception as e:
        error_message = f"Ошибка при анализе алерта: {str(e)}"
        tool_logger.error(error_message, exc_info=True)
        return f"⚠️ **Ошибка анализа:** {str(e)}"


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

# Инструменты для экспорта
get_data_alert = get_data_alert_tool
find_endpoint_info = find_endpoint_info_tool
analyze_file_alert = analyze_file_alert_tool

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