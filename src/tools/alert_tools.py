"""
Модуль для анализа алертов и обработки уведомлений о проблемах.
Содержит инструменты для разбора и анализа алертов из разных источников.
"""
# Добавляем код для корректной работы при прямом запуске
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import re
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, Pattern
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

# Константы для работы с алертами
ALERT_PATTERNS: Dict[str, Pattern] = {
    'standard': re.compile(r'(?:^|\n)(?:ПРОМ|PROM|DEV) \|'),
    'reflex': re.compile(r'(?:^|\n)АС Рефлекс')
}

MAX_TOKENS_FULL_ANALYSIS: int = 1000
MAX_TOKENS_BRIEF_ANALYSIS: int = 300

FULL_ANALYSIS_PROMPT_TEMPLATE: str = """Проанализируй следующий алерт:

```
{alert_text}
```

Пожалуйста, выполни детальный анализ этого алерта, извлеки из него всю важную информацию,
определи причину проблемы и предложи конкретные шаги для её решения."""

BRIEF_ANALYSIS_PROMPT_TEMPLATE: str = """Проанализируй следующий алерт:

```
{alert_text}
```

Дай ОЧЕНЬ КРАТКИЙ анализ (не более 5-6 предложений) этого алерта. 
Укажи только главную проблему, сервис и возможную причину."""

# Переменная для хранения модели, которая будет загружена позже
gigachat_model = None

# Функция-заглушка на случай, если импорт get_bot_response не удастся
def fallback_bot_response(prompt: str, max_tokens: int = 1000, alert_data: Optional[Dict[str, Any]] = None) -> str:
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

# Функция для отложенной загрузки модели
def get_gigachat_model():
    """
    Функция для отложенной загрузки модели GigaChat,
    чтобы избежать циклического импорта.
    
    Returns:
        Модель GigaChat или None, если не удалось импортировать
    """
    global gigachat_model
    if gigachat_model is None:
        try:
            # Импортируем модель только когда она нужна
            from src.core.agent import model as imported_model
            gigachat_model = imported_model
            tool_logger.info("Модель GigaChat успешно загружена")
        except ImportError as e:
            tool_logger.error(f"Не удалось импортировать модель GigaChat: {str(e)}")
    return gigachat_model

# Функция для отложенной загрузки get_bot_response
def get_ai_response_function() -> Callable:
    """
    Функция для отложенного импорта get_bot_response,
    чтобы избежать циклического импорта.
    
    Returns:
        Функция get_bot_response или fallback_bot_response в случае ошибки
    """
    try:
        # Импортируем функцию только когда она нужна
        from src.core.agent import get_bot_response
        return get_bot_response
    except ImportError as e:
        tool_logger.error(f"Не удалось импортировать get_bot_response: {str(e)}")
        return fallback_bot_response

# Функция get_data_alert теперь является оберткой для функции из alert_parser
def get_data_alert(alert_text: str) -> Dict[str, Any]:
    """
    Получив текст алерта, разбирает его на части, сообщает когда был алерт,
    на каком сервисе, какая ошибка и интерпретирует код HTTP ошибки,
    указывает на каких проектах OpenShift возникло отклонение и указывает период,
    за который следует проверить логи.
    
    Args:
        alert_text: Текст алерта для анализа
        
    Returns:
        Dict[str, Any]: Структурированные данные алерта
    """
    # Используем функцию из модуля alert_parser
    return parse_get_data_alert(alert_text)

def split_alerts_from_file(alert_file_content: str) -> List[str]:
    """
    Разделяет содержимое файла на отдельные алерты.
    
    Args:
        alert_file_content: Содержимое файла с алертами
        
    Returns:
        List[str]: Список алертов
    """
    # Пробуем стандартные паттерны для разделения алертов
    alert_positions = []
    
    # Проверяем каждый известный паттерн
    for pattern_name, pattern in ALERT_PATTERNS.items():
        alert_starts = pattern.finditer(alert_file_content)
        positions = [match.start() for match in alert_starts]
        
        if positions:
            tool_logger.info(f"Найдены алерты по паттерну '{pattern_name}': {len(positions)}")
            alert_positions = positions
            break
    
    # Если ни один паттерн не сработал, считаем весь файл одним алертом
    if not alert_positions:
        tool_logger.warning("Не удалось найти стандартные маркеры начала алертов, весь файл считается одним алертом")
        alert_positions = [0]
    
    # Разделяем текст на отдельные алерты
    alerts = []
    for i in range(len(alert_positions)):
        start = alert_positions[i]
        end = alert_positions[i + 1] if i < len(alert_positions) - 1 else len(alert_file_content)
        alerts.append(alert_file_content[start:end].strip())
    
    return alerts

