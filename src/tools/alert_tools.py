"""
Модуль для анализа алертов и обработки уведомлений о проблемах.
Содержит инструменты для разбора и анализа алертов из разных источников.
"""
import re
import os
from langchain.tools import Tool
from datetime import datetime, timedelta
# Импортируем функции парсинга алертов из нового модуля
from src.alert_processing.alert_parser import (
    parse_alert,
    get_data_alert as parse_get_data_alert,
    extract_additional_alert_info,
    get_icon_for_key,
    extract_service_name
)
from .logging_utils import tool_logger

# Функция-заглушка на случай, если импорт get_bot_response не удастся
def fallback_bot_response(prompt, max_tokens=1000, alert_data=None):
    """
    Резервная функция для генерации ответа, когда основная модель недоступна.
    
    Args:
        prompt: Текст запроса
        max_tokens: Максимальное количество токенов
        alert_data: Данные алерта (опционально)
        
    Returns:
        str: Сообщение об ошибке
    """
    import traceback
    error_info = traceback.format_exc()
    tool_logger.error(f"Использование заглушки fallback_bot_response. Запрос: {prompt[:50]}...")
    tool_logger.error(f"Стек вызовов:\n{error_info}")
    
    return f"""Извините, не удалось получить ответ от AI-ассистента из-за технической проблемы:
1. Произошла ошибка при импорте функции get_bot_response
2. Вместо полного анализа используется резервный ответ
3. Возможное решение: проверьте доступность API GigaChat и настройки импорта

Пожалуйста, сообщите об этой проблеме разработчикам.
"""

# Функция get_data_alert теперь является оберткой для функции из alert_parser
def get_data_alert(alert_text: str) -> dict:
    """
    Получив текст алерта, разбирает его на части, сообщает когда был алерт,
    на каком сервисе, какая ошибка и интерпретирует код HTTP ошибки,
    указывает на каких проектах OpenShift возникло отклонение и указывает период,
    за который следует проверить логи.
    
    Args:
        alert_text: Текст алерта для анализа
        
    Returns:
        dict: Структурированные данные алерта
    """
    # Используем функцию из модуля alert_parser
    return parse_get_data_alert(alert_text)

