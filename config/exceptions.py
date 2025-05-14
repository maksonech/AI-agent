"""
Модуль для централизованной обработки исключений.
Содержит определения пользовательских исключений и функции-обработчики.
"""
from typing import Any, Optional, Dict, List, Callable, Type
import traceback
import sys
from functools import wraps
import logging

# Базовое исключение для всего приложения
class AIAgentError(Exception):
    """Базовый класс для всех исключений в приложении."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# Исключения, связанные с конфигурацией
class ConfigError(AIAgentError):
    """Ошибка конфигурации приложения."""
    pass


class CredentialsError(ConfigError):
    """Ошибка с учетными данными API."""
    pass


# Исключения, связанные с API
class APIError(AIAgentError):
    """Ошибка при работе с внешним API."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 api_response: Optional[Any] = None, details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.api_response = api_response
        super().__init__(message, details)


class GigaChatAPIError(APIError):
    """Ошибка при работе с GigaChat API."""
    pass


class AuthenticationError(APIError):
    """Ошибка аутентификации при работе с API."""
    pass


# Исключения, связанные с обработкой данных
class DataProcessingError(AIAgentError):
    """Ошибка при обработке данных."""
    pass


class AlertParsingError(DataProcessingError):
    """Ошибка при парсинге алерта."""
    pass


class FileOperationError(AIAgentError):
    """Ошибка при работе с файлами."""
    pass


# Функции для обработки исключений
def format_exception(e: Exception) -> str:
    """
    Форматирует исключение в читаемый вид.
    
    Args:
        e: Исключение для форматирования
        
    Returns:
        str: Отформатированное сообщение об ошибке
    """
    if isinstance(e, AIAgentError):
        # Форматируем кастомные исключения
        result = f"❌ **{e.__class__.__name__}**: {e.message}"
        
        # Добавляем детали для API ошибок
        if isinstance(e, APIError) and e.status_code:
            result += f"\nКод статуса: {e.status_code}"
            
        # Добавляем дополнительные детали
        if hasattr(e, 'details') and e.details:
            details_str = "\n".join([f"- {k}: {v}" for k, v in e.details.items()])
            result += f"\n\nДетали:\n{details_str}"
            
        return result
    else:
        # Для стандартных исключений возвращаем просто сообщение
        return f"❌ **Ошибка**: {str(e)}"


def log_exception(e: Exception, logger: logging.Logger) -> None:
    """
    Логирует исключение с соответствующим уровнем.
    
    Args:
        e: Исключение для логирования
        logger: Логгер для записи
    """
    exc_info = sys.exc_info()
    
    if isinstance(e, (ConfigError, CredentialsError, APIError, AuthenticationError)):
        # Критические ошибки, которые препятствуют работе приложения
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=exc_info)
    elif isinstance(e, (DataProcessingError, AlertParsingError, FileOperationError)):
        # Ошибки, которые могут быть обработаны и не приводят к остановке приложения
        logger.warning(f"Ошибка обработки: {str(e)}", exc_info=exc_info)
    else:
        # Все остальные исключения
        logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=exc_info)


def safe_execute(
    func: Callable, 
    *args: Any, 
    error_message: str = "Произошла ошибка при выполнении операции",
    logger: Optional[logging.Logger] = None,
    error_handler: Optional[Callable[[Exception], Any]] = None,
    expected_exceptions: Optional[List[Type[Exception]]] = None,
    **kwargs: Any
) -> Any:
    """
    Безопасно выполняет функцию с обработкой возможных исключений.
    
    Args:
        func: Функция для выполнения
        *args: Аргументы функции
        error_message: Сообщение об ошибке
        logger: Логгер для записи ошибок
        error_handler: Пользовательский обработчик ошибок
        expected_exceptions: Список ожидаемых исключений
        **kwargs: Именованные аргументы функции
        
    Returns:
        Результат выполнения функции или результат обработчика ошибок
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # Проверяем, является ли исключение ожидаемым
        if expected_exceptions and any(isinstance(e, exc_type) for exc_type in expected_exceptions):
            is_expected = True
        else:
            is_expected = False
            
        # Логируем исключение, если предоставлен логгер
        if logger:
            log_exception(e, logger)
            
        # Вызываем пользовательский обработчик, если предоставлен
        if error_handler:
            return error_handler(e)
            
        # Формируем сообщение об ошибке
        if isinstance(e, AIAgentError):
            error_text = format_exception(e)
        else:
            error_text = f"{error_message}: {str(e)}"
            
        # Если исключение ожидаемое, возвращаем сообщение об ошибке
        # В противном случае пробрасываем исключение дальше
        if is_expected:
            return error_text
        else:
            raise


def exception_handler(
    error_message: str = "Произошла ошибка при выполнении операции",
    logger: Optional[logging.Logger] = None,
    expected_exceptions: Optional[List[Type[Exception]]] = None,
    default_return: Any = None
) -> Callable:
    """
    Декоратор для обработки исключений в функциях.
    
    Args:
        error_message: Сообщение об ошибке
        logger: Логгер для записи ошибок
        expected_exceptions: Список ожидаемых исключений
        default_return: Значение, возвращаемое в случае исключения
        
    Returns:
        Декорированная функция
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Проверяем, является ли исключение ожидаемым
                if expected_exceptions and any(isinstance(e, exc_type) for exc_type in expected_exceptions):
                    is_expected = True
                else:
                    is_expected = False
                    
                # Логируем исключение, если предоставлен логгер
                if logger:
                    log_exception(e, logger)
                    
                # Формируем сообщение об ошибке
                if isinstance(e, AIAgentError):
                    error_text = format_exception(e)
                else:
                    error_text = f"{error_message}: {str(e)}"
                    
                # Если исключение ожидаемое, возвращаем default_return или сообщение об ошибке
                # В противном случае пробрасываем исключение дальше
                if is_expected:
                    return default_return if default_return is not None else error_text
                else:
                    raise
        return wrapper
    return decorator 