def extract_alert_data(alert_text: str, alert_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Извлекает структурированные данные из текста алерта.
    
    Args:
        alert_text: Текст алерта
        alert_number: Номер алерта (для логирования)
        
    Returns:
        Optional[Dict[str, Any]]: Структурированные данные алерта или None в случае ошибки
    """
    try:
        alert_data = get_data_alert(alert_text)
        if alert_number:
            tool_logger.info(f"Успешно извлечены структурированные данные из алерта #{alert_number}")
        else:
            tool_logger.info("Успешно извлечены структурированные данные из алерта")
        return alert_data
    except Exception as e:
        if alert_number:
            tool_logger.warning(f"Не удалось извлечь структурированные данные из алерта #{alert_number}: {str(e)}")
        else:
            tool_logger.warning(f"Не удалось извлечь структурированные данные из алерта: {str(e)}")
        return None

def analyze_alert_with_ai(alert_text: str, brief: bool = False, alert_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Анализирует алерт с помощью AI-модели.
    
    Args:
        alert_text: Текст алерта
        brief: Флаг для краткого анализа
        alert_data: Предварительно извлеченные данные алерта
        
    Returns:
        str: Результат анализа
    """
    # Получаем функцию get_bot_response с помощью отложенной загрузки
    get_bot_response = get_ai_response_function()
    
    # Выбираем шаблон и параметры в зависимости от типа анализа
    if brief:
        prompt = BRIEF_ANALYSIS_PROMPT_TEMPLATE.format(alert_text=alert_text)
        max_tokens = MAX_TOKENS_BRIEF_ANALYSIS
        tool_logger.info("Отправка запроса для краткого анализа алерта")
    else:
        prompt = FULL_ANALYSIS_PROMPT_TEMPLATE.format(alert_text=alert_text)
        max_tokens = MAX_TOKENS_FULL_ANALYSIS
        tool_logger.info("Отправка запроса для полного анализа алерта")
    
    # Анализируем алерт с помощью модели
    analysis_result = get_bot_response(prompt, max_tokens=max_tokens, alert_data=alert_data)
    
    return analysis_result

def analyze_file_alert(file_path: Optional[str] = None, alert_number: Optional[int] = None) -> str:
    """
    Анализирует алерты из файла, используя GigaChat для генерации аналитического отчета.
    
    Args:
        file_path: Путь к файлу с алертами
        alert_number: Номер конкретного алерта для анализа (опционально)
        
    Returns:
        str: Результат анализа алертов
    """
    tool_logger.info(f"Анализ файла алертов: {file_path}")
    
    # Проверяем доступность модели GigaChat с помощью отложенной загрузки
    model = get_gigachat_model()
    
    try:
        # Проверка существования файла
        if not file_path or not os.path.exists(file_path):
            error_msg = f"Файл не найден: {file_path}"
            tool_logger.error(error_msg)
            return f"⚠️ **Ошибка:** {error_msg}"
        
        # Чтение файла с учетом возможных проблем с кодировкой
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                alert_file_content = f.read()
        except UnicodeDecodeError:
            tool_logger.warning(f"Проблема с кодировкой UTF-8, пробуем другую кодировку")
            with open(file_path, 'r', encoding='windows-1251') as f:
                alert_file_content = f.read()
        
        # Разделяем файл на отдельные алерты
        alerts = split_alerts_from_file(alert_file_content)
        tool_logger.info(f"Найдено {len(alerts)} алертов в файле")
        
        # Если указан конкретный номер алерта, обрабатываем только его
        if alert_number is not None:
            if alert_number <= 0 or alert_number > len(alerts):
                return f"В файле {file_path} содержится {len(alerts)} алертов. Нет алерта с номером {alert_number}."
            
            # Получаем текст выбранного алерта
            alert_text = alerts[alert_number - 1]
            
            # Извлекаем структурированные данные алерта
            alert_data = extract_alert_data(alert_text, alert_number)
            
            # Анализируем алерт с помощью модели и возвращаем результат
            return analyze_alert_with_ai(alert_text, brief=False, alert_data=alert_data)
            
        else:
            # Если алертов больше одного, анализируем первый алерт и указываем общее количество
            if len(alerts) > 1:
                # Получаем текст первого алерта
                alert_text = alerts[0]
                
                # Извлекаем структурированные данные алерта
                alert_data = extract_alert_data(alert_text)
                
                # Анализируем алерт с помощью модели
                analysis_result = analyze_alert_with_ai(alert_text, brief=True, alert_data=alert_data)
                
                # Форматируем результат
                file_basename = os.path.basename(file_path)
                return (f"Найдено {len(alerts)} алертов в файле {file_basename}\n\n"
                        f"Краткий анализ первого алерта:\n{analysis_result}\n\n"
                        f"Для анализа других алертов введите номер, например: '2 алерт'")
                
            elif len(alerts) == 1:
                # Если только один алерт, делаем полный анализ
                alert_text = alerts[0]
                
                # Извлекаем структурированные данные алерта
                alert_data = extract_alert_data(alert_text)
                
                # Анализируем алерт с помощью модели
                return analyze_alert_with_ai(alert_text, brief=False, alert_data=alert_data)
            else:
                # Если нет алертов вообще
                return f"Не найдено алертов в файле {file_path}"
            
    except Exception as e:
        error_message = f"Ошибка анализа файла: {str(e)}"
        tool_logger.error(error_message, exc_info=True)
        return f"⚠️ **Ошибка анализа файла:** {str(e)}"

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

# Экспортируем инструменты и функции для использования через LangChain
# Оставляем оригинальные функции доступными для прямого вызова
# get_data_alert = get_data_alert_tool
# analyze_file_alert = analyze_file_alert_tool 