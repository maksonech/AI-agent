"""
Модуль для анализа алертов и обработки уведомлений о проблемах.
Содержит инструменты для разбора и анализа алертов из разных источников.
"""
# Добавляем код для корректной работы при прямом запуске
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import re
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
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

# Импортируем модель GigaChat для анализа алертов
try:
    # Не импортируем get_bot_response здесь, чтобы избежать циклического импорта
    from src.core.agent import model as gigachat_model
    tool_logger.info(f"Успешно импортирована модель GigaChat: {gigachat_model is not None}")
except ImportError as e:
    tool_logger.error(f"Не удалось импортировать модель GigaChat из модуля agent: {str(e)}")
    gigachat_model = None

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