def analyze_file_alert(file_path: str = None, alert_number: int = None) -> str:
    """
    Анализ алерта из указанного файла или файла по умолчанию.
    Читает содержимое файла и анализирует его.
    
    Args:
        file_path: Путь к файлу с алертом (опционально)
        alert_number: Номер алерта для анализа в файле с несколькими алертами (опционально)
        
    Returns:
        str: Результат анализа алерта
    """
    try:
        tool_logger.info(f"Вызов функции analyze_file_alert c параметрами: file_path={file_path}, alert_number={alert_number}")
        
        # Если путь не указан, используем файл по умолчанию
        if not file_path:
            # Импортируем функцию для получения пути к файлу алерта
            try:
                from src.config.settings import get_alert_file_path
                file_path = get_alert_file_path()
                tool_logger.info(f"Получен путь к файлу алерта по умолчанию: {file_path}")
            except ImportError:
                # Если не удалось импортировать, используем прямой путь
                root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                test_alerts_dir = os.path.join(root_dir, 'tests', 'fixtures')
                
                # Пробуем найти любой .txt файл в директории с тестовыми алертами
                try:
                    for filename in os.listdir(test_alerts_dir):
                        if filename.endswith('.txt'):
                            file_path = os.path.join(test_alerts_dir, filename)
                            tool_logger.info(f"Используем первый найденный файл алерта: {file_path}")
                            break
                    else:
                        default_file = os.path.join(test_alerts_dir, 'multiple_alerts.txt')
                        tool_logger.warning(f"Не найдены файлы алертов, используем путь по умолчанию: {default_file}")
                        file_path = default_file
                except Exception as e:
                    tool_logger.error(f"Ошибка при поиске файлов алертов: {str(e)}")
                    default_file = os.path.join(test_alerts_dir, 'multiple_alerts.txt')
                    file_path = default_file
        
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
        
        # Проверяем, запрашивается ли конкретный алерт
        if alert_number is not None:
            tool_logger.info(f"Запрошен конкретный алерт с номером {alert_number}")
            
            # Проверяем, существует ли запрошенный алерт
            if alert_number <= 0 or alert_number > len(alerts):
                error_msg = f"В файле содержится {len(alerts)} алертов. Нет алерта с номером {alert_number}."
                tool_logger.error(error_msg)
                return error_msg
                
            # Анализируем только запрошенный алерт
            specific_alert = alerts[alert_number - 1]
            result = f"## Алерт #{alert_number}\n\n"
            analysis = analyze_single_alert(specific_alert, include_bot_analysis=True)
            result += analysis
            
            tool_logger.info(f"Успешно проанализирован алерт #{alert_number}")
            return result
        
        # Анализируем каждый алерт отдельно
        results = []
        open_count = 0
        resolved_count = 0
        unknown_count = 0
        
        for i, alert in enumerate(alerts, 1):
            try:
                # Извлекаем статус алерта из текста
                status_match = re.search(r'(?:OPEN|RESOLVED|ACTIVE)', alert, re.IGNORECASE)
                status = status_match.group().upper() if status_match else "UNKNOWN"
                
                if status == "OPEN" or status == "ACTIVE":
                    open_count += 1
                elif status == "RESOLVED":
                    resolved_count += 1
                else:
                    unknown_count += 1
                
                # Для каждого алерта добавляем информацию в результаты
                result = f"### Алерт {i}: {status}\n\n"
                analysis = analyze_single_alert(alert, include_bot_analysis=False)
                result += analysis
                results.append(result)
                
            except Exception as e:
                error_msg = f"Ошибка при анализе алерта {i}: {str(e)}"
                tool_logger.error(error_msg, exc_info=True)
                results.append(f"### Алерт {i}: Ошибка анализа\n\n⚠️ {error_msg}")
        
        # Формируем общую сводку по алертам
        summary = f"# 📊 Сводка по алертам\n\n"
        summary += f"Проанализировано алертов: **{len(alerts)}**\n\n"
        
        if open_count > 0:
            summary += f"⚠️ **Внимание:** {open_count} алертов требуют вашего внимания.\n\n"
            
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
        recommendations += "### ⚠️ По алертам с неизвестным статусом\n\n"
        recommendations += "1. **Уточнение:** Уточните статус алертов и их актуальность\n"
        recommendations += "2. **Проверка источника:** Проверьте корректность работы системы мониторинга\n\n"
    
    return recommendations

