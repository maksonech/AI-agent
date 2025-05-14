"""
Модуль для централизованной настройки логирования в приложении.
Предоставляет функции для создания и настройки логгеров для различных компонентов приложения.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Dict, Any

# Базовые пути для логов
def get_logs_dir() -> str:
    """Возвращает путь к директории с логами."""
    app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(app_root, 'src', 'logs')

def get_log_path(log_type: str, timestamp: Optional[str] = None) -> str:
    """
    Возвращает абсолютный путь к файлу лога.
    
    Args:
        log_type: Тип лога (например, 'chat', 'tools', 'error')
        timestamp: Временная метка для имени файла (опционально)
        
    Returns:
        str: Абсолютный путь к файлу лога
    """
    logs_dir = get_logs_dir()
    
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y-%m-%d')
    
    log_filename = f"{log_type}_{timestamp}.log"
    
    # Создаем директорию, если она не существует
    os.makedirs(logs_dir, exist_ok=True)
    
    return os.path.join(logs_dir, log_filename)


def setup_logger(logger_name: str, log_file: str, 
                level: int = logging.INFO, 
                format_str: Optional[str] = None,
                max_bytes: int = 5242880,  # 5 MB
                backup_count: int = 3) -> logging.Logger:
    """
    Создает и настраивает логгер с заданными параметрами.
    
    Args:
        logger_name: Имя логгера
        log_file: Путь к файлу лога
        level: Уровень лога
        format_str: Строка форматирования
        max_bytes: Максимальный размер файла лога
        backup_count: Количество резервных копий
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    if format_str is None:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Получаем или создаем логгер
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Проверяем, нужно ли добавлять обработчики
    if not logger.handlers:
        # Создаем обработчик для вывода в файл с ротацией
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        # Создаем обработчик для вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Создаем форматтер
        formatter = logging.Formatter(format_str)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Добавляем обработчики к логгеру
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


def setup_chat_logger() -> logging.Logger:
    """
    Создает и настраивает логгер для чата с агентом.
    
    Returns:
        logging.Logger: Настроенный логгер для чата
    """
    log_file = get_log_path('chat')
    
    # Получаем или создаем логгер
    logger = logging.getLogger('chat')
    logger.setLevel(logging.INFO)
    
    # Проверяем, нужно ли добавлять обработчики
    if not logger.handlers:
        # Создаем обработчик только для вывода в файл с ротацией
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5242880,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Создаем форматтер
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Добавляем только файловый обработчик к логгеру
        logger.addHandler(file_handler)
        
        # Отключаем распространение логов к корневому логгеру
        logger.propagate = False
    
    return logger


def setup_tool_logger(tool_name: str) -> logging.Logger:
    """
    Создает и настраивает логгер для инструмента.
    
    Args:
        tool_name: Имя инструмента
        
    Returns:
        logging.Logger: Настроенный логгер для инструмента
    """
    log_file = get_log_path(f'tool_{tool_name}')
    logger = setup_logger(
        f'tool.{tool_name}', 
        log_file
    )
    return logger


def setup_api_logger() -> logging.Logger:
    """
    Создает и настраивает логгер для API-запросов.
    
    Returns:
        logging.Logger: Настроенный логгер для API
    """
    log_file = get_log_path('api')
    logger = setup_logger(
        'api', 
        log_file, 
        format_str='%(asctime)s - %(levelname)s - [%(client_ip)s] - %(message)s',
        level=logging.DEBUG
    )
    return logger


def get_logger_by_name(name: str) -> logging.Logger:
    """
    Возвращает существующий логгер по имени или создает новый.
    
    Args:
        name: Имя логгера
        
    Returns:
        logging.Logger: Логгер с указанным именем
    """
    logger = logging.getLogger(name)
    
    # Если логгер не имеет обработчиков, настраиваем его
    if not logger.handlers:
        log_file = get_log_path(name.replace('.', '_'))
        return setup_logger(name, log_file)
    
    return logger


def setup_error_logger() -> logging.Logger:
    """
    Настраивает логгер для ошибок приложения.
    
    Returns:
        logging.Logger: Настроенный логгер для ошибок
    """
    logger_name = "errors"
    timestamp = datetime.now().strftime('%Y-%m-%d')
    log_file = get_log_path('errors', timestamp)
    
    # Формат для логов ошибок
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    return setup_logger(logger_name, log_file, logging.ERROR, format_str)


def get_alert_logger() -> logging.Logger:
    """
    Получает логгер для записи информации об алертах.
    
    Returns:
        logging.Logger: Настроенный логгер для алертов
    """
    logger_name = "alerts"
    timestamp = datetime.now().strftime('%Y-%m-%d')
    log_file = get_log_path('alerts', timestamp)
    
    # Формат для логов алертов с подробными деталями
    format_str = '%(asctime)s - %(levelname)s - %(message)s'
    
    return setup_logger(logger_name, log_file, logging.INFO, format_str)


def log_alert_analysis(logger: logging.Logger, alert_text: str, analysis_result: Dict[str, Any]) -> None:
    """
    Логирует анализ алерта с детализацией.
    
    Args:
        logger: Логгер для записи
        alert_text: Текст анализируемого алерта
        analysis_result: Результат анализа алерта
    """
    logger.info("-" * 50)
    logger.info(f"Анализ алерта начат: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Текст алерта: {alert_text[:500]}...")
    
    # Логируем ключевые поля результата анализа
    for key, value in analysis_result.items():
        if key in ['service', 'status', 'http_code', 'severity']:
            logger.info(f"{key}: {value}")
    
    logger.info(f"Полный результат анализа: {analysis_result}")
    logger.info(f"Анализ алерта завершен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("-" * 50) 