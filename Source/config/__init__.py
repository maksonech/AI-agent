"""
Модуль для централизованного управления конфигурацией приложения.
Предоставляет доступ к настройкам приложения, путям к файлам и другим конфигурационным параметрам.
"""

from .settings import get_settings
from .credentials import CredentialsManager
from .logging_config import setup_tool_logger, setup_chat_logger
from .exceptions import (
    AIAgentError, ConfigError, CredentialsError, APIError, GigaChatAPIError,
    AuthenticationError, DataProcessingError, AlertParsingError, FileOperationError,
    format_exception, log_exception, safe_execute, exception_handler
)

# Экспортируем основные компоненты
__all__ = [
    'get_settings',
    'CredentialsManager',
    'setup_tool_logger',
    'setup_chat_logger',
    # Исключения
    'AIAgentError',
    'ConfigError', 
    'CredentialsError',
    'APIError',
    'GigaChatAPIError',
    'AuthenticationError',
    'DataProcessingError',
    'AlertParsingError',
    'FileOperationError',
    # Утилиты для работы с исключениями
    'format_exception',
    'log_exception',
    'safe_execute',
    'exception_handler'
] 