def analyze_single_alert(alert_text, include_bot_analysis=True):
    """
    Анализ отдельного алерта.
    Извлекает детали алерта и генерирует структурированный вывод.
    
    Args:
        alert_text: Текст алерта для анализа
        include_bot_analysis: Включать ли анализ с помощью бота
        
    Returns:
        str: Результат анализа алерта
    """
    tool_logger.info("Анализ одиночного алерта")
    
    try:
        # Извлечение деталей алерта с использованием функций из alert_parser
        http_code_match = re.search(r'HTTP (?:ERROR )?(\d{3})|(\d{3}) POST', alert_text, re.IGNORECASE)
        http_code = http_code_match.group(1) if http_code_match and http_code_match.group(1) else http_code_match.group(2) if http_code_match else "Неизвестно"
        
        # Извлекаем детали о сервисе и типе алерта
        service = extract_service_name(alert_text)
        
        # Извлекаем тип алерта и проверяем содержит ли он в себе информацию о статусе
        alert_type_match = re.search(r'\| ([^|]+) \|', alert_text)
        alert_type = alert_type_match.group(1).strip() if alert_type_match else "Неизвестный тип"
        
        # Извлекаем информацию о времени из алерта - упрощенный вариант
        timestamp_match = re.search(r'(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2})', alert_text)
        if not timestamp_match:
            timestamp_match = re.search(r'(\d{2}:\d{2} \(\w+\) \d{2}\.\d{2}\.\d{4})', alert_text)
        
        timestamp = timestamp_match.group(1) if timestamp_match else "Время не указано"
        
        # Проверяем, содержится ли в тексте информация о HTTP ошибке
        if http_code != "Неизвестно":
            has_http_error = True
        else:
            has_http_error = False
        
        # Извлекаем информацию о запросе из алерта
        request_match = re.search(r'Request:\s*([^\n]+)', alert_text)
        request = request_match.group(1).strip() if request_match else "Не указан"
        
        # Извлекаем ID алерта
        alert_id_match = re.search(r'P-(\d+)', alert_text)
        alert_id = alert_id_match.group(0) if alert_id_match else "Не указан"
        
        # Создаем структурированный вывод
        structured_data = {
            "id": alert_id,
            "service": service,
            "http_code": http_code,
            "timestamp": timestamp,
            "alert_type": alert_type,
            "request": request,
            "has_http_error": has_http_error
        }
        
        # Добавляем информацию из alert_parser, если она доступна
        try:
            additional_info = extract_additional_alert_info(alert_text)
            for key, value in additional_info.items():
                if key not in structured_data or not structured_data[key]:
                    structured_data[key] = value
        except Exception as e:
            tool_logger.warning(f"Не удалось извлечь дополнительную информацию: {str(e)}")
        
        # Форматируем результат
        result = f"#### 📝 Основная информация\n\n"
        result += f"- **ID алерта:** {structured_data['id']}\n"
        result += f"- **Сервис:** {structured_data['service'] or 'Не указан'}\n"
        result += f"- **Тип алерта:** {structured_data['alert_type']}\n"
        result += f"- **Время:** {structured_data['timestamp']}\n"
        
        if has_http_error:
            result += f"- **HTTP код:** {structured_data['http_code']}\n"
            
            # Добавляем расшифровку HTTP кода
            if structured_data['http_code'].startswith('4'):
                result += f"  - **Описание:** Клиентская ошибка (проблема с запросом)\n"
            elif structured_data['http_code'].startswith('5'):
                result += f"  - **Описание:** Серверная ошибка (проблема на стороне сервера)\n"
        
        # Добавляем информацию о запросе, если она есть
        if request != "Не указан":
            result += f"- **Запрос:** `{request}`\n"
        
        # Добавляем дополнительные поля
        result += "\n#### 📊 Дополнительная информация\n\n"
        
        # Добавляем дополнительную информацию из полей алерта
        for key, value in structured_data.items():
            if key not in ["id", "service", "http_code", "timestamp", "alert_type", "request", "has_http_error"] and value:
                icon = get_icon_for_key(key)
                result += f"- **{icon} {key.capitalize()}:** {value}\n"
        
        # Анализируем HTTP ошибку более подробно
        if has_http_error:
            result += "\n#### 🔍 Анализ HTTP ошибки\n\n"
            if structured_data['http_code'].startswith('4'):
                result += "- Клиентская ошибка может указывать на проблемы с запросом:\n"
                result += "  - Проверьте параметры и формат запроса\n"
                result += "  - Проверьте аутентификацию и авторизацию\n"
                result += "  - Убедитесь, что запрашиваемый ресурс существует\n"
            elif structured_data['http_code'].startswith('5'):
                result += "- Серверная ошибка может указывать на проблемы с сервисом:\n"
                result += "  - Проверьте логи сервиса для выявления ошибок\n"
                result += "  - Проверьте доступность внешних зависимостей\n"
                result += "  - Проверьте ресурсы сервера (CPU, память, диск)\n"
        
        # Добавляем рекомендации по действиям
        result += "\n#### 🛠 Рекомендуемые действия\n\n"
        
        if structured_data.get("status", "").upper() == "RESOLVED":
            result += "✅ **Алерт уже разрешен.** Действий не требуется, но рекомендуется изучить причину проблемы для предотвращения ее повторения.\n"
        else:
            # Если есть HTTP ошибка, добавляем рекомендации по ее исправлению
            if has_http_error:
                if structured_data['http_code'].startswith('4'):
                    result += "1. Проверьте формат запроса и параметры\n"
                    result += "2. Проверьте аутентификацию и права доступа\n"
                elif structured_data['http_code'].startswith('5'):
                    result += "1. Проверьте состояние сервиса через системный мониторинг\n"
                    result += "2. Изучите логи сервиса на предмет ошибок\n"
            
            # Общие рекомендации для всех типов алертов
            result += "3. Проверьте доступность зависимых сервисов\n"
            result += "4. Если проблема в Kubernetes, выполните:\n"
            result += f"- Просмотрите логи: `kubectl logs <pod-name>`\n"
            result += f"- Проверьте события: `kubectl get events`\n\n"
        
        # Добавляем рекомендации по мониторингу на основе типа алерта
        if structured_data.get("alert_type"):
            if "AVAILABILITY" in structured_data["alert_type"]:
                result += f"**📊 Рекомендации по мониторингу доступности:**\n\n"
                result += f"- Проверьте метрики доступности сервиса\n"
                result += f"- Мониторьте время отклика и процент успешных запросов\n"
                result += f"- Настройте оповещения при падении доступности ниже 99.9%\n\n"
            elif "ERROR" in structured_data["alert_type"]:
                result += f"**⚠️ Рекомендации по работе с ошибками:**\n\n"
                result += f"- Анализируйте логи на предмет частых ошибок\n"
                result += f"- Отслеживайте количество ошибок в единицу времени\n"
                result += f"- Настройте группировку однотипных ошибок для облегчения анализа\n\n"
        
        # Добавляем анализ от бота, если это требуется
        if include_bot_analysis:
            try:
                from src.core.agent import get_bot_response
                result += "\n#### 🤖 Анализ от AI-ассистента\n\n"
                bot_prompt = f"Проанализируй следующий алерт и кратко опиши проблему, возможные причины и рекомендации по устранению:\n\n{alert_text}"
                bot_response = get_bot_response(bot_prompt, max_tokens=800, alert_data=structured_data)
                result += bot_response
            except ImportError:
                tool_logger.warning("Не удалось импортировать get_bot_response, используем заглушку")
                bot_response = fallback_bot_response(alert_text, alert_data=structured_data)
                result += bot_response
        
        return result
        
    except Exception as e:
        error_message = f"Ошибка при анализе алерта: {str(e)}"
        tool_logger.error(error_message, exc_info=True)
        return f"⚠️ **Ошибка анализа:** {str(e)}"

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
        
        # Добавляем рекомендации для конкретных HTTP кодов
        specific_recommendations = {
            "400": "Неверный запрос. Проверьте формат и содержимое запроса.",
            "401": "Неавторизованный доступ. Проверьте учетные данные аутентификации.",
            "403": "Доступ запрещен. Проверьте права доступа.",
            "404": "Ресурс не найден. Проверьте URL или маршруты API.",
            "408": "Тайм-аут запроса. Увеличьте время ожидания или проверьте производительность сервера.",
            "500": "Внутренняя ошибка сервера. Проверьте логи сервера для деталей.",
            "502": "Плохой шлюз. Проверьте прокси или балансировщик нагрузки.",
            "503": "Сервис недоступен. Проверьте состояние сервиса и его зависимостей.",
            "504": "Тайм-аут шлюза. Проверьте время выполнения запросов на бэкенде."
        }
        
        if http_code in specific_recommendations:
            result += f"**📌 Рекомендации для HTTP {http_code}:**\n\n"
            result += f"{specific_recommendations[http_code]}\n\n"
    
    # Добавляем рекомендации по Kubernetes, если есть признаки проблем с K8s
    if alert_data.get('service') and ('pod' in alert_data['service'].lower() or 'k8s' in alert_data['service'].lower() or 'kubernetes' in alert_data['service'].lower()):
        result += f"**☸️ Рекомендации по Kubernetes:**\n\n"
        result += f"- Проверьте состояние пода: `kubectl describe pod <pod-name> -n <namespace>`\n"
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

# Создаем инструмент для анализа алерта из файла
analyze_file_alert_tool = Tool(
    name="File Alert Analyzer",
    func=analyze_file_alert,
    description="Анализирую алерт из выбранного файла и предоставляю результаты анализа."
)

# Экспортируем инструменты и функции
get_data_alert = get_data_alert_tool
analyze_file_alert_tool = analyze_file_alert_tool  # Инструмент для использования через invoke
analyze_file_alert = analyze_file_alert  # Оригинальная функция для прямого вызова 